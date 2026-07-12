import time
import pyglet
import cv2
import cv2.aruco as aruco
from pathlib import Path
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from PIL import Image
import json
import sounddevice as sd
import soundfile as sf

from explorer.hand_landmark_drawer import draw_hand

MISS_THRESHOLD = (
    45  # max number of frames the template can be lost (not all markers found)
)

SCREEN_FRACTION = 0.8  # in relation to screen dimentions

MARKER_DICTIONARY = (
    aruco.DICT_ARUCO_ORIGINAL
)  # to match the markers generated in the export/printable file from the Creator app's side

MEDIAPIPE_MODEL_PATH = Path(__file__).resolve().parent / "hand_landmarker.task"

NUM_HANDS = 1  # only one hand needed for pointing

INDEX_TIP = 8  # landmark no. for the tip of the index finger


# OpenCV -> pyglet function given in Assignment 4
def cv2glet(img, fmt):
    """Convert an OpenCV BGR image to a pyglet ImageData object.
    https://gist.github.com/nkymut/1cb40ea6ae4de0cf9ded7332f1ca0d55
    """
    if fmt == "GRAY":
        rows, cols = img.shape
        channels = 1
    else:
        rows, cols, channels = img.shape

    raw_img = Image.fromarray(img).tobytes()
    top_to_bottom_flag = -1
    bytes_per_row = channels * cols
    return pyglet.image.ImageData(
        width=cols,
        height=rows,
        fmt=fmt,
        data=raw_img,
        pitch=top_to_bottom_flag * bytes_per_row,
    )


# function to convert hex to rgb
def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b, g, r)


# function to retrieve relevant info from Creator app's json output file
def load_hotspots(project_dir):
    project_dir = Path(project_dir)
    json_path = project_dir / "project.camio.json"
    data = json.loads(json_path.read_text())

    hotspots = []
    for h in data["hotspots"]:
        audio_path = project_dir / h["audio"] if h["audio"] else None
        hotspots.append(
            {
                "name": h["name"],
                "color": hex_to_bgr(h["color"]),
                "audio_path": audio_path,
            }
        )
    return hotspots


