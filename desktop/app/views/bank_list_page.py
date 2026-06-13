from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from app.repositories.bank_repository import BankRepository
from app.widgets.bank_card import BankCard
from app.widgets.confirm_dialog import confirm_dialog
from app.widgets.empty_state import EmptyState
from app.widgets.flow_layout import FlowLayout
from app.widgets.page_header import PageHeader
from app.widgets.primary_button import PrimaryButton
from app.widgets.toast import show_toast
from app.widgets.message_dialog import warning


class BankListPage(QWidget):
    import_requested = Signal()
    start_requested = Signal(int, str)
    detail_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.repo = BankRepository()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        header_row = QHBoxLayout()
        header_row.addWidget(PageHeader("题库", "管理本地题库，继续练习或导入新的 Excel 题库。"), 1)
        import_btn = PrimaryButton("导入新题库")
        import_btn.clicked.connect(self.import_requested.emit)
        header_row.addWidget(import_btn)
        layout.addLayout(header_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.list_layout = FlowLayout(self.container, margin=0, spacing=16)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

    def refresh(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        banks = self.repo.list_banks()
        if not banks:
            empty = EmptyState("暂时还没有题库", "下载标准模板并导入题目后，就可以开始刷题了。", "导入第一个题库")
            empty.action_clicked.connect(self.import_requested.emit)
            self.list_layout.addWidget(empty)
            return
        for bank in banks:
            card = BankCard(bank)
            card.start_clicked.connect(lambda bank_id: self.start_requested.emit(bank_id, "顺序刷题"))
            card.detail_clicked.connect(self.detail_requested.emit)
            card.delete_clicked.connect(self.delete_bank)
            self.list_layout.addWidget(card)

    def delete_bank(self, bank_id: int) -> None:
        if not confirm_dialog(self, "删除题库", "删除题库会同时删除题目、记录、错题和收藏。确认删除吗？"):
            return
        try:
            self.repo.delete_bank(bank_id)
            self.refresh()
            show_toast(self, "题库已删除", "success")
        except Exception as exc:
            warning(self, f"删除题库失败：{exc}")
