from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

from app.database import get_database
from app.widgets.page_header import PageHeader
from app.widgets.primary_button import PrimaryButton
from app.widgets.toast import show_toast


class SettingsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.controls: dict[str, QCheckBox | QSpinBox] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        layout.addWidget(PageHeader("设置", "调整答题体验和界面显示。"))
        layout.addWidget(self._section("答题设置", [
            ("show_answer_immediately", "答题后立即显示答案", "提交后在当前题下方展示结果和解析。"),
            ("auto_next", "答题后自动进入下一题", "适合快速练习，当前版本保存设置供后续使用。"),
            ("shuffle_questions", "随机打乱题目顺序", "随机练习时优先使用该设置。"),
            ("shuffle_options", "随机打乱选项顺序", "当前版本保存设置供后续使用。"),
            ("blank_ignore_case", "填空题忽略大小写", "判断填空答案时忽略大小写和首尾空格。"),
        ]))
        appearance = QFrame()
        appearance.setObjectName("card")
        app_layout = QVBoxLayout(appearance)
        app_layout.setContentsMargins(18, 16, 18, 16)
        app_layout.setSpacing(12)
        title = QLabel("外观设置")
        title.setObjectName("sectionTitle")
        app_layout.addWidget(title)
        row = QHBoxLayout()
        label = QLabel("刷题页字体大小")
        label.setObjectName("cardTitle")
        font = QSpinBox()
        font.setRange(12, 24)
        font.setValue(15)
        self.controls["font_size"] = font
        row.addWidget(label)
        row.addStretch()
        row.addWidget(font)
        app_layout.addLayout(row)
        layout.addWidget(appearance)
        about = QFrame()
        about.setObjectName("card")
        about_layout = QVBoxLayout(about)
        about_layout.setContentsMargins(18, 16, 18, 16)
        about_layout.addWidget(QLabel("关于软件"))
        desc = QLabel("题练通 v1.0 - 所有题库、错题、收藏和学习记录均保存在本地 SQLite 数据库。")
        desc.setObjectName("mutedText")
        desc.setWordWrap(True)
        about_layout.addWidget(desc)
        layout.addWidget(about)
        save = PrimaryButton("保存设置")
        save.clicked.connect(self.save)
        layout.addWidget(save)
        layout.addStretch()
        self.load()

    def _section(self, title_text: str, items: list[tuple[str, str, str]]) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        title = QLabel(title_text)
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        for key, name, desc in items:
            row = QHBoxLayout()
            text_col = QVBoxLayout()
            name_label = QLabel(name)
            name_label.setObjectName("cardTitle")
            desc_label = QLabel(desc)
            desc_label.setObjectName("mutedText")
            desc_label.setWordWrap(True)
            text_col.addWidget(name_label)
            text_col.addWidget(desc_label)
            box = QCheckBox()
            box.setToolTip(name)
            self.controls[key] = box
            row.addLayout(text_col, 1)
            row.addWidget(box)
            layout.addLayout(row)
        return card

    def load(self) -> None:
        with get_database().connect() as conn:
            rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        values = {row["key"]: row["value"] for row in rows}
        for key, control in self.controls.items():
            if isinstance(control, QCheckBox):
                control.setChecked(values.get(key, "1" if key == "blank_ignore_case" else "0") == "1")
            else:
                control.setValue(int(values.get(key, "15")))

    def save(self) -> None:
        with get_database().transaction() as conn:
            for key, control in self.controls.items():
                value = "1" if isinstance(control, QCheckBox) and control.isChecked() else str(control.value() if hasattr(control, "value") else 0)
                conn.execute(
                    "INSERT OR REPLACE INTO app_settings(key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (key, value),
                )
        show_toast(self, "设置已保存", "success")
