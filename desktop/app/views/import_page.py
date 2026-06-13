from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QProgressBar, QTextEdit, QVBoxLayout, QWidget

from app.services.excel_import_service import ExcelImportService, ImportResult
from app.services.template_service import SAMPLE_NAME, TEMPLATE_NAME, TemplateService
from app.widgets.page_header import PageHeader
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton
from app.widgets.toast import show_toast
from app.widgets.message_dialog import warning


class ImportPage(QWidget):
    imported = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.template_service = TemplateService()
        self.import_service = ExcelImportService()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        layout.addWidget(PageHeader("导入题库", "通过标准模板快速创建并导入自己的题库。"))

        template_card = self._card("1  下载题库模板", "请先下载模板，按照填写说明录入题目。")
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        blank_btn = SecondaryButton("下载空白模板")
        sample_btn = SecondaryButton("下载示例题库")
        help_btn = SecondaryButton("查看填写说明")
        blank_btn.clicked.connect(lambda: self.download_template(False))
        sample_btn.clicked.connect(lambda: self.download_template(True))
        help_btn.clicked.connect(self.show_help)
        row1.addWidget(blank_btn)
        row1.addWidget(sample_btn)
        row1.addWidget(help_btn)
        row1.addStretch()
        template_card.layout().addLayout(row1)
        layout.addWidget(template_card)

        import_card = self._card("2  导入填写完成的文件", "支持 .xlsx，建议文件不超过 20MB。")
        self.drop = QFrame()
        self.drop.setObjectName("DropArea")
        self.drop.setProperty("dragging", False)
        drop_layout = QVBoxLayout(self.drop)
        drop_layout.setContentsMargins(22, 24, 22, 24)
        drop_layout.setSpacing(12)
        self.drop_title = QLabel("将 Excel 文件拖到这里")
        self.drop_title.setObjectName("sectionTitle")
        self.drop_title.setAlignment(Qt.AlignHCenter)
        self.file_label = QLabel("或点击下方按钮选择文件")
        self.file_label.setObjectName("mutedText")
        self.file_label.setAlignment(Qt.AlignHCenter)
        choose_btn = PrimaryButton("选择 Excel 文件")
        choose_btn.clicked.connect(self.choose_file)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        drop_layout.addWidget(self.drop_title)
        drop_layout.addWidget(self.file_label)
        drop_layout.addWidget(choose_btn, alignment=Qt.AlignHCenter)
        drop_layout.addWidget(self.progress)
        import_card.layout().addWidget(self.drop)
        self.status_card = QFrame()
        self.status_card.setObjectName("statusCard")
        self.status_card.hide()
        status_layout = QVBoxLayout(self.status_card)
        status_layout.setContentsMargins(14, 12, 14, 12)
        self.status_text = QLabel("")
        self.status_text.setWordWrap(True)
        status_layout.addWidget(self.status_text)
        import_card.layout().addWidget(self.status_card)
        layout.addWidget(import_card)

        other_card = self._card("3  其他导入方式", "文本和 TXT 导入接口已预留，当前版本优先使用 Excel 模板。")
        row3 = QHBoxLayout()
        paste_btn = SecondaryButton("粘贴题目文本（预留）")
        txt_btn = SecondaryButton("导入 TXT 文件（预留）")
        paste_btn.clicked.connect(lambda: warning(self, "文本粘贴导入将在后续版本开放，当前请使用 Excel 模板。"))
        txt_btn.clicked.connect(lambda: warning(self, "TXT 导入将在后续版本开放，当前请使用 Excel 模板。"))
        row3.addWidget(paste_btn)
        row3.addWidget(txt_btn)
        row3.addStretch()
        other_card.layout().addLayout(row3)
        layout.addWidget(other_card)
        layout.addStretch()

    def _card(self, title_text: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setObjectName("StepCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        title = QLabel(title_text)
        title.setObjectName("sectionTitle")
        desc = QLabel(subtitle)
        desc.setObjectName("mutedText")
        desc.setWordWrap(True)
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        return card

    def download_template(self, sample: bool) -> None:
        default_name = SAMPLE_NAME if sample else TEMPLATE_NAME
        path, _ = QFileDialog.getSaveFileName(self, "保存模板", default_name, "Excel 文件 (*.xlsx)")
        if not path:
            return
        try:
            self.template_service.copy_template(sample, path)
            show_toast(self, f"模板已保存：{Path(path).name}", "success")
        except Exception as exc:
            self.show_status(f"模板保存失败：{exc}", "error")

    def show_help(self) -> None:
        text = QTextEdit()
        text.setReadOnly(True)
        text.setText(
            "题型支持：单选题、单选、多选题、多选、判断题、判断、填空题、填空。\n\n"
            "单选题答案填写 A；多选题填写 ABD 或 A,B,D。\n"
            "判断题支持：正确、错误、对、错、√、×、True、False、1、0。\n"
            "填空题多个答案使用 | 分隔，例如 html|htm。\n"
            "解析、章节、难度允许为空。"
        )
        text.resize(560, 340)
        text.setWindowTitle("填写说明")
        text.show()
        self._help_window = text

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择 Excel 题库", "", "Excel 文件 (*.xlsx)")
        if path:
            self.import_excel(path)

    def import_excel(self, path: str | Path) -> None:
        file_path = Path(path)
        if file_path.exists():
            size_mb = file_path.stat().st_size / 1024 / 1024
            self.file_label.setText(f"已选择：{file_path.name} · {size_mb:.2f} MB")
        self.progress.show()
        self.progress.setValue(20)
        self.show_status("正在读取并校验题库，请稍候...", "info")
        try:
            result: ImportResult = self.import_service.import_file(path)
            self.progress.setValue(100)
            self.show_status(
                f"导入校验完成：共读取 {result.total_count} 题，成功识别 {result.valid_count} 题，存在问题 {result.error_count} 题。",
                "success" if result.error_count == 0 else "error",
            )
            self.imported.emit(result)
        except Exception as exc:
            self.progress.setValue(0)
            self.show_status(f"导入失败：{exc}", "error")

    def show_status(self, text: str, status: str) -> None:
        self.status_card.setProperty("status", status)
        self.status_text.setText(text)
        self.status_card.style().unpolish(self.status_card)
        self.status_card.style().polish(self.status_card)
        self.status_card.show()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            self.drop.setProperty("dragging", True)
            self.drop.style().unpolish(self.drop)
            self.drop.style().polish(self.drop)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self.drop.setProperty("dragging", False)
        self.drop.style().unpolish(self.drop)
        self.drop.style().polish(self.drop)
        event.accept()

    def dropEvent(self, event) -> None:
        self.drop.setProperty("dragging", False)
        self.drop.style().unpolish(self.drop)
        self.drop.style().polish(self.drop)
        urls = event.mimeData().urls()
        if urls:
            self.import_excel(urls[0].toLocalFile())
