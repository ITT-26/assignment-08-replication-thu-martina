import pyglet
import cv2
import cv2.aruco as aruco
import numpy as np
from PIL import Image

MISS_THRESHOLD = (
    45  # max number of frames the template can be lost (not all markers found)
)

MARKER_DICTIONARY = (
    aruco.DICT_ARUCO_ORIGINAL
)  # to match the markers generated using https://aruco-gen.netlify.app/

# TODO: update once CamIO Creator's export format is defined
OUTPUT_WIDTH = 800
OUTPUT_HEIGHT = 600


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


class ExplorerApp:
    def __init__(self, camera_id, template_path):
        self.camera_id = camera_id
        self.template_path = template_path

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

        # pyglet - TODO: check window size
        cam_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        cam_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.window = pyglet.window.Window(cam_w, cam_h, caption="CamIO Explorer")

        # NOTE: debug for now
        self.status_label = pyglet.text.Label(
            "Searching for markers...",
            font_size=16,
            x=10,
            y=cam_h - 10,
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
                [OUTPUT_WIDTH, 0],
                [0, OUTPUT_HEIGHT],
                [OUTPUT_WIDTH, OUTPUT_HEIGHT],
            ]
        )
        return cv2.getPerspectiveTransform(source, destination)

    def warp_frame(self, frame, mat):
        return cv2.warpPerspective(
            frame,
            mat,
            (OUTPUT_WIDTH, OUTPUT_HEIGHT),
            flags=cv2.INTER_LINEAR,
        )

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

        if source is not None:
            self.last_source = source
            self.miss_count = 0
            self.transformation_matrix = self.perspective_transformation(source)
            self.status_label.text = "Board registered"  # NOTE: debug for now
        else:
            self.miss_count += 1
            if self.miss_count > MISS_THRESHOLD:
                self.last_source = None
                self.transformation_matrix = None
            self.status_label.text = "Searching for markers..."  # NOTE: debug for now

        # draw raw camera feed as backgrounf
        cam_img = cv2glet(frame, "BGR")
        cam_img.blit(0, 0, 0)

        # NOTE: debug - draw the warped result as a picture-in-picture in the
        # corner, just to visually confirm registration is correct 
        # This debug feature was implemented with help of Claude AI (Anthropic)
        if self.transformation_matrix is not None:
            warped = self.warp_frame(frame, self.transformation_matrix)
            warped_img = cv2glet(warped, "BGR")
            preview_w, preview_h = 240, int(240 * OUTPUT_HEIGHT / OUTPUT_WIDTH)
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
