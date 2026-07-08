from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QWidget

# Simple Qt dialog for entering a hotspot name.
# The UI layout was created with AI assistance and adapted for this project.
class NameDialog(QDialog):
    def __init__(self, default_name: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Name region")
        self.setModal(True)
        self.name_edit = QLineEdit(default_name)
        self.name_edit.selectAll()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("Region name", self.name_edit)
        layout.addRow(buttons)

    @property
    def name(self) -> str:
        return self.name_edit.text().strip()
