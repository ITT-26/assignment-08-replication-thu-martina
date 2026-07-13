from __future__ import annotations
import sounddevice as sd
import soundfile as sf
import numpy as np
import sys
from pathlib import Path
from shutil import copy2
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QKeySequence
from PySide6.QtWidgets import (QApplication, QColorDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QPushButton, QPlainTextEdit, QSplitter, QToolBar, QVBoxLayout, QWidget,)

from .canvas import CanvasView
from .exporter import export_project
from .models import Hotspot, Project


class CreatorWindow(QMainWindow):
    # Load an existing project if available, otherwise create a new one.
    def __init__(self, image_path: Path):
        super().__init__()
        template_name = image_path.stem
        project_file = (Path(__file__).parent.parent.parent/ "templates"/ template_name/ "project.camio.json")
        if project_file.exists():
            self.project = Project.load(project_file)
        else:
            self.project = Project(template_path=image_path)
        self.current_hotspot: Hotspot | None = None
        self._updating_inspector = False

        # Audio recording
        self.recording = False
        self.recorded_audio: list[np.ndarray] = []
        self.sample_rate = 44100
        self.stream = None

        self.setWindowTitle("CamIO Creator")
        self.resize(1450, 900)
        self._build_ui()
        self.canvas.refresh_polygons()
        self.refresh_list()
        self._connect()
        self._apply_style()
        self.statusBar().showMessage("Click on the image to create a hotspot.")

    def _build_ui(self) -> None:
        # Build the main application layout consisting of
        # hotspot list, drawing canvas and property inspector.
        # UI layout created with AI assistance.
        self.action_delete = QAction("Delete", self)
        self.action_delete.setShortcut(QKeySequence.Delete)
        self.action_save = QAction("Save changes", self)
        self.action_fit = QAction("Fit view", self)
        self.canvas = CanvasView(self.project)
        left = self._build_sidebar()
        right = self._build_inspector()
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(self.canvas)
        splitter.addWidget(right)
        splitter.setSizes([240, 900, 260])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        self.setCentralWidget(splitter)
        self._set_inspector_enabled(False)

    def _build_sidebar(self) -> QWidget:
        # Create the hotspot overview shown on the left side.
        # UI layout created with AI assistance.
        panel = QWidget()
        panel.setObjectName("sidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("Hotspots")
        title.setObjectName("panelTitle")
        hint = QLabel("Click directly on the image to add a region.")
        hint.setObjectName("hintText")
        hint.setWordWrap(True)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("hotspotList")
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.list_widget, 1)
        return panel

    def _build_inspector(self) -> QWidget:
        # Create the property editor for the selected hotspot.
        # UI layout created with AI assistance.
        panel = QWidget()
        panel.setObjectName("sidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel("Properties")
        title.setObjectName("panelTitle")
        self.empty_label = QLabel("Select a hotspot or draw a new one.")
        self.empty_label.setObjectName("hintText")
        self.empty_label.setWordWrap(True)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Region name")

        self.desc_edit = QPlainTextEdit()
        self.desc_edit.setPlaceholderText("Description spoken or shown by Explorer")
        self.desc_edit.setFixedHeight(110)

        audio_row = QWidget()
        audio_layout = QHBoxLayout(audio_row)
        audio_layout.setContentsMargins(0, 0, 0, 0)
        self.audio_label = QLabel("No audio selected")
        self.audio_label.setObjectName("audioLabel")
        self.audio_button = QPushButton("Browse")
        self.record_button = QPushButton("🎙 Record")

        audio_layout.addWidget(self.audio_label, 1)
        audio_layout.addWidget(self.audio_button)
        audio_layout.addWidget(self.record_button)

        color_row = QWidget()
        color_layout = QHBoxLayout(color_row)
        color_layout.setContentsMargins(0, 0, 0, 0)
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(28, 28)
        self.color_button = QPushButton("Choose color")
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_button, 1)

        layout.addWidget(title)
        layout.addWidget(self.empty_label)
        layout.addSpacing(6)
        layout.addWidget(QLabel("Name"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Description"))
        layout.addWidget(self.desc_edit)
        layout.addWidget(QLabel("Audio"))
        layout.addWidget(audio_row)
        layout.addWidget(QLabel("Color"))
        layout.addWidget(color_row)
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("deleteButton")
        self.save_button = QPushButton("Save changes")
        self.save_button.setObjectName("saveButton")
        layout.addSpacing(12)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.save_button)
        layout.addStretch(1)
        return panel

    def _connect(self) -> None:
        # Connect all UI widgets and canvas signals to their corresponding handlers.
        self.delete_button.clicked.connect(self.delete_selected)
        self.save_button.clicked.connect(self.save_changes)
        self.action_fit.triggered.connect(self.canvas.reset_view)

        self.canvas.hotspot_created.connect(self.select_hotspot)
        self.canvas.hotspot_selected.connect(self.select_hotspot)
        self.canvas.status_changed.connect(self.statusBar().showMessage)

        self.list_widget.currentRowChanged.connect(self._row_changed)
        self.list_widget.itemDoubleClicked.connect(self._rename_from_list)

        self.name_edit.textChanged.connect(self._autosave_inspector)
        self.desc_edit.textChanged.connect(self._autosave_inspector)
        self.audio_button.clicked.connect(self.browse_audio)
        self.color_button.clicked.connect(self.choose_color)

        self.record_button.clicked.connect(self.toggle_recording)

    def _set_inspector_enabled(self, enabled: bool) -> None:
        for widget in (self.name_edit, self.desc_edit, self.audio_button, self.record_button, self.color_button, self.delete_button, self.save_button,):
            widget.setEnabled(enabled)
        self.empty_label.setVisible(not enabled)

    def refresh_list(self) -> None:
        # Synchronize the hotspot list with the current project state.
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for hotspot in self.project.hotspots:
            item = QListWidgetItem(f"■  {hotspot.name}")
            item.setForeground(QColor(*hotspot.color))
            item.setData(Qt.UserRole, hotspot.id)
            self.list_widget.addItem(item)
        if self.current_hotspot:
            for row in range(self.list_widget.count()):
                if self.list_widget.item(row).data(Qt.UserRole) == self.current_hotspot.id:
                    self.list_widget.setCurrentRow(row)
                    break
        self.list_widget.blockSignals(False)

    def select_hotspot(self, hotspot: Hotspot | None) -> None:
        # Update the current selection in both the canvas and property inspector.
        self.current_hotspot = hotspot
        self.canvas.set_selected_hotspot(hotspot)
        self.refresh_list()
        self._load_inspector(hotspot)

    def _load_inspector(self, hotspot: Hotspot | None) -> None:
        self._updating_inspector = True
        if not hotspot:
            self.name_edit.clear()
            self.desc_edit.clear()
            self.audio_label.setText("No audio selected")
            self.color_preview.setStyleSheet("background: transparent; border: 1px solid #999;")
            self._set_inspector_enabled(False)
            self._updating_inspector = False
            return
        self._set_inspector_enabled(True)
        self.name_edit.setText(hotspot.name)
        self.desc_edit.setPlainText(hotspot.description)
        self.audio_label.setText(Path(hotspot.audio).name if hotspot.audio else "No audio selected")
        self.color_preview.setStyleSheet(f"background: {hotspot.color_hex}; border: 1px solid #777; border-radius: 4px;")
        self._updating_inspector = False

    def _autosave_inspector(self) -> None:
        # Store edited hotspot properties directly in the project model.
        if self._updating_inspector or not self.current_hotspot:
            return
        hotspot = self.current_hotspot
        hotspot.name = self.name_edit.text().strip() or f"Region {hotspot.id}"
        hotspot.description = self.desc_edit.toPlainText().strip()
        self.refresh_list()
        self.statusBar().showMessage("Changes saved automatically.")
        self.save_button.setEnabled(True)
        self.save_button.setText("Save changes")

    def _row_changed(self, row: int) -> None:
        if row < 0:
            return
        hotspot_id = self.list_widget.item(row).data(Qt.UserRole)
        hotspot = self.project.find(hotspot_id)
        if hotspot:
            self.select_hotspot(hotspot)

    def _rename_from_list(self, item: QListWidgetItem) -> None:
        hotspot = self.project.find(item.data(Qt.UserRole))
        if hotspot:
            self.select_hotspot(hotspot)
            self.name_edit.setFocus()
            self.name_edit.selectAll()

    def browse_audio(self) -> None:
        # Copy the selected audio file into the project folder
        # and associate it with the current hotspot.
        if not self.current_hotspot:
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Choose audio file", "", "Audio files (*.wav *.mp3 *.ogg *.m4a);;All files (*)",)
        if not filename:
            return  # case: user cancelled the dialog
        
        template_name = Path(self.project.template_path).stem
        audio_dir = (Path(__file__).parent.parent.parent/ "templates"/ template_name/ "audio")
        audio_dir.mkdir(parents=True, exist_ok=True)

        target = audio_dir / Path(filename).name

        source = Path(filename)
        if source.resolve() != target.resolve():
            copy2(source, target)

        self.current_hotspot.audio = str(target)
        self.audio_label.setText(target.name)

        self.statusBar().showMessage(f"Audio selected: {target.name}")
        self.save_button.setEnabled(True)
        self.save_button.setText("Save changes")

    def choose_color(self) -> None:
        # Assign a new display color to the selected hotspot.
        if not self.current_hotspot:
            return
        old = QColor(*self.current_hotspot.color)
        color = QColorDialog.getColor(old, self, "Choose hotspot color")
        if not color.isValid():
            return
        self.current_hotspot.color = (color.red(), color.green(), color.blue())
        self.color_preview.setStyleSheet(f"background: {self.current_hotspot.color_hex}; border: 1px solid #777; border-radius: 4px;")
        self.canvas.refresh_polygons()
        self.refresh_list()
        self.save_button.setEnabled(True)
        self.save_button.setText("Save changes")

    def delete_selected(self) -> None:
        # Remove the currently selected hotspot from the project.
        if not self.current_hotspot:
            return
        if self.current_hotspot.audio:
            audio_file = Path(self.current_hotspot.audio)

            if audio_file.exists():
                try:
                    audio_file.unlink()
                except OSError:
                    pass
        self.project.remove_hotspot(self.current_hotspot)
        self.current_hotspot = None
        self.canvas.set_selected_hotspot(None)
        self.canvas.refresh_polygons()
        self.refresh_list()
        self._load_inspector(None)
        self.statusBar().showMessage("Hotspot deleted.")
        self.save_changes()

    def save_changes(self) -> None:
        # Export the complete project (JSON, color map,
        # template image and audio files) into the output folder.
        template_name = Path(self.project.template_path).stem
        out_dir = (Path(__file__).parent.parent.parent/ "templates"/ template_name)
        print("Template:", self.project.template_path)
        print("Output:", out_dir)
        export_project(self.project, out_dir)
        self.save_button.setText("✓ Saved")
        self.save_button.setEnabled(False)

    def toggle_recording(self) -> None:
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        if self.recording:
            self.recorded_audio.append(indata.copy())

    def start_recording(self) -> None:
        # Start recording audio from the default microphone.
        if not self.current_hotspot:
            return
        self.recorded_audio = []
        self.recording = True
        self.record_button.setText("■ Stop")
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self._audio_callback,
        )
        self.stream.start()
        self.statusBar().showMessage("Recording...")


    def stop_recording(self) -> None:
        # Save the recorded audio as a WAV file
        # inside the current project directory.
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.record_button.setText("🎙 Record")

        if not self.recorded_audio:
            return

        audio = np.concatenate(self.recorded_audio, axis=0)

        template_name = Path(self.project.template_path).stem
        audio_dir = (Path(__file__).parent.parent.parent/ "templates"/ template_name/ "audio")
        audio_dir.mkdir(parents=True, exist_ok=True)

        hotspot_name = self.current_hotspot.name.strip() or f"hotspot_{self.current_hotspot.id}"
        filename = audio_dir / f"{hotspot_name}.wav"

        sf.write(str(filename), audio, self.sample_rate)

        self.current_hotspot.audio = str(filename)
        self.audio_label.setText(filename.name)

        self.statusBar().showMessage("Recording saved.")
        self.save_button.setEnabled(True)
        self.save_button.setText("Save changes")

    def _apply_style(self) -> None:
        # Apply a simple stylesheet for a cleaner user interface.
        # Styling created with AI assistance.
        self.setStyleSheet(
            """
            QMainWindow { background: #f4f4f4; }
            QToolBar { background: #ffffff; border-bottom: 1px solid #d6d6d6; spacing: 8px; padding: 5px; }
            QToolButton { padding: 6px 12px; }
            QWidget#sidePanel { background: #fafafa; border-left: 1px solid #dddddd; border-right: 1px solid #dddddd; }
            QLabel#panelTitle { font-size: 19px; font-weight: 700; color: #202020; }
            QLabel#hintText { color: #666666; }
            QLabel#audioLabel { color: #333333; padding: 6px; background: #ffffff; border: 1px solid #d0d0d0; border-radius: 4px; }
            QListWidget#hotspotList { background: #ffffff; color: #202020; border: 1px solid #d4d4d4; border-radius: 4px; }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background: #e8f0fe; color: #111111; }
            QLineEdit, QPlainTextEdit { background: #ffffff; color: #202020; border: 1px solid #cccccc; border-radius: 4px; padding: 6px; }

            QPushButton {
                padding: 6px 10px;
                border: 1px solid #c4c4c4;
                border-radius: 5px;
                background: #ffffff;
                color: #202020;
            }

            QPushButton:hover {
                background: #f0f0f0;
            }

            QPushButton#saveButton {
                background: #2d7ff9;
                color: white;
                font-weight: bold;
            }

            QPushButton#saveButton:hover {
                background: #1d6fe0;
            }

            QPushButton#deleteButton {
                background: #f5f5f5;
            }

            QPushButton#deleteButton:hover {
                background: #e6e6e6;
            }

            QPushButton#saveButton:disabled {
                background: #cfcfcf;
                color: #666666;
                border: 1px solid #b5b5b5;
            }
            """
        )


def main(asset_path: Path | None = None, mic: int | None = None) -> None:
    app = QApplication(sys.argv)
    base = Path(__file__).parent.parent

    if mic is not None:
        sd.default.device = mic  # mic input device index

    image_path = Path(asset_path) if asset_path is not None else base / "assets" / "body_anatomy.png"

    if not image_path.exists():
        raise FileNotFoundError(f"Template image not found: {image_path}")
    window = CreatorWindow(image_path)
    window.show()
    sys.exit(app.exec())
