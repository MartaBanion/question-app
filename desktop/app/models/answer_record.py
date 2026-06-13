from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnswerRecord:
    id: int
    question_id: int
    bank_id: int
    user_answer: str
    is_correct: bool
    answer_duration: int
    practice_mode: str
    created_at: str

