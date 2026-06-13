from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app.repositories.bank_repository import BankRepository
from app.utils.resource_path import resource_path
from app.views.bank_detail_page import BankDetailPage
from app.views.bank_list_page import BankListPage
from app.views.favorite_page import FavoritePage
from app.views.import_page import ImportPage
from app.views.import_preview_page import ImportPreviewPage
from app.views.practice_page import PracticePage
from app.views.settings_page import SettingsPage
from app.views.statistics_page import StatisticsPage
from app.views.wrong_page import WrongPage
from app.widgets.random_practice_dialog import RandomPracticeDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("题练通")
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)

        root = QWidget()
        root.setObjectName("RootWidget")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        brand = QLabel("题练通")
        brand.setObjectName("BrandTitle")
        subtitle = QLabel("本地刷题工作台")
        subtitle.setObjectName("BrandSubTitle")
        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(subtitle)

        self.nav = QListWidget()
        self.nav.setObjectName("NavList")
        self.nav.setIconSize(QSize(20, 20))
        nav_items = [
            ("题库", "bank.svg"),
            ("刷题", "practice.svg"),
            ("错题本", "wrong.svg"),
            ("收藏", "favorite.svg"),
            ("学习记录", "stats.svg"),
            ("设置", "settings.svg"),
        ]
        for name, icon in nav_items:
            item = QListWidgetItem(QIcon(resource_path(f"resources/icons/{icon}")), name)
            item.setToolTip(name)
            self.nav.addItem(item)
        sidebar_layout.addWidget(self.nav, 1)
        version = QLabel("v1.0 · 本地数据")
        version.setObjectName("VersionLabel")
        sidebar_layout.addWidget(version)

        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentStack")
        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        self.import_page = ImportPage()
        self.preview_page = ImportPreviewPage()
        self.bank_list_page = BankListPage()
        self.detail_page = BankDetailPage()
        self.practice_page = PracticePage()
        self.wrong_page = WrongPage()
        self.favorite_page = FavoritePage()
        self.statistics_page = StatisticsPage()
        self.settings_page = SettingsPage()
        for page in [
            self.bank_list_page,
            self.import_page,
            self.preview_page,
            self.detail_page,
            self.practice_page,
            self.wrong_page,
            self.favorite_page,
            self.statistics_page,
            self.settings_page,
        ]:
            self.stack.addWidget(page)

        self.nav.currentRowChanged.connect(self.on_nav)
        self.import_page.imported.connect(self.show_preview)
        self.preview_page.saved.connect(self.show_detail)
        self.preview_page.cancelled.connect(self.show_import)
        self.bank_list_page.import_requested.connect(self.show_import)
        self.bank_list_page.start_requested.connect(self.start_practice)
        self.bank_list_page.detail_requested.connect(self.show_detail)
        self.detail_page.back_requested.connect(self.show_banks)
        self.detail_page.practice_requested.connect(self.start_practice)
        self.practice_page.exit_requested.connect(self.show_banks)
        self.wrong_page.practice_requested.connect(self.start_practice)
        self.favorite_page.practice_requested.connect(self.start_practice)

        if BankRepository().has_banks():
            self.show_banks()
        else:
            self.show_import()

    def on_nav(self, row: int) -> None:
        if row == 0:
            self.show_banks()
        elif row == 1:
            self.stack.setCurrentWidget(self.practice_page)
        elif row == 2:
            self.wrong_page.refresh()
            self.stack.setCurrentWidget(self.wrong_page)
        elif row == 3:
            self.favorite_page.refresh()
            self.stack.setCurrentWidget(self.favorite_page)
        elif row == 4:
            self.statistics_page.refresh()
            self.stack.setCurrentWidget(self.statistics_page)
        elif row == 5:
            self.settings_page.load()
            self.stack.setCurrentWidget(self.settings_page)

    def show_import(self) -> None:
        self.stack.setCurrentWidget(self.import_page)

    def show_preview(self, result) -> None:
        self.preview_page.set_result(result)
        self.stack.setCurrentWidget(self.preview_page)

    def show_banks(self) -> None:
        self.bank_list_page.refresh()
        self.stack.setCurrentWidget(self.bank_list_page)
        self.nav.setCurrentRow(0)

    def show_detail(self, bank_id: int) -> None:
        self.detail_page.load_bank(bank_id)
        self.stack.setCurrentWidget(self.detail_page)
        self.nav.setCurrentRow(0)

    def start_practice(self, bank_id: int, mode: str) -> None:
        limit = None
        question_types = None
        if mode == "随机刷题":
            questions = self.practice_page.repo.list_questions(bank_id, mode)
            dialog = RandomPracticeDialog(len(questions), self)
            if dialog.exec() != dialog.Accepted:
                return
            limit = dialog.count()
            question_types = dialog.selected_types()
        self.practice_page.load(bank_id, mode, limit=limit, question_types=question_types)
        self.stack.setCurrentWidget(self.practice_page)
        self.nav.setCurrentRow(1)
