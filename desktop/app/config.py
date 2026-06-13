from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "题练通"
BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCES_DIR = BASE_DIR / "resources"
TEMPLATES_DIR = RESOURCES_DIR / "templates"
STYLES_DIR = RESOURCES_DIR / "styles"


def _app_data_dir() -> Path:
    """开发环境使用项目 data，打包后使用用户可写目录保存数据。"""
    if getattr(sys, "frozen", False):
        if sys.platform.startswith("win"):
            root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            return root / APP_NAME / "data"
        return Path.home() / ".local" / "share" / APP_NAME / "data"
    return BASE_DIR / "data"


DATA_DIR = _app_data_dir()
DB_PATH = DATA_DIR / "question_app.db"

QUESTION_TYPES = ("单选题", "多选题", "判断题", "填空题")
DIFFICULTIES = ("简单", "中等", "困难")
