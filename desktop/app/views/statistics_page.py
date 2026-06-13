from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.services.statistics_service import StatisticsService
from app.widgets.empty_state import EmptyState
from app.widgets.page_header import PageHeader
from app.widgets.stat_card import StatCard


class StatisticsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = StatisticsService()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        layout.addWidget(PageHeader("学习记录", "查看累计做题、正确率和薄弱章节。"))
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(12)
        layout.addLayout(self.stats_row)
        bank_title = QLabel("各题库正确率")
        bank_title.setObjectName("sectionTitle")
        layout.addWidget(bank_title)
        self.bank_table = QTableWidget(0, 5)
        self.bank_table.setHorizontalHeaderLabels(["题库", "做题数量", "正确率", "错题数量", "最近练习"])
        self.bank_table.setAlternatingRowColors(True)
        layout.addWidget(self.bank_table)
        chapter_title = QLabel("薄弱章节排行")
        chapter_title.setObjectName("sectionTitle")
        layout.addWidget(chapter_title)
        self.chapter_table = QTableWidget(0, 4)
        self.chapter_table.setHorizontalHeaderLabels(["章节", "已做题数", "正确率", "掌握情况"])
        self.chapter_table.setAlternatingRowColors(True)
        layout.addWidget(self.chapter_table)

    def refresh(self) -> None:
        self._clear_stats()
        data = self.service.overview()
        t = data["totals"]
        total = t.get("total") or 0
        correct = t.get("correct") or 0
        wrong = t.get("wrong") or 0
        accuracy = round(correct * 100 / total, 1) if total else 0
        for title, value, caption in [
            ("累计做题", str(total), "全部练习记录"),
            ("今日做题", str(t.get("today") or 0), "本地日期统计"),
            ("总体正确率", f"{accuracy}%", f"正确 {correct} · 错误 {wrong}"),
            ("最近练习", t.get("last_time") or "暂无", "最近一次答题时间"),
        ]:
            self.stats_row.addWidget(StatCard(title, value, caption))
        self.bank_table.setRowCount(len(data["banks"]))
        for row, item in enumerate(data["banks"]):
            values = [item["bank_name"], item.get("total") or 0, f"{item.get('accuracy') or 0}%", item.get("wrong_count") or 0, item.get("last_time") or "暂无"]
            for col, value in enumerate(values):
                self.bank_table.setItem(row, col, QTableWidgetItem(str(value)))
        self.chapter_table.setRowCount(len(data["chapters"]))
        for row, item in enumerate(data["chapters"]):
            acc = item.get("accuracy") or 0
            values = [item["chapter_name"], item.get("total") or 0, f"{acc}%", self.service.mastery(float(acc))]
            for col, value in enumerate(values):
                self.chapter_table.setItem(row, col, QTableWidgetItem(str(value)))
        self.bank_table.resizeColumnsToContents()
        self.chapter_table.resizeColumnsToContents()

    def _clear_stats(self) -> None:
        while self.stats_row.count():
            item = self.stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
