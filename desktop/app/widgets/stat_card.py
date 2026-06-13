from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame


class StatCard(QFrame):
    def __init__(self, title: str, value: str, caption: str = "") -> None:
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        layout.addWidget(value_label)
        layout.addWidget(title_label)
        if caption:
            caption_label = QLabel(caption)
            caption_label.setObjectName("statCaption")
            caption_label.setWordWrap(True)
            layout.addWidget(caption_label)


class StatusTag(QLabel):
    def __init__(self, text: str, status: str = "info") -> None:
        super().__init__(text)
        self.setObjectName("statusTag")
        self.setProperty("status", status)
