from __future__ import annotations

import re

TRUE_VALUES = {"正确", "对", "√", "true", "1"}
FALSE_VALUES = {"错误", "错", "×", "x", "false", "0"}


def normalize_question_type(value: str) -> str:
    text = (value or "").strip()
    return {"单选": "单选题", "多选": "多选题", "判断": "判断题", "填空": "填空题"}.get(text, text)


def normalize_choice_answer(value: str) -> str:
    text = re.sub(r"[\s，,、]+", "", (value or "").strip().upper())
    return "".join(dict.fromkeys(text))


def normalize_judge_answer(value: str) -> str | None:
    text = (value or "").strip()
    lower = text.lower()
    if text in TRUE_VALUES or lower in TRUE_VALUES:
        return "正确"
    if text in FALSE_VALUES or lower in FALSE_VALUES:
        return "错误"
    return None


def normalize_blank_answer(value: str) -> str:
    return "|".join(part.strip() for part in (value or "").split("|") if part.strip())


def normalize_answer(question_type: str, value: str) -> str:
    qtype = normalize_question_type(question_type)
    if qtype in {"单选题", "多选题"}:
        return normalize_choice_answer(value)
    if qtype == "判断题":
        return normalize_judge_answer(value) or (value or "").strip()
    if qtype == "填空题":
        return normalize_blank_answer(value)
    return (value or "").strip()


def is_answer_correct(question_type: str, correct_answer: str, user_answer: str, ignore_case: bool = True) -> bool:
    qtype = normalize_question_type(question_type)
    if qtype == "单选题":
        return normalize_choice_answer(correct_answer) == normalize_choice_answer(user_answer)
    if qtype == "多选题":
        return set(normalize_choice_answer(correct_answer)) == set(normalize_choice_answer(user_answer))
    if qtype == "判断题":
        return normalize_judge_answer(correct_answer) == normalize_judge_answer(user_answer)
    if qtype == "填空题":
        user = (user_answer or "").strip()
        choices = [part.strip() for part in (correct_answer or "").split("|") if part.strip()]
        if ignore_case:
            user = user.lower()
            choices = [part.lower() for part in choices]
        return user in choices
    return False
