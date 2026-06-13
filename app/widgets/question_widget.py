from __future__ import annotations

import json

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class QuestionDisplay(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.layout = QVBoxLayout(self)

    def set_question(self, question: dict) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.layout.addWidget(QLabel(f"题型：{question.get('question_type', '')}"))
        self.layout.addWidget(QLabel(f"章节：{question.get('chapter_name') or '未分章'}    难度：{question.get('difficulty') or '未填写'}"))
        title = QLabel(question.get("question_text", ""))
        title.setObjectName("QuestionTitle")
        title.setWordWrap(True)
        self.layout.addWidget(title)
        options = json.loads(question.get("options_json") or "{}")
        for key, value in options.items():
            label = QLabel(f"{key}. {value}")
            label.setWordWrap(True)
            self.layout.addWidget(label)

