from __future__ import annotations

import random
from typing import Any

from app.database import Database, get_database


class QuestionRepository:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or get_database()

    def list_questions(self, bank_id: int, mode: str = "顺序刷题") -> list[dict[str, Any]]:
        if mode == "错题练习":
            sql = """
            SELECT q.*, c.name AS chapter_name,
                   CASE WHEN f.id IS NULL THEN 0 ELSE 1 END AS is_favorite
            FROM questions q
            JOIN wrong_questions w ON w.question_id=q.id
            LEFT JOIN chapters c ON c.id=q.chapter_id
            LEFT JOIN favorites f ON f.question_id=q.id
            WHERE q.bank_id=?
            ORDER BY w.updated_at DESC
            """
        else:
            sql = """
            SELECT q.*, c.name AS chapter_name,
                   CASE WHEN f.id IS NULL THEN 0 ELSE 1 END AS is_favorite
            FROM questions q
            LEFT JOIN chapters c ON c.id=q.chapter_id
            LEFT JOIN favorites f ON f.question_id=q.id
            WHERE q.bank_id=?
            ORDER BY q.id
            """
        with self.db.connect() as conn:
            items = [dict(row) for row in conn.execute(sql, (bank_id,)).fetchall()]
        if mode == "随机刷题":
            random.shuffle(items)
        return items

    def get_question(self, question_id: int) -> dict[str, Any] | None:
        sql = """
        SELECT q.*, c.name AS chapter_name,
               CASE WHEN f.id IS NULL THEN 0 ELSE 1 END AS is_favorite
        FROM questions q
        LEFT JOIN chapters c ON c.id=q.chapter_id
        LEFT JOIN favorites f ON f.question_id=q.id
        WHERE q.id=?
        """
        with self.db.connect() as conn:
            row = conn.execute(sql, (question_id,)).fetchone()
            return dict(row) if row else None

    def list_favorites(self, bank_id: int | None = None) -> list[dict[str, Any]]:
        params: tuple[Any, ...] = ()
        where = ""
        if bank_id:
            where = "AND q.bank_id=?"
            params = (bank_id,)
        sql = f"""
        SELECT q.*, b.name AS bank_name, c.name AS chapter_name, f.created_at AS favorite_at
        FROM favorites f
        JOIN questions q ON q.id=f.question_id
        JOIN question_banks b ON b.id=q.bank_id
        LEFT JOIN chapters c ON c.id=q.chapter_id
        WHERE 1=1 {where}
        ORDER BY f.created_at DESC
        """
        with self.db.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def list_wrong_questions(self) -> list[dict[str, Any]]:
        sql = """
        SELECT q.*, b.name AS bank_name, c.name AS chapter_name, w.wrong_count,
               w.continuous_correct_count, w.mastery_status, w.last_wrong_at
        FROM wrong_questions w
        JOIN questions q ON q.id=w.question_id
        JOIN question_banks b ON b.id=q.bank_id
        LEFT JOIN chapters c ON c.id=q.chapter_id
        ORDER BY w.updated_at DESC
        """
        with self.db.connect() as conn:
            return [dict(row) for row in conn.execute(sql).fetchall()]

    def toggle_favorite(self, question_id: int, bank_id: int) -> bool:
        with self.db.transaction() as conn:
            row = conn.execute("SELECT id FROM favorites WHERE question_id=?", (question_id,)).fetchone()
            if row:
                conn.execute("DELETE FROM favorites WHERE question_id=?", (question_id,))
                return False
            conn.execute("INSERT INTO favorites(question_id, bank_id) VALUES (?, ?)", (question_id, bank_id))
            return True

    def remove_favorite(self, question_id: int) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM favorites WHERE question_id=?", (question_id,))

    def mark_mastered(self, question_id: int) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE wrong_questions SET mastery_status='已掌握', updated_at=CURRENT_TIMESTAMP WHERE question_id=?",
                (question_id,),
            )

    def remove_wrong(self, question_id: int) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM wrong_questions WHERE question_id=?", (question_id,))

