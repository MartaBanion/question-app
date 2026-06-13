from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QuestionBank:
    id: int
    name: str
    category: str = ""
    description: str = ""
    question_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    last_study_at: str | None = None

