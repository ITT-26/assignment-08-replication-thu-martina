# logic and landmark drawing adapted from a project I did in Argentina (playing rock-paper-scissors against the machine)

import cv2
from math import dist
from mediapipe.tasks.python import vision


HAND_CONNECTIONS = [
    (c.start, c.end) for c in vision.HandLandmarksConnections.HAND_CONNECTIONS
]

# landmarks for each finger
FINGERS = {
    "thumb": (1, 2, 3, 4),
    "index": (5, 6, 7, 8),
    "middle": (9, 10, 11, 12),
    "ring": (13, 14, 15, 16),
    "pinky": (17, 18, 19, 20),
}

# landmarks (middle, tip) -> used to decide whether a finger is flexed 
FINGERS_TIPS = {
    "thumb": (2, 4),
    "index": (6, 8),
    "middle": (10, 12),
    "ring": (14, 16),
    "pinky": (18, 20),
}

OPEN_COLOR = (0, 255, 0)    # green 
CLOSED_COLOR = (0, 0, 255)  # red 
LINE_COLOR = (255, 255, 255)
WRIST_COLOR = (255, 255, 255)

# returns 'FINGER_NAME: True' if finger is flexed
# to decide whether a finger is flexed, the distance from the palm to the middle landmark is compared 
# with the distance from the palm to the tip landmark. If the tip is closer, then the finger is flexed.
def fingers_state(hand_landmarks) -> dict:

    palm = hand_landmarks[0]
    closed = {}
    for name, (middle_i, tip_i) in FINGERS_TIPS.items():
        middle = hand_landmarks[middle_i]
        tip = hand_landmarks[tip_i]
        d_middle = dist((palm.x, palm.y), (middle.x, middle.y))
        d_tip = dist((palm.x, palm.y), (tip.x, tip.y))
        closed[name] = d_tip < d_middle

    # thumb - special case - palm reference is landmark 13
    palm_thumb = hand_landmarks[13]
    thumb_middle = hand_landmarks[2]
    thumb_tip = hand_landmarks[4]
    d_middle = dist((palm_thumb.x, palm_thumb.y), (thumb_middle.x, thumb_middle.y))
    d_tip = dist((palm_thumb.x, palm_thumb.y), (thumb_tip.x, thumb_tip.y))
    closed["thumb"] = d_tip < d_middle

    return closed

# paint landmarks red if finger is flexed - easy visual debug
# Claude AI (Anthropic) was used to help draw the points and lines
def draw_hand(frame, hand_landmarks) -> dict:

    height, width, _ = frame.shape
    closed = fingers_state(hand_landmarks)

    points = [(int(lm.x * width), int(lm.y * height)) for lm in hand_landmarks]

    for start_i, end_i in HAND_CONNECTIONS:
        cv2.line(frame, points[start_i], points[end_i], LINE_COLOR, 2, cv2.LINE_AA)

    landmark_to_finger = {i: name for name, indexes in FINGERS.items() for i in indexes}

    for i, (x, y) in enumerate(points):
        finger = landmark_to_finger.get(i)
        if finger is None:
            color = WRIST_COLOR  
        else:
            color = CLOSED_COLOR if closed[finger] else OPEN_COLOR
        cv2.circle(frame, (x, y), 5, color, -1, cv2.LINE_AA)

    return closed