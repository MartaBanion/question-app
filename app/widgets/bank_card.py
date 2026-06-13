from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QProgressBar, QSizePolicy, QVBoxLayout

from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton


class BankCard(QFrame):
    start_clicked = Signal(int)
    detail_clicked = Signal(int)
    delete_clicked = Signal(int)

    def __init__(self, bank: dict) -> None:
        super().__init__()
        self.bank = bank
        self.setObjectName("BankCard")
        self.setMinimumWidth(300)
        self.setMaximumWidth(430)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        title = QLabel(bank["name"])
        title.setObjectName("CardTitle")
        title.setToolTip(bank["name"])
        title.setTextInteractionFlags(Qt.TextSelectableByMouse)
        meta = QLabel(
            f"{bank.get('category') or '未分类'} · {bank.get('chapter_count', 0)} 个章节 · {bank['question_count']} 道题"
        )
        meta.setObjectName("CardMeta")
        layout.addWidget(title)
        layout.addWidget(meta)

        progress_value = int(float(bank.get("progress") or 0))
        progress_row = QHBoxLayout()
        progress_label = QLabel("学习进度")
        progress_label.setObjectName("CardMeta")
        progress_percent = QLabel(f"{progress_value}%")
        progress_percent.setObjectName("CardMeta")
        progress_row.addWidget(progress_label)
        progress_row.addStretch()
        progress_row.addWidget(progress_percent)
        layout.addLayout(progress_row)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(progress_value)
        bar.setTextVisible(False)
        layout.addWidget(bar)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        for label, value in [
            ("已完成", bank.get("done_count", 0)),
            ("正确率", f"{bank.get('accuracy', 0)}%"),
            ("错题", bank.get("wrong_count", 0)),
        ]:
            block = QVBoxLayout()
            num = QLabel(str(value))
            num.setObjectName("statSmallValue")
            text = QLabel(label)
            text.setObjectName("statSmallLabel")
            block.addWidget(num)
            block.addWidget(text)
            stats.addLayout(block)
        layout.addLayout(stats)

        actions = QHBoxLayout()
        start = PrimaryButton("继续练习")
        more = SecondaryButton("更多")
        start.clicked.connect(lambda: self.start_clicked.emit(bank["id"]))
        more.clicked.connect(self._show_menu)
        actions.addWidget(start)
        actions.addWidget(more)
        layout.addLayout(actions)

    def _show_menu(self) -> None:
        menu = QMenu(self)
        detail = menu.addAction("查看详情")
        menu.addAction("编辑题库（预留）")
        menu.addAction("导出题库（预留）")
        delete = menu.addAction("删除题库")
        action = menu.exec(self.mapToGlobal(self.rect().bottomRight()))
        if action == detail:
            self.detail_clicked.emit(self.bank["id"])
        elif action == delete:
            self.delete_clicked.emit(self.bank["id"])
