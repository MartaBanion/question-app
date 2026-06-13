from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.widgets.primary_button import PrimaryButton


class EmptyState(QWidget):
    action_clicked = Signal()

    def __init__(self, title: str, message: str, action_text: str = "") -> None:
        super().__init__()
        self.setObjectName("emptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 42, 32, 42)
        layout.setSpacing(12)
        title_label = QLabel(title)
        title_label.setObjectName("emptyTitle")
        title_label.setAlignment(Qt.AlignHCenter)
        message_label = QLabel(message)
        message_label.setObjectName("emptyMessage")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        if action_text:
            button = PrimaryButton(action_text)
            button.clicked.connect(self.action_clicked.emit)
            layout.addWidget(button, alignment=Qt.AlignHCenter)
