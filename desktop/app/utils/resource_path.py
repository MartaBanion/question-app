from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """兼容开发环境和 PyInstaller 打包环境的资源路径。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return str(base / relative_path)

