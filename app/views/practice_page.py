from __future__ import annotations

import json
import random
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QProgressBar, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.repositories.bank_repository import BankRepository
from app.repositories.question_repository import QuestionRepository
from app.services.question_service import QuestionService
from app.utils.answer_utils import normalize_choice_answer
from app.widgets.page_header import PageHeader
from app.widgets.primary_button import PrimaryButton
from app.widgets.question_option import QuestionOption
from app.widgets.secondary_button import DangerButton, SecondaryButton
from app.widgets.toast import show_toast
from app.widgets.message_dialog import warning


class PracticePage(QWidget):
    exit_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.repo = QuestionRepository()
        self.bank_repo = BankRepository()
        self.service = QuestionService()
        self.questions: list[dict] = []
        self.index = 0
        self.mode = "顺序刷题"
        self.bank_name = "题库"
        self.start_time = time.time()
        self.option_cards: dict[str, QuestionOption] = {}
        self.selected: set[str] = set()
        self.submitted = False
        self.blank_input: QLineEdit | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 26, 32, 26)
        root.setSpacing(14)
        self.header = PageHeader("刷题", "选择答案后提交，系统会记录答题结果并更新错题本。")
        root.addWidget(self.header)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        root.addWidget(self.progress_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(14)
        self.panel = QFrame()
        self.panel.setObjectName("practicePanel")
        self.panel.setMaximumWidth(900)
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(26, 24, 26, 24)
        panel_layout.setSpacing(16)
        self.meta = QLabel("")
        self.meta.setObjectName("practiceMeta")
        self.title = QLabel("")
        self.title.setObjectName("practiceTitle")
        self.title.setWordWrap(True)
        self.title.setTextInteractionFlags(Qt.TextSelectableByMouse)
        panel_layout.addWidget(self.meta)
        panel_layout.addWidget(self.title)
        self.answer_area = QVBoxLayout()
        self.answer_area.setSpacing(12)
        panel_layout.addLayout(self.answer_area)
        self.result = QLabel("")
        self.result.setObjectName("answerPanel")
        self.result.setWordWrap(True)
        self.result.hide()
        panel_layout.addWidget(self.result)
        self.scroll_layout.addWidget(self.panel, alignment=Qt.AlignHCenter)
        self.scroll_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
        root.addWidget(self.scroll, 1)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.prev_btn = SecondaryButton("上一题")
        self.next_btn = SecondaryButton("下一题")
        self.favorite_btn = SecondaryButton("收藏")
        self.submit_btn = PrimaryButton("提交答案")
        self.exit_btn = DangerButton("退出练习")
        self.prev_btn.clicked.connect(self.prev_question)
        self.next_btn.clicked.connect(self.next_question)
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        self.submit_btn.clicked.connect(self.submit_answer)
        self.exit_btn.clicked.connect(self.exit_requested.emit)
        row.addWidget(self.prev_btn)
        row.addWidget(self.next_btn)
        row.addStretch()
        row.addWidget(self.favorite_btn)
        row.addWidget(self.submit_btn)
        row.addWidget(self.exit_btn)
        root.addLayout(row)

    def load(self, bank_id: int, mode: str, limit: int | None = None, question_types: list[str] | None = None) -> None:
        self.mode = mode
        bank = self.bank_repo.get_bank(bank_id)
        self.bank_name = bank["name"] if bank else "题库"
        self.questions = self.repo.list_questions(bank_id, mode)
        if question_types:
            self.questions = [q for q in self.questions if q["question_type"] in question_types]
        if mode == "随机刷题":
            random.shuffle(self.questions)
        if limit:
            self.questions = self.questions[:limit]
        self.index = 0
        self.show_question()

    def show_question(self) -> None:
        self.clear_answers()
        self.result.hide()
        self.result.setText("")
        self.submitted = False
        self.selected.clear()
        if not self.questions:
            self.header = PageHeader("暂无可练习题目", "当前模式下没有题目。")
            self.meta.setText("")
            self.title.setText("当前模式下没有题目。")
            self.submit_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            return
        self.submit_btn.setEnabled(self.mode != "背题模式")
        self.start_time = time.time()
        q = self.questions[self.index]
        progress = int((self.index + 1) * 100 / len(self.questions))
        self.progress_bar.setValue(progress)
        self.header.findChild(QLabel, "pageTitle").setText(f"{self.bank_name}")
        self.header.findChild(QLabel, "pageSubTitle").setText(f"{self.mode} · 第 {self.index + 1} / {len(self.questions)} 题")
        self.meta.setText(f"{q['question_type']}    {q.get('chapter_name') or '未分章'}    {q.get('difficulty') or '未填写'}")
        self.title.setText(f"{self.index + 1}. {q['question_text']}")
        self.favorite_btn.setText("已收藏" if q.get("is_favorite") else "收藏")
        qtype = q["question_type"]
        options = json.loads(q.get("options_json") or "{}")
        if qtype in {"单选题", "多选题"}:
            for key, value in options.items():
                card = QuestionOption(key, value, multi=qtype == "多选题")
                card.clicked.connect(self.select_option)
                self.option_cards[key] = card
                self.answer_area.addWidget(card)
        elif qtype == "判断题":
            for value in ["正确", "错误"]:
                card = QuestionOption(value, value)
                card.clicked.connect(self.select_option)
                self.option_cards[value] = card
                self.answer_area.addWidget(card)
        else:
            self.blank_input = QLineEdit()
            self.blank_input.setPlaceholderText("请输入答案")
            self.blank_input.setMinimumHeight(44)
            self.answer_area.addWidget(self.blank_input)
        if self.mode == "背题模式":
            self.show_answer_panel(True, "", locked=True)

    def clear_answers(self) -> None:
        while self.answer_area.count():
            item = self.answer_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.option_cards = {}
        self.blank_input = None

    def select_option(self, key: str) -> None:
        if self.submitted:
            return
        qtype = self.questions[self.index]["question_type"]
        if qtype == "多选题":
            if key in self.selected:
                self.selected.remove(key)
            else:
                self.selected.add(key)
        else:
            self.selected = {key}
        for option_key, card in self.option_cards.items():
            card.set_selected(option_key in self.selected)

    def selected_answer(self) -> str:
        q = self.questions[self.index]
        if q["question_type"] == "填空题":
            return self.blank_input.text() if self.blank_input else ""
        if q["question_type"] == "判断题":
            return next(iter(self.selected), "")
        return "".join(sorted(self.selected))

    def submit_answer(self) -> None:
        if not self.questions or self.submitted:
            return
        answer = self.selected_answer()
        if not answer.strip():
            warning(self, "请先填写或选择答案。")
            return
        q = self.questions[self.index]
        duration = int(time.time() - self.start_time)
        correct = self.service.submit_answer(q, answer, duration, self.mode)
        self.submitted = True
        self.submit_btn.setEnabled(False)
        self.show_answer_panel(correct, answer, locked=True)

    def show_answer_panel(self, correct: bool, answer: str, locked: bool) -> None:
        q = self.questions[self.index]
        correct_answer = q["correct_answer"]
        qtype = q["question_type"]
        if locked:
            for card in self.option_cards.values():
                card.set_locked(True)
            if self.blank_input:
                self.blank_input.setEnabled(False)
        if qtype in {"单选题", "多选题"}:
            correct_set = set(normalize_choice_answer(correct_answer))
            selected_set = set(normalize_choice_answer(answer))
            for key, card in self.option_cards.items():
                if key in correct_set:
                    card.set_state("correct", "正确答案")
                elif key in selected_set:
                    card.set_state("wrong", "你的选择")
        elif qtype == "判断题":
            for key, card in self.option_cards.items():
                if key == correct_answer:
                    card.set_state("correct", "正确答案")
                elif key == answer:
                    card.set_state("wrong", "你的选择")
        status = "success" if correct else "error"
        self.result.setProperty("status", status)
        self.result.style().unpolish(self.result)
        self.result.style().polish(self.result)
        self.result.setText(
            f"{'回答正确' if correct else '回答错误'}\n\n"
            f"你的答案：{answer or '未作答'}\n"
            f"正确答案：{correct_answer}\n\n"
            f"解析\n{q.get('analysis') or '暂无解析'}"
        )
        self.result.show()

    def prev_question(self) -> None:
        if self.questions:
            self.index = max(0, self.index - 1)
            self.show_question()

    def next_question(self) -> None:
        if self.questions:
            self.index = min(len(self.questions) - 1, self.index + 1)
            self.show_question()

    def toggle_favorite(self) -> None:
        if not self.questions:
            return
        q = self.questions[self.index]
        state = self.repo.toggle_favorite(q["id"], q["bank_id"])
        q["is_favorite"] = 1 if state else 0
        self.favorite_btn.setText("已收藏" if state else "收藏")
        show_toast(self, "已收藏" if state else "已取消收藏", "success")
