from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsView,
)

from .dialogs import NameDialog
from .models import Hotspot, Project


class VertexItem(QGraphicsEllipseItem):
    def __init__(self, index: int, hotspot: Hotspot, canvas: "CanvasView", x: float, y: float):
        super().__init__(-5, -5, 10, 10)
        self.index = index
        self.hotspot = hotspot
        self.canvas = canvas
        self.setPos(x, y)
        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(QColor("#333333"), 1.2))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(60)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and self.index < len(self.hotspot.polygon):
            p = self.pos()
            self.hotspot.polygon[self.index] = (p.x(), p.y())
            self.canvas.refresh_polygons(keep_vertices=False)
        return super().itemChange(change, value)


class CanvasView(QGraphicsView):
    hotspot_created = Signal(object)
    hotspot_selected = Signal(object)
    status_changed = Signal(str)

    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.selected_hotspot: Optional[Hotspot] = None
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setMouseTracking(True)

        self.drawing = False
        self.space_down = False
        self.current_points: list[QPointF] = []
        self.preview_item: Optional[QGraphicsPolygonItem] = None
        self.polygon_items: dict[int, QGraphicsPolygonItem] = {}
        self.vertex_items: list[VertexItem] = []
        self.template_item: QGraphicsPixmapItem | None = None
        self._load_template()

    def _load_template(self) -> None:
        # Load the template image into the graphics scene.
        pixmap = QPixmap(str(self.project.template_path))
        if pixmap.isNull():
            raise FileNotFoundError(f"Cannot load template image: {self.project.template_path}")
        self.template_item = QGraphicsPixmapItem(pixmap)
        self.template_item.setZValue(0)
        self.scene.addItem(self.template_item)
        self.scene.setSceneRect(self.template_item.boundingRect())
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.status_changed.emit("Click on the image to draw a hotspot. Press Enter to finish.")

    def reset_view(self) -> None:
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def set_selected_hotspot(self, hotspot: Optional[Hotspot]) -> None:
        self.selected_hotspot = hotspot
        self.refresh_polygons()
        self._show_vertices(hotspot)

    def delete_selected(self) -> None:
        if not self.selected_hotspot:
            return
        deleted_name = self.selected_hotspot.name
        self.project.remove_hotspot(self.selected_hotspot)
        self.selected_hotspot = None
        self.refresh_polygons()
        self._clear_vertices()
        self.hotspot_selected.emit(None)
        self.status_changed.emit(f"Deleted {deleted_name}")

    def finish_polygon(self) -> None:
        # Finish drawing the polygon and create a new hotspot.
        if len(self.current_points) < 3:
            self.status_changed.emit("A hotspot needs at least 3 points.")
            return
        default_name = f"Region {self.project.next_id}"
        dialog = NameDialog(default_name, self.window())
        result = dialog.exec()
        # PySide can return either an enum value or the integer 1 depending on version/platform.
        # Accept all common "accepted" values so the hotspot is not accidentally discarded.
        accepted_values = {QDialog.DialogCode.Accepted, QDialog.Accepted, 1}
        if result not in accepted_values:
            self.cancel_drawing()
            return
        polygon = [(p.x(), p.y()) for p in self.current_points]
        hotspot = self.project.add_hotspot(polygon, dialog.name or default_name)
        self._end_drawing()
        self.refresh_polygons()
        self.set_selected_hotspot(hotspot)
        self.hotspot_created.emit(hotspot)
        self.status_changed.emit(f"Created {hotspot.name}")

    def cancel_drawing(self) -> None:
        self._end_drawing()
        self.status_changed.emit("Drawing cancelled.")

    def _start_drawing(self, first_point: QPointF) -> None:
        self.drawing = True
        self.current_points = [first_point]
        self.hotspot_selected.emit(None)
        self._update_preview()
        self.status_changed.emit("Drawing hotspot: click points, Enter to finish, Backspace undo, Esc cancel.")

    def _end_drawing(self) -> None:
        self.drawing = False
        self.current_points = []
        if self.preview_item:
            self.scene.removeItem(self.preview_item)
            self.preview_item = None

    def refresh_polygons(self, keep_vertices: bool = True) -> None:
        # Redraw all hotspot polygons after changes.
        for item in self.polygon_items.values():
            self.scene.removeItem(item)
        self.polygon_items.clear()

        for hotspot in self.project.hotspots:
            if len(hotspot.polygon) < 3:
                continue
            qpoly = QPolygonF([QPointF(x, y) for x, y in hotspot.polygon])
            color = QColor(*hotspot.color)
            fill = QColor(color)
            fill.setAlpha(60 if hotspot is not self.selected_hotspot else 110)
            pen = QPen(color, 1.8 if hotspot is not self.selected_hotspot else 3.0)
            item = QGraphicsPolygonItem(qpoly)
            item.setBrush(QBrush(fill))
            item.setPen(pen)
            item.setZValue(10)
            item.setData(0, hotspot.id)
            self.scene.addItem(item)
            self.polygon_items[hotspot.id] = item

        if keep_vertices and self.selected_hotspot:
            self._show_vertices(self.selected_hotspot)

    def _show_vertices(self, hotspot: Optional[Hotspot]) -> None:
        # Display draggable control points for polygon editing.
        self._clear_vertices()
        if not hotspot:
            return
        for i, (x, y) in enumerate(hotspot.polygon):
            item = VertexItem(i, hotspot, self, x, y)
            self.vertex_items.append(item)
            self.scene.addItem(item)

    def _clear_vertices(self) -> None:
        for item in self.vertex_items:
            self.scene.removeItem(item)
        self.vertex_items.clear()

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        # Handle hotspot creation and selection using mouse interaction.
        point = self.mapToScene(event.position().toPoint())
        if event.button() == Qt.LeftButton and self.scene.sceneRect().contains(point):
            if self.drawing:
                self.current_points.append(point)
                self._update_preview()
                return
            item = self.itemAt(event.position().toPoint())
            if isinstance(item, QGraphicsPolygonItem):
                hotspot = self.project.find(item.data(0))
                if hotspot:
                    self.hotspot_selected.emit(hotspot)
                    return
            self._start_drawing(point)
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.space_down = True
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            return
        if self.drawing:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.finish_polygon()
                return
            if event.key() == Qt.Key_Backspace:
                if self.current_points:
                    self.current_points.pop()
                    self._update_preview()
                if not self.current_points:
                    self.cancel_drawing()
                return
            if event.key() == Qt.Key_Escape:
                self.cancel_drawing()
                return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.space_down = False
            self.setDragMode(QGraphicsView.NoDrag)
            return
        super().keyReleaseEvent(event)

    def _update_preview(self) -> None:
        # Draw a temporary preview while creating a new polygon.
        if self.preview_item:
            self.scene.removeItem(self.preview_item)
            self.preview_item = None
        if not self.current_points:
            return
        item = QGraphicsPolygonItem(QPolygonF(self.current_points))
        item.setPen(QPen(QColor("#1f6feb"), 2.0))
        fill = QColor("#1f6feb")
        fill.setAlpha(45)
        item.setBrush(QBrush(fill))
        item.setZValue(30)
        self.preview_item = item
        self.scene.addItem(item)
