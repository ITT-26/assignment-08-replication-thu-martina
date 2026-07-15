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
from creator.app.exporter import (
    get_printable_template_constants,
    PRINT_MARGIN,
    MARKER_SIZE,
)

# Markers, detection
MARKER_DICTIONARY = aruco.DICT_ARUCO_ORIGINAL # to match the markers generated in the export/printable file from the Creator app's side
MISS_THRESHOLD = 45  # max number of frames the template can be lost (not all markers found)

# Mediapipe
MEDIAPIPE_MODEL_PATH = Path(__file__).resolve().parent / "hand_landmarker.task"
NUM_HANDS = 1  # only one hand needed for pointing
INDEX_TIP = 8  # landmark no. for the tip of the index finger

# Pyglet window
SCREEN_FRACTION = 0.8  # in relation to screen dimentions
INTRO_DURATION = 6  # seconds the instructions overlay stays visible
TRANSPARENCY = 0.35  # alpha value for hotspot polygon fill


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
def load_hotspots(project_dir, template_size):
    project_dir = Path(project_dir)
    json_path = project_dir / "project.camio.json"
    data = json.loads(json_path.read_text())

    # same scale/offset used by exporter.py when generating color_map.png,
    # needed here so the JSON polygons line up with warped coordinate space
    scale, offset_x, offset_y = get_printable_template_constants(template_size)

    hotspots = []
    for h in data["hotspots"]:
        audio_path = project_dir / h["audio"] if h["audio"] else None
        polygon = np.array(
            [[x * scale + offset_x, y * scale + offset_y] for x, y in h["polygon"]],
            dtype=np.int32,
        )
        hotspots.append(
            {
                "name": h["name"],
                "color": hex_to_bgr(h["color"]),
                "audio_path": audio_path,
                "polygon": polygon,
            }
        )
    return hotspots, data.get("name", "Untitled")


