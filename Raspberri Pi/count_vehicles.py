######## Webcam Object Detection Using Tensorflow-trained Classifier #########
#
# Author: Evan Juras
# Date: 10/27/19
# Description: 
# This program uses a TensorFlow Lite model to perform object detection on a live webcam
# feed. It draws boxes and scores around the objects of interest in each frame from the
# webcam. To improve FPS, the webcam object runs in a separate thread from the main program.
# This script will work with either a Picamera or regular USB webcam.
#
# This code is based off the TensorFlow Lite image classification example at:
# https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/examples/python/label_image.py
#
# I, Russouw Grobbelaar, then got an altered version of the code at:
# https://github.com/EdjeElectronics/TensorFlow-Lite-Object-Detection-on-Android-and-Raspberry-Pi
#
# I made my own alterations to the code to work for my application and with my own model
# I also had to change the class as the new Pi OS uses a different camera library

import os
import argparse
import cv2
import numpy as np
import sys
import time
import threading
import importlib.util

from picamera2 import Picamera2
from libcamera import Transform
from datetime import datetime
import subprocess

class VideoStream:
    """Camera object that controls video streaming from the Picamera"""
    def __init__(self,resolution=(640,480),framerate=30):
        self.camera = Picamera2()
        
        config = self.camera.create_still_configuration(main={"size": resolution},transform=Transform(vflip=False))
        self.camera.configure(config)
        
        self.camera.start()
        
        #self.camera.set_controls({"AfMode": 1})\
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
    #subprocess.run(["python3", "/home/russouw/sim800_setup.py"])
    subprocess.run(["python3", "/home/russouw/wifi_setup.py"])

# Function to run the upload script
def run_upload_script(vehicle_count):
    #subprocess.run(["python3", "/home/russouw/sim800_log.py", str(vehicle_count)])
    subprocess.run(["python3", "/home/russouw/wifi_log.py", str(vehicle_count)])

run_time_setup_script()

parser = argparse.ArgumentParser()
parser.add_argument('--modeldir', help='Folder the .tflite file is located in',
                    default='/home/russouw/v5')
parser.add_argument('--graph', help='Name of the .tflite file, if different than detect.tflite',
                    default='detect_quant.tflite')
parser.add_argument('--labels', help='Name of the labelmap file, if different than labelmap.txt',
                    default='labelmap.txt')
parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                    default=0.5)
parser.add_argument('--resolution', help='Desired webcam resolution in WxH. If the webcam does not support the resolution entered, errors may occur.',
                    default='1280x720')
parser.add_argument('--edgetpu', help='Use Coral Edge TPU Accelerator to speed up detection',
                    action='store_true')

args = parser.parse_args()

MODEL_NAME = args.modeldir
GRAPH_NAME = args.graph
LABELMAP_NAME = args.labels
min_conf_threshold = float(args.threshold)
resW, resH = args.resolution.split('x')
imW, imH = int(resW), int(resH)
use_TPU = args.edgetpu

# Import TensorFlow libraries
# If tflite_runtime is installed, import interpreter from tflite_runtime, else import from regular tensorflow
# If using Coral Edge TPU, import the load_delegate library
pkg = importlib.util.find_spec('tflite_runtime')
if pkg:
    from tflite_runtime.interpreter import Interpreter
    if use_TPU:
        from tflite_runtime.interpreter import load_delegate
else:
    from tensorflow.lite.python.interpreter import Interpreter
    if use_TPU:
        from tensorflow.lite.python.interpreter import load_delegate

# If using Edge TPU, assign filename for Edge TPU model
if use_TPU:
    # If user has specified the name of the .tflite file, use that name, otherwise use default 'edgetpu.tflite'
    if (GRAPH_NAME == 'detect.tflite'):
        GRAPH_NAME = 'edgetpu.tflite'       

# Get path to current working directory
CWD_PATH = os.getcwd()

# Path to .tflite file, which contains the model that is used for object detection
PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

# Path to label map file
PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)

