import os
import argparse
import cv2
import numpy as np
import time
import threading
import ncnn  # Import NCNN
from datetime import datetime
import subprocess
from picamera2 import Picamera2
from libcamera import Transform

class VideoStream:
    """Camera object that controls video streaming from the Picamera"""
    def __init__(self, resolution=(640, 480), framerate=30):
        self.camera = Picamera2()
        config = self.camera.create_still_configuration(main={"size": resolution}, transform=Transform(vflip=False))
        self.camera.configure(config)
        self.camera.start()
        self.camera.set_controls({"LensPosition": 0.0})
        self.frame = self.camera.capture_array()
        self.stopped = False

    def start(self):
        return self

    def update(self):
        pass

    def read(self):
        self.frame = self.camera.capture_array()
        return self.frame

    def stop(self):
        self.camera.stop()

def is_multiple_of_five():
    current_minute = datetime.now().minute
    return current_minute % 5 == 0

def run_time_setup_script():
    subprocess.run(["python3", "/home/russouw/wifi_setup.py"])

def run_upload_script(vehicle_count):
    subprocess.run(["python3", "/home/russouw/wifi_log.py", str(vehicle_count)])

run_time_setup_script()

parser = argparse.ArgumentParser()
parser.add_argument('--modeldir', help='Folder where the NCNN model files are located',
                    default='/home/russouw/v5_yolo')
parser.add_argument('--param', help='Name of the .param file',
                    default='model.ncnn.param')
parser.add_argument('--bin', help='Name of the .bin file',
                    default='model.ncnn.bin')
parser.add_argument('--labels', help='Name of the labelmap file',
                    default='labelmap.txt')
parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                    default=0.45)
parser.add_argument('--resolution', help='Desired camera resolution in WxH.',
                    default='1280x720')

args = parser.parse_args()

MODEL_DIR = args.modeldir
PARAM_FILE = args.param
BIN_FILE = args.bin
LABELMAP_NAME = args.labels
min_conf_threshold = float(args.threshold)
resW, resH = args.resolution.split('x')
imW, imH = int(resW), int(resH)

# Path to model files
PATH_TO_PARAM = os.path.join(MODEL_DIR, PARAM_FILE)
PATH_TO_BIN = os.path.join(MODEL_DIR, BIN_FILE)
PATH_TO_LABELS = os.path.join(MODEL_DIR, LABELMAP_NAME)

# Load the label map
with open(PATH_TO_LABELS, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

# Load the NCNN model
net = ncnn.Net()
net.load_param(PATH_TO_PARAM)
net.load_model(PATH_TO_BIN)

# Prepare input settings
target_size = 320  # Adjust based on your model input size (e.g., 320, 416, 640)
mean_vals = (0.0, 0.0, 0.0)
norm_vals = (1/255.0, 1/255.0, 1/255.0)

# Initialize frame rate calculation
frame_rate_calc = 1
freq = cv2.getTickFrequency()

# Initialize video stream
videostream = VideoStream(resolution=(imW, imH), framerate=30).start()
time.sleep(1)

print("Waiting for the next 5-minute interval...")
while not is_multiple_of_five():
    time.sleep(10)  # Check every 10 seconds

print("Starting vehicle detection and upload process...")

previous_vehicle_count = 0
vehicle_passed_count = 0
start_time = time.time()

# Main loop for detection
while True:
    # Start timer (for calculating frame rate)
    t1 = cv2.getTickCount()

    # Grab frame from video stream
    frame = videostream.read()

    # Resize and normalize the image for NCNN
    img = cv2.resize(frame, (target_size, target_size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Create ncnn Mat from image
    mat_in = ncnn.Mat.from_pixels(img, ncnn.Mat.PixelType.PIXEL_RGB, target_size, target_size)
    mat_in.substract_mean_normalize(mean_vals, norm_vals)

    # Create extractor
    ex = net.create_extractor()
    ex.set_light_mode(True)
    ex.input("images", mat_in)  # Adjust input blob name if necessary

    # Run inference
    ret, mat_out = ex.extract("output")  # Adjust output blob name if necessary

    # Parse detection results
    detections = []
    for i in range(mat_out.h):
        values = mat_out.row(i).numpy()
        # Adjust indices based on your model's output format
        class_id = int(values[0])
        score = values[1]
        x1 = int(values[2] * imW)
        y1 = int(values[3] * imH)
        x2 = int(values[4] * imW)
        y2 = int(values[5] * imH)

        if score > min_conf_threshold:
            detections.append([x1, y1, x2, y2, score, class_id])

    current_vehicle_count = 0

    # Draw detections on the frame
    for detection in detections:
        x1, y1, x2, y2, score, class_id = detection
        current_vehicle_count += 1

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (10, 255, 0), 2)

        # Draw label
        object_name = labels[class_id]  # Look up object name from "labels" array using class index
        label_text = '%s: %.2f%%' % (object_name, score * 100)
        labelSize, baseLine = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        label_ymin = max(y1, labelSize[1] + 10)
        cv2.rectangle(frame, (x1, label_ymin - labelSize[1] - 10), (x1 + labelSize[0], label_ymin + baseLine - 10),
                      (255, 255, 255), cv2.FILLED)
        cv2.putText(frame, label_text, (x1, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 0, 0), 2)

    # Check if the number of vehicles in the current frame is less than in the previous frame
    if current_vehicle_count < previous_vehicle_count:
        vehicle_passed_count += previous_vehicle_count - current_vehicle_count

    # Update the previous vehicle count
    previous_vehicle_count = current_vehicle_count

    # Display the vehicle passed count in the top right corner of the frame
    cv2.putText(frame, '#vehicles: {}'.format(vehicle_passed_count), (imW - 300, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)

    # Draw frame rate in the corner of the frame
    cv2.putText(frame, 'FPS: {0:.2f}'.format(frame_rate_calc), (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)

    # Display the frame
    cv2.imshow('Object detector', frame)

    # Calculate frame rate
    t2 = cv2.getTickCount()
    time1 = (t2 - t1) / freq
    frame_rate_calc = 1 / time1

    # Check if 5 minutes have passed
    if time.time() - start_time >= 5 * 60:  # 5 minutes
        # Get current time and reset the timer
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} - Uploading vehicle count: {vehicle_passed_count}")

        # Run the upload script to send the vehicle count to Google Sheets
        upload_thread = threading.Thread(target=run_upload_script, args=(vehicle_passed_count,))
        upload_thread.start()

        # Reset vehicle count and start time for the next 5-minute interval
        vehicle_passed_count = 0
        start_time = time.time()

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):
        break

cv2.destroyAllWindows()
videostream.stop()

