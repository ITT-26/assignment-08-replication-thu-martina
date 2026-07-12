from __future__ import annotations
from pathlib import Path
from shutil import copy2, rmtree
from PIL import Image, ImageDraw
from .models import Project
import cv2
import numpy as np

# A4 page: 210mm x 297mm, chosen DPI (dots per inch) = 200, 1 inch = 25.4mm
A4_WIDTH_PX = 1654 # 210 / 25.4 * DPI
A4_HEIGHT_PX = 2339 # 297 / 25.4 * DPI

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
    # CHANGE: the printable template is sized to a fixed A4 canvas to prevent
    # unwanted distortion when printing
    border = 120
    marker_size = 100

    out = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), "white")  # A4 size

    # scale template
    available_w = A4_WIDTH_PX - 2*border
    available_h = A4_HEIGHT_PX - 2*border
    scale = min(available_w/template.width, available_h / template.height)
    scaled_size = (int(template.width*scale), int(template.height*scale))
    scaled_template = template.resize(scaled_size) 

    # center the scaled template inside the A4 canvas
    paste_x = (A4_WIDTH_PX - scaled_size[0]) // 2
    paste_y = (A4_HEIGHT_PX - scaled_size[1]) // 2
    out.paste(scaled_template, (paste_x, paste_y))

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
