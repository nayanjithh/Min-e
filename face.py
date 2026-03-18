import cv2
import numpy as np
from picamera2 import Picamera2
import time

import bo_motor as bo
import servo
# ------------------------------
# CONFIG: Change these as needed
# ------------------------------
FRAME_WIDTH = 640   # Camera width
FRAME_HEIGHT = 480  # Camera height
BOX_WIDTH = 300
BOX_HEIGHT = 100
CONF_THRESHOLD = 0.6 # Confidence threshold for DNN
VERTICAL_OFFSET = 100   # move box up (increase value to move more up)
last_direction = "STOP"

MIN_FACE_AREA = 9000   # too far -> move forward
MAX_FACE_AREA = 40000   # too close -> move backward

bo.init()
servo.init()

# ------------------------------
# Load DNN Face Detector Model
# ------------------------------
net = cv2.dnn.readNetFromCaffe(
    "deploy.prototxt",
    "res10_300x300_ssd_iter_140000.caffemodel"
)


# Optional: enforce CPU usage for DNN
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

# ------------------------------
# Initialize Raspberry Pi Camera
# ------------------------------
picam2 = Picamera2()
picam2.preview_configuration.main.size = (FRAME_WIDTH, FRAME_HEIGHT)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

# ------------------------------
# Calculate center square coordinates
# ------------------------------
box_x1 = FRAME_WIDTH // 2 - BOX_WIDTH // 2
box_y1 = FRAME_HEIGHT // 2 - BOX_HEIGHT // 2 - VERTICAL_OFFSET
box_x2 = box_x1 + BOX_WIDTH
box_y2 = box_y1 + BOX_HEIGHT

# ------------------------------
# Main Loop
# ------------------------------
while True:
    frame = picam2.capture_array()
    frame = cv2.rotate(frame, cv2.ROTATE_180)
    h, w = frame.shape[:2]

    face_found = False   # NEW: track if a face is detected

    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
                                 (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()

    cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (255, 0, 0), 2)

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > CONF_THRESHOLD:
            face_found = True   # FACE DETECTED

            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (x1, y1, x2, y2) = box.astype("int")

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            face_center_x = (x1 + x2) // 2
            face_center_y = (y1 + y2) // 2
            cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 0, 255), -1)

            if box_x1 < face_center_x < box_x2 and box_y1 < face_center_y < box_y2:
                face_area = (x2 - x1) * (y2 - y1)
                if face_area < MIN_FACE_AREA:
                    direction = "FORWARD"
                    bo.forward()
                    time.sleep(0.5)
                elif face_area > MAX_FACE_AREA:
                    direction = "BACKWARD"
                    bo.backward()
                    time.sleep(0.5)
            elif face_center_x < box_x1:
                direction = "LEFT"
            elif face_center_x > box_x2:
                direction = "RIGHT"
            elif face_center_y < box_y1:
                direction = "UP"
            else:
                direction = "DOWN"

            print(direction)

            if direction == "LEFT":
                bo.left()
            elif direction == "RIGHT":
                bo.right()
            elif direction == "UP":
                servo.up()
            elif direction == "DOWN":
                servo.down()
            else:
                bo.stop()
                servo.stop()
            break

    if not face_found:
        print("NO FACE")
        bo.stop()
        servo.stop()
    cv2.imshow("DNN Face Tracker", frame)
    cv2.waitKey(1)

cv2.destroyAllWindows()
picam2.stop()
