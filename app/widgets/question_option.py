from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class QuestionOption(QFrame):
    clicked = Signal(str)

    def __init__(self, key: str, text: str, multi: bool = False) -> None:
        super().__init__()
        self.key = key
        self.multi = multi
        self.selected = False
        self.locked = False
        self.setObjectName("questionOption")
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("selected", False)
        self.setProperty("state", "normal")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(14)
        self.key_label = QLabel(key)
        self.key_label.setObjectName("optionKey")
        self.text_label = QLabel(text)
        self.text_label.setObjectName("optionText")
        self.text_label.setWordWrap(True)
        self.status_label = QLabel("")
        self.status_label.setObjectName("optionStatus")
        layout.addWidget(self.key_label)
        layout.addWidget(self.text_label, 1)
        layout.addWidget(self.status_label)

    def mousePressEvent(self, event) -> None:
        if not self.locked and event.button() == Qt.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        self.setProperty("selected", selected)
        self._refresh()

    def set_state(self, state: str, label: str = "") -> None:
        self.setProperty("state", state)
        self.status_label.setText(label)
        self._refresh()

    def set_locked(self, locked: bool) -> None:
        self.locked = locked
        self.setCursor(Qt.ArrowCursor if locked else Qt.PointingHandCursor)

    def _refresh(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
