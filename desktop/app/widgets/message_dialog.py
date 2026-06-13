from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def info(parent: QWidget | None, text: str) -> None:
    QMessageBox.information(parent, "提示", text)


def warning(parent: QWidget | None, text: str) -> None:
    QMessageBox.warning(parent, "提示", text)


def confirm(parent: QWidget | None, text: str) -> bool:
    return QMessageBox.question(parent, "确认", text, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes

