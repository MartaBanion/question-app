from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QRadioButton


def radio_option(text: str) -> QRadioButton:
    return QRadioButton(text)


def check_option(text: str) -> QCheckBox:
    return QCheckBox(text)

