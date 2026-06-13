from __future__ import annotations

from collections import Counter

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.repositories.question_repository import QuestionRepository
from app.widgets.empty_state import EmptyState
from app.widgets.page_header import PageHeader
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import DangerButton, SecondaryButton
from app.widgets.stat_card import StatCard, StatusTag


class WrongPage(QWidget):
    practice_requested = Signal(int, str)

    def __init__(self) -> None:
        super().__init__()
        self.repo = QuestionRepository()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        layout.addWidget(PageHeader("错题本", "集中复习做错的题目，连续答对两次后自动标记为已掌握。"))
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(12)
        layout.addLayout(self.stats_row)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(12)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

    def refresh(self) -> None:
        self._clear(self.list_layout)
        self._clear(self.stats_row)
        items = self.repo.list_wrong_questions()
        counter = Counter(q["mastery_status"] for q in items)
        for title, value in [
            ("错题总数", len(items)),
            ("未掌握", counter.get("未掌握", 0)),
            ("复习中", counter.get("复习中", 0)),
            ("已掌握", counter.get("已掌握", 0)),
        ]:
            self.stats_row.addWidget(StatCard(title, str(value)))
        if not items:
            self.list_layout.addWidget(EmptyState("暂无错题", "答题错误后题目会自动加入错题本。"))
        for q in items:
            card = QFrame()
            card.setObjectName("card")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.setSpacing(10)
            title = QLabel(q["question_text"])
            title.setObjectName("cardTitle")
            title.setWordWrap(True)
            title.setTextInteractionFlags(Qt.TextSelectableByMouse)
            meta = QLabel(f"题库：{q['bank_name']}    章节：{q.get('chapter_name') or '未分章'}    错误次数：{q['wrong_count']}    最近错误：{q['last_wrong_at']}")
            meta.setObjectName("mutedText")
            meta.setWordWrap(True)
            row = QHBoxLayout()
            status = q["mastery_status"]
            status_type = "danger" if status == "未掌握" else ("warning" if status == "复习中" else "success")
            row.addWidget(StatusTag(status, status_type))
            row.addStretch()
            practice = PrimaryButton("重新练习")
            mastered = SecondaryButton("标记已掌握")
            remove = DangerButton("移出错题本")
            practice.clicked.connect(lambda _, bank_id=q["bank_id"]: self.practice_requested.emit(bank_id, "错题练习"))
            mastered.clicked.connect(lambda _, qid=q["id"]: self._mark(qid))
            remove.clicked.connect(lambda _, qid=q["id"]: self._remove(qid))
            row.addWidget(practice)
            row.addWidget(mastered)
            row.addWidget(remove)
            layout.addWidget(title)
            layout.addWidget(meta)
            layout.addLayout(row)
            self.list_layout.addWidget(card)
        self.list_layout.addStretch()

    def _clear(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear(item.layout())

    def _mark(self, question_id: int) -> None:
        self.repo.mark_mastered(question_id)
        self.refresh()

    def _remove(self, question_id: int) -> None:
        self.repo.remove_wrong(question_id)
        self.refresh()
