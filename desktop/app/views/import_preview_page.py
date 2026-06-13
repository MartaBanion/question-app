from __future__ import annotations

import json

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.repositories.bank_repository import BankRepository
from app.services.excel_import_service import ImportResult
from app.utils.validators import ImportedQuestion, validate_question
from app.widgets.message_dialog import info, warning


class ImportPreviewPage(QWidget):
    saved = Signal(int)
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.result: ImportResult | None = None
        self.index = 0
        self.repo = BankRepository()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 28, 34, 28)
        layout.setSpacing(14)
        self.summary = QLabel("")
        self.summary.setObjectName("PageTitle")
        layout.addWidget(self.summary)
        self.errors = QTextEdit()
        self.errors.setReadOnly(True)
        self.errors.setMaximumHeight(120)
        layout.addWidget(self.errors)
        self.question = QLabel("")
        self.question.setObjectName("QuestionPreview")
        self.question.setWordWrap(True)
        layout.addWidget(self.question, 1)
        row = QHBoxLayout()
        for text, slot in [
            ("上一题", self.prev_question),
            ("下一题", self.next_question),
            ("编辑题目", self.edit_question),
            ("删除题目", self.delete_question),
            ("仅导入正确题目", self.confirm_save),
            ("返回修改", self.cancelled.emit),
            ("取消导入", self.cancelled.emit),
        ]:
            btn = QPushButton(text)
            if text in {"上一题", "下一题", "编辑题目", "返回修改"}:
                btn.setObjectName("SecondaryButton")
            if text in {"删除题目", "取消导入"}:
                btn.setObjectName("DangerButton")
            btn.clicked.connect(slot)
            row.addWidget(btn)
        layout.addLayout(row)

    def set_result(self, result: ImportResult) -> None:
        self.result = result
        self.index = 0
        self.refresh()

    def refresh(self) -> None:
        if not self.result:
            return
        self.summary.setText(
            f"文件名称：{self.result.file_name}    共读取：{len(self.result.questions)} 题    "
            f"成功识别：{sum(q.is_valid for q in self.result.questions)} 题    "
            f"存在问题：{sum(not q.is_valid for q in self.result.questions)} 题    "
            f"重复题目：{self.result.duplicate_count} 题"
        )
        self.errors.setText("\n".join(self.result.errors) if self.result.errors else "未发现错误。")
        if not self.result.questions:
            self.question.setText("没有题目可预览")
            return
        self.index = max(0, min(self.index, len(self.result.questions) - 1))
        q = self.result.questions[self.index]
        options = "\n".join(f"{k}. {v}" for k, v in q.options.items())
        error_text = "\n".join(q.errors) if q.errors else "无"
        self.question.setText(
            f"题目 {self.index + 1} / {len(self.result.questions)}\n\n"
            f"题型：{q.question_type}\n章节：{q.chapter or '未分章'}\n难度：{q.difficulty or '未填写'}\n\n"
            f"题目：\n{q.question_text}\n\n{options}\n\n"
            f"正确答案：{q.correct_answer}\n\n解析：\n{q.analysis or '无'}\n\n校验问题：{error_text}"
        )

    def prev_question(self) -> None:
        self.index -= 1
        self.refresh()

    def next_question(self) -> None:
        self.index += 1
        self.refresh()

    def delete_question(self) -> None:
        if self.result and self.result.questions:
            self.result.questions.pop(self.index)
            self.revalidate()

    def edit_question(self) -> None:
        if not self.result or not self.result.questions:
            return
        q = self.result.questions[self.index]
        dialog = QuestionEditDialog(q, self)
        if dialog.exec() == QDialog.Accepted:
            self.result.questions[self.index] = dialog.to_question(q.row_number)
            self.revalidate()

    def revalidate(self) -> None:
        if not self.result:
            return
        seen: set[str] = set()
        errors: list[str] = []
        duplicate_count = 0
        for q in self.result.questions:
            validate_question(q, seen)
            if any("重复题目" in err for err in q.errors):
                duplicate_count += 1
            errors.extend(f"第 {q.row_number} 行：{err}" for err in q.errors)
        self.result.errors = errors
        self.result.duplicate_count = duplicate_count
        self.refresh()

    def confirm_save(self) -> None:
        if not self.result:
            return
        valid = [q for q in self.result.questions if q.is_valid]
        if not valid:
            warning(self, "没有可导入的正确题目。")
            return
        dialog = BankMetaDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        name, category, desc = dialog.values()
        try:
            bank_id = self.repo.save_bank_with_questions(name, category, desc, valid)
            info(self, "题库保存成功。")
            self.saved.emit(bank_id)
        except Exception as exc:
            warning(self, f"保存题库失败：{exc}")


class QuestionEditDialog(QDialog):
    def __init__(self, q: ImportedQuestion, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("编辑题目")
        self.fields: dict[str, QLineEdit | QPlainTextEdit] = {}
        layout = QFormLayout(self)
        for name, value in [
            ("题型", q.question_type),
            ("题目", q.question_text),
            ("A选项", q.options.get("A", "")),
            ("B选项", q.options.get("B", "")),
            ("C选项", q.options.get("C", "")),
            ("D选项", q.options.get("D", "")),
            ("E选项", q.options.get("E", "")),
            ("F选项", q.options.get("F", "")),
            ("正确答案", q.correct_answer),
            ("解析", q.analysis),
            ("章节", q.chapter),
            ("难度", q.difficulty),
        ]:
            widget = QPlainTextEdit(value) if name in {"题目", "解析"} else QLineEdit(value)
            if isinstance(widget, QPlainTextEdit):
                widget.setFixedHeight(80)
            self.fields[name] = widget
            layout.addRow(name, widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _text(self, name: str) -> str:
        widget = self.fields[name]
        return widget.toPlainText() if isinstance(widget, QPlainTextEdit) else widget.text()

    def to_question(self, row_number: int) -> ImportedQuestion:
        return ImportedQuestion(
            row_number=row_number,
            question_type=self._text("题型"),
            question_text=self._text("题目"),
            options={k: self._text(f"{k}选项") for k in "ABCDEF"},
            correct_answer=self._text("正确答案"),
            analysis=self._text("解析"),
            chapter=self._text("章节"),
            difficulty=self._text("难度"),
        )


class BankMetaDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("保存题库")
        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.category = QLineEdit()
        self.desc = QPlainTextEdit()
        self.desc.setFixedHeight(80)
        layout.addRow("题库名称（必填）", self.name)
        layout.addRow("题库分类", self.category)
        layout.addRow("题库说明", self.desc)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def accept(self) -> None:
        if not self.name.text().strip():
            warning(self, "题库名称不能为空。")
            return
        super().accept()

    def values(self) -> tuple[str, str, str]:
        return self.name.text(), self.category.text(), self.desc.toPlainText()

