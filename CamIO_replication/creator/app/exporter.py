from __future__ import annotations
from pathlib import Path
from shutil import copy2, rmtree
from PIL import Image, ImageDraw
from .models import Project
import cv2
import numpy as np


def export_project(project: Project, output_dir: Path) -> Path:
    # Export all project resources required by the Explorer,
    # including template image, color map, printable template,
    # audio files and project description.
    output_dir.mkdir(parents=True, exist_ok=True)

    template = Image.open(project.template_path).convert("RGB")
    template.save(output_dir / "template.png")

    color_map = Image.new("RGB", template.size, (0, 0, 0))
    draw_map = ImageDraw.Draw(color_map)

    for hotspot in project.hotspots:
        if len(hotspot.polygon) >= 3:
            draw_map.polygon(hotspot.polygon, fill=hotspot.color)

    color_map.save(output_dir / "color_map.png")

    printable = make_printable_template(template)
    printable.save(output_dir / "printable_template.png")

    project.save_json(output_dir / "project.camio.json")

    return output_dir


def make_printable_template(template: Image.Image) -> Image.Image:
    """Create a printable template with real ArUco markers."""
    border = 120
    marker_size = 90
    out = Image.new("RGB", (template.width + 2 * border, template.height + 2 * border),"white",)
    out.paste(template, (border, border))
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
    positions = [
        (18, 18, 0),
        (out.width - marker_size - 18, 18, 1),
        (out.width - marker_size - 18, out.height - marker_size - 18, 2),
        (18, out.height - marker_size - 18, 3),
    ]
    for x, y, marker_id in positions:
        marker = cv2.aruco.generateImageMarker(dictionary, marker_id, marker_size,)
        marker = Image.fromarray(marker).convert("RGB")
        out.paste(marker, (x, y))
    return out
