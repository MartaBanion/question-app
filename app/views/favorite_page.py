from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.repositories.question_repository import QuestionRepository
from app.widgets.empty_state import EmptyState
from app.widgets.page_header import PageHeader
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import DangerButton


class FavoritePage(QWidget):
    practice_requested = Signal(int, str)

    def __init__(self) -> None:
        super().__init__()
        self.repo = QuestionRepository()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        layout.addWidget(PageHeader("收藏", "查看收藏题目，快速回到重点题目继续练习。"))
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(12)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

    def refresh(self) -> None:
        self._clear()
        items = self.repo.list_favorites()
        if not items:
            self.list_layout.addWidget(EmptyState("暂无收藏题目", "刷题时点击收藏后，题目会显示在这里。"))
        for q in items:
            card = QFrame()
            card.setObjectName("card")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.setSpacing(10)
            title = QLabel(q["question_text"])
            title.setObjectName("cardTitle")
            title.setWordWrap(True)
            meta = QLabel(f"题库：{q['bank_name']}    章节：{q.get('chapter_name') or '未分章'}")
            meta.setObjectName("mutedText")
            row = QHBoxLayout()
            row.addStretch()
            practice = PrimaryButton("开始练习")
            cancel = DangerButton("取消收藏")
            practice.clicked.connect(lambda _, bank_id=q["bank_id"]: self.practice_requested.emit(bank_id, "顺序刷题"))
            cancel.clicked.connect(lambda _, qid=q["id"]: self._remove(qid))
            row.addWidget(practice)
            row.addWidget(cancel)
            layout.addWidget(title)
            layout.addWidget(meta)
            layout.addLayout(row)
            self.list_layout.addWidget(card)
        self.list_layout.addStretch()

    def _clear(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _remove(self, question_id: int) -> None:
        self.repo.remove_favorite(question_id)
        self.refresh()
