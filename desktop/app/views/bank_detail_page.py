from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.database import get_database
from app.repositories.bank_repository import BankRepository
from app.widgets.page_header import PageHeader
from app.widgets.secondary_button import SecondaryButton
from app.widgets.stat_card import StatCard


class ModeCard(QFrame):
    clicked = Signal(str)

    def __init__(self, mode: str, title: str, description: str) -> None:
        super().__init__()
        self.mode = mode
        self.setObjectName("modeCard")
        self.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        desc = QLabel(description)
        desc.setObjectName("mutedText")
        desc.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(desc)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.mode)
        super().mousePressEvent(event)


class BankDetailPage(QWidget):
    back_requested = Signal()
    practice_requested = Signal(int, str)

    def __init__(self) -> None:
        super().__init__()
        self.bank_id = 0
        self.repo = BankRepository()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        top = QHBoxLayout()
        self.header_holder = QVBoxLayout()
        top.addLayout(self.header_holder, 1)
        back = SecondaryButton("返回题库列表")
        back.clicked.connect(self.back_requested.emit)
        top.addWidget(back)
        layout.addLayout(top)

        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(12)
        layout.addLayout(self.stats_row)

        mode_title = QLabel("练习模式")
        mode_title.setObjectName("sectionTitle")
        layout.addWidget(mode_title)
        grid = QGridLayout()
        grid.setSpacing(14)
        modes = [
            ("顺序刷题", "顺序练习", "按照题库顺序逐题练习，适合系统复习。"),
            ("随机刷题", "随机练习", "随机打乱题目顺序，适合考前巩固。"),
            ("错题练习", "错题练习", "集中复习做错的题目，连续答对后自动掌握。"),
            ("背题模式", "背题模式", "直接查看答案和解析，适合快速记忆。"),
        ]
        for i, (mode, title, desc) in enumerate(modes):
            card = ModeCard(mode, title, desc)
            card.clicked.connect(lambda m, self=self: self.practice_requested.emit(self.bank_id, m))
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)

        chapter_title = QLabel("章节掌握情况")
        chapter_title.setObjectName("sectionTitle")
        layout.addWidget(chapter_title)
        self.chapter_table = QTableWidget(0, 4)
        self.chapter_table.setHorizontalHeaderLabels(["章节", "题目数", "已做", "正确率"])
        self.chapter_table.setAlternatingRowColors(True)
        layout.addWidget(self.chapter_table, 1)

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def load_bank(self, bank_id: int) -> None:
        self.bank_id = bank_id
        bank = self.repo.get_bank(bank_id)
        self._clear_layout(self.header_holder)
        self._clear_layout(self.stats_row)
        if not bank:
            self.header_holder.addWidget(PageHeader("题库不存在", "该题库可能已被删除。"))
            self.chapter_table.setRowCount(0)
            return
        with get_database().connect() as conn:
            chapters = conn.execute("SELECT COUNT(*) c FROM chapters WHERE bank_id=?", (bank_id,)).fetchone()["c"]
            done = conn.execute("SELECT COUNT(DISTINCT question_id) c FROM answer_records WHERE bank_id=?", (bank_id,)).fetchone()["c"]
            total = conn.execute("SELECT COUNT(*) c FROM answer_records WHERE bank_id=?", (bank_id,)).fetchone()["c"]
            correct = conn.execute("SELECT COUNT(*) c FROM answer_records WHERE bank_id=? AND is_correct=1", (bank_id,)).fetchone()["c"]
            wrong = conn.execute("SELECT COUNT(*) c FROM wrong_questions WHERE bank_id=?", (bank_id,)).fetchone()["c"]
            fav = conn.execute("SELECT COUNT(*) c FROM favorites WHERE bank_id=?", (bank_id,)).fetchone()["c"]
            chapter_rows = conn.execute(
                """
                SELECT COALESCE(c.name,'未分章') chapter_name, COUNT(q.id) question_count,
                       COUNT(DISTINCT r.question_id) done_count,
                       CASE WHEN COUNT(r.id)>0 THEN ROUND(SUM(CASE WHEN r.is_correct=1 THEN 1 ELSE 0 END)*100.0/COUNT(r.id),1) ELSE 0 END accuracy
                FROM questions q
                LEFT JOIN chapters c ON c.id=q.chapter_id
                LEFT JOIN answer_records r ON r.question_id=q.id
                WHERE q.bank_id=?
                GROUP BY COALESCE(c.name,'未分章')
                ORDER BY question_count DESC
                """,
                (bank_id,),
            ).fetchall()
        accuracy = round(correct * 100 / total, 1) if total else 0
        progress = round(done * 100 / bank["question_count"], 1) if bank["question_count"] else 0
        self.header_holder.addWidget(
            PageHeader(
                bank["name"],
                f"{bank['question_count']} 道题目 · {chapters} 个章节 · 上次学习：{bank.get('last_study_at') or '暂无'}",
            )
        )
        for title, value in [
            ("总体进度", f"{progress}%"),
            ("已完成", str(done)),
            ("正确率", f"{accuracy}%"),
            ("错题", str(wrong)),
            ("收藏", str(fav)),
        ]:
            self.stats_row.addWidget(StatCard(title, value))
        self.chapter_table.setRowCount(len(chapter_rows))
        for row, item in enumerate(chapter_rows):
            values = [item["chapter_name"], item["question_count"], item["done_count"], f"{item['accuracy']}%"]
            for col, value in enumerate(values):
                self.chapter_table.setItem(row, col, QTableWidgetItem(str(value)))
        self.chapter_table.resizeColumnsToContents()
