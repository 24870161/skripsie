import cv2
import numpy as np
from picamera2 import Picamera2

picam2 = Picamera2()

picam2.configure(picam2.create_still_configuration())

picam2.start()

frame = picam2.capture_array()

original_frame = frame.copy()

converted_frame = cv2.cvtColor(original_frame, cv2.COLOR_BGR2RGB)

side_by_side = np.hstack((original_frame, converted_frame))

cv2.imshow('Original | Converted', side_by_side)

cv2.waitKey(0)
cv2.destroyAllWindows()

picam2.stop()