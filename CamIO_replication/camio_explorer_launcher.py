# CamIO Explorer launcher
# lets users choose camera input and a template file before running the application 
# -- this means the app has to be launched again if the user wants to try out a different camera or template 

from pathlib import Path
import pyglet
import cv2

from explorer.camio_explorer import ExplorerApp

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


# try opening the first 10 cameras, only save the functioning ones
def list_available_cameras(max_index=10):
    available = []
    for index in range(max_index):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            available.append(index)
        cap.release()
    return available


# let user pick a camera from the available camera list
def choose_camera(available):
    print("\nAvailable cameras:")
    for index in available:
        print(f"  [{index}] Camera {index}")

    while True:
        choice = input("Select a camera index: ").strip()
        if choice.isdigit() and int(choice) in available:
            return int(choice)
        print("Invalid choice, try again.")


# list all .json files in the templates folder
# NOTE: we still haven't decided the Creator app output file type/format, change if necessary when we do
def list_available_templates():
    return sorted(p for p in TEMPLATES_DIR.iterdir() if p.is_dir())


# let user pick a template from the available template list
def choose_template(available):
    print("Available templates:")
    for index, path in enumerate(available):
        print(f"  [{index}] {path.name}")

    while True:
        choice = input("Select a template index: ").strip()
        if choice.isdigit() and int(choice) in range(len(available)):
            return str(available[int(choice)].resolve())
        print("Invalid choice, try again.")


def main() -> None:

    print("====== CamIO Explorer ======\n")

    print("Searching for available cameras...")
    available_cameras = list_available_cameras()
    if not available_cameras:
        print("No cameras found.")
        return
    camera_index = choose_camera(available_cameras)

    print("\nSearching for saved templates...\n")
    available_templates = list_available_templates()
    if not available_templates:
        print("No templates found.")
        return
    template_path = choose_template(available_templates)

    # run CamIO Explorer app
    app = ExplorerApp(camera_index, template_path)
    pyglet.app.run()


if __name__ == "__main__":
    main()
