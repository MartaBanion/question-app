from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WrongQuestion:
    id: int
    question_id: int
    bank_id: int
    wrong_count: int
    continuous_correct_count: int
    mastery_status: str
    last_wrong_at: str
    updated_at: str

