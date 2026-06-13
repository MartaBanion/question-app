from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.database import Database
from app.services.template_service import TemplateService
from app.utils.resource_path import resource_path
from app.views.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    try:
        Database()
        TemplateService().ensure_templates()
    except Exception as exc:
        QMessageBox.critical(None, "启动失败", f"程序初始化失败：{exc}")
        return 1

    qss_path = resource_path("resources/styles/main.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except OSError:
        pass

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
