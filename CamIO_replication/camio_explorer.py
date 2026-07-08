import pyglet
import cv2

class ExplorerApp:
    def __init__(self, camera_id, template_path):
        self.camera_id = camera_id
        self.template_path = template_path
        
        # # open stream
        # cap = cv2.VideoCapture(self.camera_id)

        # if not cap.isOpened():
        #     print(f"Could not open camera {self.camera_id}.")
        #     return

        # print(f"Opened camera {self.camera_id}. Press 'q' to quit.")
        # while True:
        #     ret, frame = cap.read()
        #     if not ret:
        #         print("Failed to read frame.")
        #         break

        #     cv2.imshow("CamIO Explorer", frame)
        #     if cv2.waitKey(1) & 0xFF == ord("q"):
        #         break

        # cap.release()
        # cv2.destroyAllWindows()


# abrir camara con pyglet
# aruco detection
# perspective transformation