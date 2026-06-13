from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.utils.answer_utils import normalize_answer, normalize_judge_answer, normalize_question_type

OPTION_KEYS = ("A", "B", "C", "D", "E", "F")


@dataclass
class ImportedQuestion:
    row_number: int
    question_type: str
    question_text: str
    options: dict[str, str]
    correct_answer: str
    analysis: str = ""
    chapter: str = ""
    difficulty: str = ""
    errors: list[str] = field(default_factory=list)

    def options_json(self) -> str:
        return json.dumps(self.options, ensure_ascii=False)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_question(question: ImportedQuestion, seen_texts: set[str] | None = None) -> ImportedQuestion:
    q = question
    q.errors.clear()
    q.question_type = normalize_question_type(q.question_type)
    q.question_text = (q.question_text or "").strip()
    q.correct_answer = normalize_answer(q.question_type, q.correct_answer)
    q.analysis = (q.analysis or "").strip()
    q.chapter = (q.chapter or "").strip()
    q.difficulty = (q.difficulty or "").strip()
    q.options = {k: (v or "").strip() for k, v in q.options.items() if (v or "").strip()}

    if not q.question_text:
        q.errors.append("题目内容为空")
    if seen_texts is not None and q.question_text:
        if q.question_text in seen_texts:
            q.errors.append("存在重复题目")
        else:
            seen_texts.add(q.question_text)
    if q.question_type not in {"单选题", "多选题", "判断题", "填空题"}:
        q.errors.append("题型不支持")
    if not q.correct_answer:
        q.errors.append("正确答案为空")

    if q.question_type == "单选题":
        _validate_single(q)
    elif q.question_type == "多选题":
        _validate_multiple(q)
    elif q.question_type == "判断题":
        if normalize_judge_answer(q.correct_answer) is None:
            q.errors.append("判断题答案无法识别")
        else:
            q.correct_answer = normalize_judge_answer(q.correct_answer) or q.correct_answer
    elif q.question_type == "填空题":
        if not q.correct_answer:
            q.errors.append("填空题答案不能为空")
    return q


def _validate_single(q: ImportedQuestion) -> None:
    if len(q.options) < 2:
        q.errors.append("单选题至少需要两个选项")
    if len(q.correct_answer) != 1 or not q.correct_answer.isalpha():
        q.errors.append("单选题正确答案不能填写多个选项")
        return
    if q.correct_answer not in q.options:
        q.errors.append("单选题正确答案必须对应已有选项")


def _validate_multiple(q: ImportedQuestion) -> None:
    if len(q.options) < 2:
        q.errors.append("多选题至少需要两个选项")
    if len(q.correct_answer) < 2:
        q.errors.append("多选题正确答案至少包含两个选项")
    for letter in q.correct_answer:
        if letter not in q.options:
            q.errors.append(f"多选题答案 {letter} 没有对应选项")
            break

