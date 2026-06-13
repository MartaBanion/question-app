from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Question:
    id: int
    bank_id: int
    chapter_id: int | None
    question_type: str
    question_text: str
    options_json: str
    correct_answer: str
    analysis: str = ""
    difficulty: str = ""
    chapter_name: str = ""
    is_favorite: bool = False

