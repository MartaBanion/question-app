from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget


def confirm_dialog(parent: QWidget | None, title: str, message: str) -> bool:
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setObjectName("confirmDialog")
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 22, 24, 18)
    layout.setSpacing(14)
    label = QLabel(message)
    label.setWordWrap(True)
    layout.addWidget(label)
    buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
    buttons.button(QDialogButtonBox.Yes).setText("确认")
    buttons.button(QDialogButtonBox.No).setText("取消")
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    return dialog.exec() == QDialog.Accepted
