from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QWidget


class Toast(QLabel):
    def __init__(self, parent: QWidget, text: str, status: str = "info") -> None:
        super().__init__(text, parent)
        self.setObjectName("toast")
        self.setProperty("status", status)
        self.setWordWrap(True)
        self.adjustSize()
        self.move(parent.width() - self.width() - 32, 24)
        self.show()
        QTimer.singleShot(2600, self.deleteLater)


def show_toast(parent: QWidget, text: str, status: str = "info") -> None:
    Toast(parent, text, status)
