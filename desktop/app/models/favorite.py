from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Favorite:
    id: int
    question_id: int
    bank_id: int
    created_at: str

