import argparse
import pyglet

from camio_explorer import ExplorerApp


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--camera", type=int, help="Input camera ID")  # camera id
    parser.add_argument("-t", "--template", type=str, help="Path to template")  # path to template (CamIO Creator output file)

    args = parser.parse_args()

    # validate arguments
    # TODO

    # run CamIO Explorer app
    app = ExplorerApp(parser.camera, parser.template)
    pyglet.app.run()


if __name__ == "__main__":
    main()
