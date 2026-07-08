from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json

Color = tuple[int, int, int]
Point = tuple[float, float]

DEFAULT_COLORS: list[Color] = [
    (231, 76, 60),   # red
    (52, 152, 219),  # blue
    (46, 204, 113),  # green
    (241, 196, 15),  # yellow
    (155, 89, 182),  # purple
    (230, 126, 34),  # orange       
    (26, 188, 156),  # teal
    (236, 112, 99),  # pink
]


@dataclass
class Hotspot:
    # Represents a single interactive region.
    id: int
    name: str
    polygon: list[Point]
    color: Color
    description: str = ""
    audio: str = ""

    @property
    def color_hex(self) -> str:
        return "#%02x%02x%02x" % self.color

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color_hex,
            "audio": (f"audio/{Path(self.audio).name}" if self.audio else ""),
            "polygon": [[round(x, 2), round(y, 2)] for x, y in self.polygon],
        }


@dataclass
class Project:
    # Stores all hotspots belonging to one template image.
    template_path: Path
    name: str = "CamIO Anatomy Demo"
    hotspots: list[Hotspot] = field(default_factory=list)
    next_id: int = 1

    def add_hotspot(self, polygon: list[Point], name: str | None = None) -> Hotspot:
        # Create a new hotspot and assign the next available color.
        color = DEFAULT_COLORS[(self.next_id - 1) % len(DEFAULT_COLORS)]
        hotspot = Hotspot(
            id=self.next_id,
            name=(name or f"Region {self.next_id}").strip() or f"Region {self.next_id}",
            polygon=polygon,
            color=color,
        )
        self.next_id += 1
        self.hotspots.append(hotspot)
        return hotspot

    def remove_hotspot(self, hotspot: Optional[Hotspot]) -> None:
        if hotspot in self.hotspots:
            self.hotspots.remove(hotspot)

    def find(self, hotspot_id: int) -> Hotspot | None:
        return next((h for h in self.hotspots if h.id == hotspot_id), None)

    def to_dict(self) -> dict:
        # Convert the project into a JSON-compatible structure.
        root = Path(__file__).parent.parent.parent.resolve()
        return {
            "format": "camio-creator-replica",
            "version": 2,
            "name": self.name,
            "source_template": str(
                Path(self.template_path).resolve().relative_to(root)
            ),
            "template": "template.png",
            "color_map": "color_map.png",
            "printable_template": "printable_template.png",
            "hotspots": [hotspot.to_dict() for hotspot in self.hotspots],
            "aruco_markers": [
                {"id": 0, "corner": "top_left"},
                {"id": 1, "corner": "top_right"},
                {"id": 2, "corner": "bottom_right"},
                {"id": 3, "corner": "bottom_left"},
            ],
        }

    def save_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, filename: Path):
        # Restore a previously saved project from JSON.
        data = json.loads(filename.read_text())
        project_dir = filename.parent
        root_dir = Path(__file__).parent.parent.parent.resolve()
        if "source_template" in data:
            template_path = Path(data["source_template"])
            if not template_path.is_absolute():
                template_path = (root_dir / template_path).resolve()
        else:
            template_path = (project_dir / data["template"]).resolve()

        project = cls(template_path=template_path, name=data.get("name", "CamIO Anatomy Demo"),)
        
        max_id = 0
        for h in data["hotspots"]:
            color = h["color"]
            if isinstance(color, str):
                color = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

            audio = h.get("audio", "")
            if audio:
                audio_path = Path(audio)
                if not audio_path.is_absolute():
                    audio = str(project_dir / audio_path)

            hotspot = Hotspot(
                id=h["id"],
                name=h["name"],
                polygon=[tuple(p) for p in h["polygon"]],
                color=color,
                description=h.get("description", ""),
                audio=audio,
            )
            project.hotspots.append(hotspot)
            max_id = max(max_id, hotspot.id)

        project.next_id = max_id + 1
        return project