# Load the label map
with open(PATH_TO_LABELS, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

# Have to do a weird fix for label map if using the COCO "starter model" from
# https://www.tensorflow.org/lite/models/object_detection/overview
# First label is '???', which has to be removed.
if labels[0] == '???':
    del(labels[0])

# Load the Tensorflow Lite model.
# If using Edge TPU, use special load_delegate argument
if use_TPU:
    interpreter = Interpreter(model_path=PATH_TO_CKPT,
                              experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
    print(PATH_TO_CKPT)
else:
    interpreter = Interpreter(model_path=PATH_TO_CKPT)

interpreter.allocate_tensors()

# Get model details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
height = input_details[0]['shape'][1]
width = input_details[0]['shape'][2]

floating_model = (input_details[0]['dtype'] == np.float32)

input_mean = 127.5
input_std = 127.5

# Check output layer name to determine if this model was created with TF2 or TF1,
# because outputs are ordered differently for TF2 and TF1 models
outname = output_details[0]['name']

if ('StatefulPartitionedCall' in outname): # This is a TF2 model
    boxes_idx, classes_idx, scores_idx = 1, 3, 0
else: # This is a TF1 model
    boxes_idx, classes_idx, scores_idx = 0, 1, 2

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
    frame1 = videostream.read()

    # Acquire frame and resize to expected shape [1xHxWx3]
    frame = frame1.copy()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, (width, height))
    input_data = np.expand_dims(frame_resized, axis=0)

    # Normalize pixel values if using a floating model (i.e., if the model is non-quantized)
    if floating_model:
        input_data = (np.float32(input_data) - input_mean) / input_std

    # Perform the actual detection by running the model with the image as input
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    # Retrieve detection results
    boxes = interpreter.get_tensor(output_details[boxes_idx]['index'])[0]  # Bounding box coordinates of detected objects
    classes = interpreter.get_tensor(output_details[classes_idx]['index'])[0]  # Class index of detected objects
    scores = interpreter.get_tensor(output_details[scores_idx]['index'])[0]  # Confidence of detected objects
    
    # Count the number of vehicles in the current frame
    current_vehicle_count = 0
    detected_objects = []
    
    # Loop over all detections and count vehicles if confidence is above the minimum threshold
    for i in range(len(scores)):
        if (scores[i] > min_conf_threshold) and (scores[i] <= 1.0):
            current_vehicle_count += 1

            # Get bounding box coordinates and draw box
            ymin = int(max(1, (boxes[i][0] * imH)))
            xmin = int(max(1, (boxes[i][1] * imW)))
            ymax = int(min(imH, (boxes[i][2] * imH)))
            xmax = int(min(imW, (boxes[i][3] * imW)))
            
            cv2.rectangle(frame_rgb, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)

            # Draw label
            object_name = labels[int(classes[i])]  # Look up object name from "labels" array using class index
            label = '%s: %d%%' % (object_name, int(scores[i] * 100))  # Example: 'person: 72%'
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)  # Get font size
            label_ymin = max(ymin, labelSize[1] + 10)  # Make sure not to draw label too close to top of window
            cv2.rectangle(frame_rgb, (xmin, label_ymin - labelSize[1] - 10), (xmin + labelSize[0], label_ymin + baseLine - 10), (255, 255, 255), cv2.FILLED)  # Draw white box to put label text in
            cv2.putText(frame_rgb, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)  # Draw label text

    # Check if the number of vehicles in the current frame is less than in the previous frame
    if current_vehicle_count < previous_vehicle_count:
        vehicle_passed_count += previous_vehicle_count - current_vehicle_count

    # Update the previous vehicle count
    previous_vehicle_count = current_vehicle_count

    # Display the vehicle passed count in the top right corner of the frame
    cv2.putText(frame_rgb, '#vehicles: {}'.format(vehicle_passed_count), (imW - 300, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)

    # Draw frame rate in the corner of the frame
    cv2.putText(frame_rgb, 'FPS: {0:.2f}'.format(frame_rate_calc), (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)

    # Display the frame
    cv2.imshow('Object detector', frame_rgb)

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

    # Add logic to break the loop if needed (e.g., press 'q')
    if cv2.waitKey(1) == ord('q'):
        break

cv2.destroyAllWindows()
videostream.stop()