# CamIO Creator launcher
# lets users choose an asset image and a microphone input device before running the application
# -- this means the app has to be launched again if the user wants to try out a different asset or mic

import argparse
from pathlib import Path

from creator.app.app import main

DEFAULT_ASSET = Path(__file__).resolve().parent / "creator" / "assets" / "body_anatomy.png"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CamIO Creator launcher")
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_ASSET,
        help="Path to the template image to annotate.",
    )
    parser.add_argument(
        "--mic",
        type=int,
        default=None,
        help="Index of the microphone input device to use.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.template, args.mic)