class ExplorerApp:
    def __init__(self, camera_id, template_path):
        self.camera_id = camera_id
        self.template_path = template_path

        # hotspot / color map data
        self.hotspots = load_hotspots(self.template_path)
        color_map_path = Path(self.template_path) / "color_map.png"
        self.color_map = cv2.imread(str(color_map_path))
        self.output_height, self.output_width = self.color_map.shape[:2]

        self.current_hotspot = None

        # camera setup
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {self.camera_id}")

        # aruco markers setup - same as in Assignment 4
        self.aruco_dict = aruco.getPredefinedDictionary(MARKER_DICTIONARY)
        self.aruco_params = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

        # template detection state
        self.last_source = (
            None  # last known marker corner positions, in camera coordinates
        )
        self.miss_count = 0  # number of consecutive frames in which not all of the markers where found
        self.transformation_matrix = (
            None  # current camera -> template coordinate transformation
        )

        # hand detection setup
        hand_options = mp_vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(
                model_asset_path=str(MEDIAPIPE_MODEL_PATH)
            ),
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=NUM_HANDS,
        )
        self.hand_detector = mp_vision.HandLandmarker.create_from_options(hand_options)

        self.pointing_point = None
        self.template_point = None

        # pyglet
        cam_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        cam_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # figure out how big the window can be without exceeding the screen,
        # preserving the camera's aspect ratio - same scaling pattern as
        # compute_template_placement() in creator/exporter.py
        display = pyglet.display.get_display()
        screen = display.get_default_screen()
        available_w = screen.width * SCREEN_FRACTION
        available_h = screen.height * SCREEN_FRACTION
        window_scale = min(available_w / cam_w, available_h / cam_h)
        self.window_w = int(cam_w * window_scale)
        self.window_h = int(cam_h * window_scale)

        self.window = pyglet.window.Window(
            self.window_w, self.window_h, caption="CamIO Explorer"
        )
        # NOTE: debug for now
        self.status_label = pyglet.text.Label(
            "...",
            font_size=16,
            x=10,
            y=self.window_h - 10,
            anchor_x="left",
            anchor_y="top",
            color=(255, 255, 255, 255),
        )

        # pyglet callbacks/handlers
        self.window.push_handlers(on_draw=self.on_draw, on_close=self.on_close)

    # board detection using ArUco markers - code adapted from Assignment 4 (Martina)
    def detect_board(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)

        self.draw_marker_debug(frame, corners, ids)

        if ids is None:
            return None

        # save marker center points by id
        source = [None] * 4
        for marker_corners, marker_id in zip(corners, ids.flatten()):
            if 0 <= marker_id <= 3:
                source[marker_id] = marker_corners[0].mean(axis=0)

        # need all 4 markers to register
        if any(pt is None for pt in source):
            return None

        # order points by position (TL, TR, BL, BR)
        pts = np.float32(source)
        pts = pts[np.argsort(pts[:, 1])]
        top = pts[:2]
        bottom = pts[2:]
        top = top[np.argsort(top[:, 0])]
        bottom = bottom[np.argsort(bottom[:, 0])]

        return np.array([top[0], top[1], bottom[0], bottom[1]])

    def perspective_transformation(self, source):
        # destination points (TL, TR, BL, BR), same order as source
        destination = np.float32(
            [
                [0, 0],
                [self.output_width, 0],
                [0, self.output_height],
                [self.output_width, self.output_height],
            ]
        )
        return cv2.getPerspectiveTransform(source, destination)

    def warp_frame(self, frame, mat):
        return cv2.warpPerspective(
            frame,
            mat,
            (self.output_width, self.output_height),
            flags=cv2.INTER_LINEAR,
        )

    def detect_pointing_gesture(self, frame):
        # convert frame from BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # convert into mp.Image
        mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        # get timestamp in ms
        timestamp_ms = int(time.time() * 1000)

        # run the detector
        result = self.hand_detector.detect_for_video(mp_frame, timestamp_ms)

        if not result.hand_landmarks:
            return None
        else:
            hand_landmarks = result.hand_landmarks[0]
            closed = draw_hand(frame, hand_landmarks)

        # pointing gesture -> all fingers closed/flexed except for the index
        pointing = (
            not closed["index"]  # False
            and closed["thumb"]  # True
            and closed["middle"]  # True
            and closed["ring"]  # True
            and closed["pinky"]  # True
        )  # will be True if condition is met

        if not pointing:
            return None
        else:
            height, width, _ = frame.shape
            index_x = hand_landmarks[INDEX_TIP].x * width
            index_y = hand_landmarks[INDEX_TIP].y * height
            return index_x, index_y

    # map the coordinates returned by detect_pointing_gesture to the template's
    def map_to_template(self, point):
        # point -> pointing coordinates related to captured camera w,h
        if point is None:
            return None

        if self.transformation_matrix is None:
            return None

        point_np = np.array(
            [[point]], dtype=np.float32
        )  # format that perspectiveTransform() needs
        transformed_point_np = cv2.perspectiveTransform(
            point_np, self.transformation_matrix
        )
        transformed_point = (
            transformed_point_np[0][0][0],
            transformed_point_np[0][0][1],
        )

        return transformed_point

    def get_hotspot_at(self, point):

        if point is None:
            return None

        x, y = int(point[0]), int(point[1])
        height, width, _ = self.color_map.shape

        if not (0 <= x < width and 0 <= y < height):
            return None

        pixel_color = tuple(int(v) for v in self.color_map[y, x])  # BGR

        for hotspot in self.hotspots:
            if hotspot["color"] == pixel_color:
                return hotspot

        return None  # no associated color
    
    def play_hotspot_audio(self, hotspot):
        if hotspot is None or hotspot["audio_path"] is None:
            return
        data, samplerate = sf.read(str(hotspot["audio_path"]))
        sd.stop() 
        sd.play(data, samplerate)

    # NOTE: debug - draws a box around each detected marker and labels it with its ID
    def draw_marker_debug(self, frame, corners, ids):
        if ids is None:
            return
        for marker_corners, marker_id in zip(corners, ids.flatten()):
            pts = marker_corners[0].astype(np.int32)
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 255), thickness=2)
            center = pts.mean(axis=0).astype(int)
            cv2.putText(
                frame,
                str(int(marker_id)),
                (center[0] - 10, center[1] + 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

    def on_draw(self):
        self.window.clear()

        ret, frame = self.cap.read()
        if not ret:
            return

        source = self.detect_board(frame)

        self.pointing_point = self.detect_pointing_gesture(frame)

        self.template_point = self.map_to_template(self.pointing_point)

        # debounce logic for hotspots
        new_hotspot = self.get_hotspot_at(self.template_point)
        if new_hotspot is not self.current_hotspot:
            self.play_hotspot_audio(new_hotspot)
        self.current_hotspot = new_hotspot

        if source is not None:
            self.last_source = source
            self.miss_count = 0
            self.transformation_matrix = self.perspective_transformation(source)
            # self.status_label.text = "Board registered"  # NOTE: debug for now
        else:
            self.miss_count += 1
            if self.miss_count > MISS_THRESHOLD:
                self.last_source = None
                self.transformation_matrix = None
            # self.status_label.text = "Searching for markers..."  # NOTE: debug for now

        # DEBUG visual feedback - TODO: paint hotspot on top of camera feedback
        if self.current_hotspot is not None:
            self.status_label.text = f"Pointing at: {self.current_hotspot['name']}"

        # draw raw camera feed as background
        cam_img = cv2glet(frame, "BGR")
        cam_img.blit(0, 0, 0, width=self.window_w, height=self.window_h)

        # NOTE: debug - draw the warped result as a picture-in-picture in the
        # corner, just to visually confirm registration is correct
        # This debug feature was implemented with help of Claude AI (Anthropic)
        if self.transformation_matrix is not None:
            warped = self.warp_frame(frame, self.transformation_matrix)
            warped_img = cv2glet(warped, "BGR")
            preview_w, preview_h = 240, int(
                240 * self.output_height / self.output_width
            )
            warped_img.blit(
                self.window.width - preview_w - 10,
                10,
                0,
                width=preview_w,
                height=preview_h,
            )

        self.status_label.draw()

    def on_close(self):
        self.cap.release()
        pyglet.app.exit()