class ExplorerApp:
    def __init__(self, camera_id, template_path):
        self.camera_id = camera_id
        self.template_path = template_path

        # hotspot / color map data
        template_path = Path(self.template_path) / "template.png"
        template_h, template_w = cv2.imread(str(template_path)).shape[:2]
        self.hotspots, self.project_name = load_hotspots(
            self.template_path, (template_w, template_h)
        )

        color_map_path = Path(self.template_path) / "color_map.png"
        self.color_map = cv2.imread(str(color_map_path))
        self.output_height, self.output_width = self.color_map.shape[:2]

        self.current_hotspot = None

        # camera setup
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {self.camera_id}")
        # request a higher capture resolution 
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        # aruco markers setup - same as in Assignment 4, but with a different dictionary
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
            self.window_w,
            self.window_h,
            caption=f"CamIO Explorer - {self.project_name}",
        )

        # use framebuffer (physical pixel size) since on HiDPI/Retina displays (Mac) logical window size differs
        self.fb_w, self.fb_h = self.window.get_framebuffer_size()

        self.create_labels()
        self.create_shapes()

        # intro overlay timing: shows project name + controls briefly on startup
        self.show_intro = True
        pyglet.clock.schedule_once(self.hide_intro, INTRO_DURATION)

        # pyglet callbacks/handlers
        self.window.push_handlers(
            on_draw=self.on_draw, on_close=self.on_close, on_key_press=self.on_key_press
        )

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

    # takes into account position of ArUco markers, and how the export is handled in creator app (margins, markers)
    def perspective_transformation(self, source):
        marker_offset = PRINT_MARGIN + MARKER_SIZE / 2
        destination = np.float32(
            [
                [marker_offset, marker_offset],
                [self.output_width - marker_offset, marker_offset],
                [marker_offset, self.output_height - marker_offset],
                [self.output_width - marker_offset, self.output_height - marker_offset],
            ]
        )
        return cv2.getPerspectiveTransform(source, destination)

    # get warped
    def warp_frame(self, frame, mat):
        return cv2.warpPerspective(
            frame,
            mat,
            (self.output_width, self.output_height),
            flags=cv2.INTER_LINEAR,
        )

    # function to fit an image inside a pyglet window preserving its aspect ratio
    # NOTE: coded with AI assistance
    def fit_and_blit(self, img, img_w, img_h):
        scale = min(self.fb_w / img_w, self.fb_h / img_h)
        draw_w = int(img_w * scale)
        draw_h = int(img_h * scale)
        x = (self.fb_w - draw_w) // 2
        y = (self.fb_h - draw_h) // 2
        img.blit(x, y, 0, width=draw_w, height=draw_h)

    # detect gesture to trigger info feedback
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

    # return the hotspot that is being pointed at based on color map
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

    # play audio, if there is one
    def play_hotspot_audio(self, hotspot):
        if hotspot is None or hotspot["audio_path"] is None:
            return

        if not hotspot["audio_path"].exists():
            print(f"[warning] missing audio file for '{hotspot['name']}': {hotspot['audio_path']}")
            return

        try:
            data, samplerate = sf.read(str(hotspot["audio_path"]))
            sd.stop()
            sd.play(data, samplerate)
        except Exception as e:
            print(f"[warning] could not play audio for '{hotspot['name']}': {e}")  # fix so that the app doesn't crash if the audio file is corrupt

    # draw a box around each detected marker and label it with its ID
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

    # draw hotspot area on top of the shown img
    def draw_hotspot(self, warped, hotspot, alpha=TRANSPARENCY):
        if hotspot is None:
            return

        overlay = warped.copy()
        # NOTE: AI helped with these two cv2 functions:
        cv2.fillPoly(overlay, [hotspot["polygon"]], color=hotspot["color"])
        cv2.addWeighted(overlay, alpha, warped, 1 - alpha, 0, dst=warped)

        cv2.polylines(
            warped,
            [hotspot["polygon"]],
            isClosed=True,
            color=(255, 255, 255),
            thickness=3,
        )

    # handle keyboard input
    def on_key_press(self, symbol, modifiers):
        # 'q' or [ESC] to quit
        if symbol == pyglet.window.key.Q or symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()

    # pyglet labels
    def create_labels(self):
        self.hotspot_label = pyglet.text.Label(
            "",
            font_size=22,
            x=self.fb_w // 2,
            y=self.fb_h - 10,
            anchor_x="center",
            anchor_y="top",
            color=(255, 255, 255, 255),
        )

        self.intro_label = pyglet.text.Label(
            f"{self.project_name}\n\n"
            "Point at the board with your index finger\nto hear each part described.\n\n"
            "Press 'q' / [ESC] to quit",
            font_size=24,
            x=self.fb_w // 2,
            y=self.fb_h // 2,
            anchor_x="center",
            anchor_y="center",
            color=(255, 255, 255, 255),
            multiline=True,
            width=self.fb_w - 80,
            align="center",
        )

    # pyglet shapes
    def create_shapes(self):
        self.intro_overlay = pyglet.shapes.Rectangle(
            0, 0, self.window_w, self.window_h, color=(0, 0, 0)
        )
        self.intro_overlay.opacity = 160

    # update based on pointed hotspot
    def update_status_label(self):
        if self.current_hotspot is not None:
            self.hotspot_label.text = f"● {self.current_hotspot['name']}"
            self.hotspot_label.color = (
                *self.current_hotspot["color"][::-1],
                255,
            )  # BGR -> RGB
        else:
            self.hotspot_label.text = ""

    # on draw
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

        self.update_status_label()

        # main view: warped template once the board is registered; raw camera
        # feed as fallback while searching for markers
        if self.transformation_matrix is not None:
            warped = self.warp_frame(frame, self.transformation_matrix)
            self.draw_hotspot(warped, self.current_hotspot)
            main_img = cv2glet(warped, "BGR")
            self.fit_and_blit(main_img, self.output_width, self.output_height)
        else:
            main_img = cv2glet(frame, "BGR")
            cam_h, cam_w, _ = frame.shape
            self.fit_and_blit(main_img, cam_w, cam_h)

        self.hotspot_label.draw()

        if self.show_intro:
            self.intro_overlay.draw()  # transparent black background
            self.intro_label.draw()  # text

    # hide instructions
    def hide_intro(self, dt):
        self.show_intro = False

    def on_close(self):
        self.cap.release()
        pyglet.app.exit()
