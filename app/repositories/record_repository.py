from __future__ import annotations

from typing import Any

from app.database import Database, get_database


class RecordRepository:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or get_database()

    def save_answer(
        self,
        question_id: int,
        bank_id: int,
        user_answer: str,
        is_correct: bool,
        answer_duration: int,
        practice_mode: str,
    ) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO answer_records(question_id, bank_id, user_answer, is_correct, answer_duration, practice_mode)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (question_id, bank_id, user_answer, 1 if is_correct else 0, answer_duration, practice_mode),
            )
            conn.execute("UPDATE question_banks SET last_study_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?", (bank_id,))
            if is_correct:
                conn.execute(
                    """
                    UPDATE wrong_questions
                    SET continuous_correct_count=continuous_correct_count+1,
                        mastery_status=CASE WHEN continuous_correct_count+1 >= 2 THEN '已掌握' ELSE mastery_status END,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE question_id=?
                    """,
                    (question_id,),
                )
            else:
                row = conn.execute("SELECT id FROM wrong_questions WHERE question_id=?", (question_id,)).fetchone()
                if row:
                    conn.execute(
                        """
                        UPDATE wrong_questions
                        SET wrong_count=wrong_count+1, continuous_correct_count=0, mastery_status='复习中',
                            last_wrong_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
                        WHERE question_id=?
                        """,
                        (question_id,),
                    )
                else:
                    conn.execute(
                        "INSERT INTO wrong_questions(question_id, bank_id) VALUES (?, ?)",
                        (question_id, bank_id),
                    )

    def totals(self) -> dict[str, Any]:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) total, SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) correct,
                       SUM(CASE WHEN is_correct=0 THEN 1 ELSE 0 END) wrong,
                       MAX(created_at) last_time,
                       SUM(CASE WHEN date(created_at)=date('now','localtime') THEN 1 ELSE 0 END) today
                FROM answer_records
                """
            ).fetchone()
            return dict(row)

