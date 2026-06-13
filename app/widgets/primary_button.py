from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("primaryButton")
        self.setCursor(Qt.PointingHandCursor)
