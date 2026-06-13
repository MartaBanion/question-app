from __future__ import annotations

from app.repositories.question_repository import QuestionRepository
from app.repositories.record_repository import RecordRepository
from app.utils.answer_utils import is_answer_correct


class QuestionService:
    def __init__(self) -> None:
        self.questions = QuestionRepository()
        self.records = RecordRepository()

    def submit_answer(self, question: dict, user_answer: str, duration: int, mode: str, ignore_case: bool = True) -> bool:
        correct = is_answer_correct(question["question_type"], question["correct_answer"], user_answer, ignore_case)
        self.records.save_answer(question["id"], question["bank_id"], user_answer, correct, duration, mode)
        return correct

