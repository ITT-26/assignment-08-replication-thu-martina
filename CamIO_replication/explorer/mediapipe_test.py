# note: this was coded with help from AI to quickly test hand_landmark_drawer.py

import sys
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from hand_landmark_drawer import draw_hand

VIDEO_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 0
MODEL_PATH = "./hand_landmarker.task"

# --- 1. set up the detector ---
options = vision.HandLandmarkerOptions(
    base_options=python.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
)
detector = vision.HandLandmarker.create_from_options(options)

# --- 2. open the camera ---
cap = cv2.VideoCapture(VIDEO_ID)
if not cap.isOpened():
    print(f"Could not open camera {VIDEO_ID}")
    sys.exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame")
        break

    # MediaPipe wants RGB, OpenCV gives BGR
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    timestamp_ms = int(time.time() * 1000)
    result = detector.detect_for_video(mp_frame, timestamp_ms)

    # --- debug: how many hands did it find this frame? ---
    # print(f"hands detected: {len(result.hand_landmarks)}")

    # --- 3. draw landmarks + finger state using the new drawer ---
    for hand_landmarks in result.hand_landmarks:
        closed = draw_hand(frame, hand_landmarks)
        print(closed)

    cv2.imshow("hand landmarks", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()