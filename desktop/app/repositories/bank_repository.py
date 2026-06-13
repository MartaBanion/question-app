from __future__ import annotations

import sqlite3
from typing import Any

from app.database import Database, get_database
from app.models.question_bank import QuestionBank
from app.utils.validators import ImportedQuestion


class BankRepository:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or get_database()

    def has_banks(self) -> bool:
        with self.db.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM question_banks").fetchone()
            return bool(row["c"])

    def list_banks(self) -> list[dict[str, Any]]:
        sql = """
        SELECT b.*,
               COALESCE(done.done_count, 0) AS done_count,
               COALESCE(w.wrong_count, 0) AS wrong_count,
               COALESCE(ch.chapter_count, 0) AS chapter_count,
               CASE WHEN b.question_count > 0
                    THEN ROUND(COALESCE(done.done_count, 0) * 100.0 / b.question_count, 1)
                    ELSE 0 END AS progress,
               CASE WHEN done.total_count > 0
                    THEN ROUND(done.correct_count * 100.0 / done.total_count, 1)
                    ELSE 0 END AS accuracy
        FROM question_banks b
        LEFT JOIN (
            SELECT bank_id, COUNT(*) total_count, COUNT(DISTINCT question_id) done_count,
                   SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) correct_count
            FROM answer_records GROUP BY bank_id
        ) done ON done.bank_id=b.id
        LEFT JOIN (
            SELECT bank_id, COUNT(*) wrong_count FROM wrong_questions GROUP BY bank_id
        ) w ON w.bank_id=b.id
        LEFT JOIN (
            SELECT bank_id, COUNT(*) chapter_count FROM chapters GROUP BY bank_id
        ) ch ON ch.bank_id=b.id
        ORDER BY b.updated_at DESC, b.id DESC
        """
        with self.db.connect() as conn:
            return [dict(row) for row in conn.execute(sql).fetchall()]

    def get_bank(self, bank_id: int) -> dict[str, Any] | None:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM question_banks WHERE id=?", (bank_id,)).fetchone()
            return dict(row) if row else None

    def save_bank_with_questions(
        self,
        name: str,
        category: str,
        description: str,
        questions: list[ImportedQuestion],
    ) -> int:
        valid_questions = [q for q in questions if q.is_valid]
        if not name.strip():
            raise ValueError("题库名称不能为空")
        if not valid_questions:
            raise ValueError("没有可导入的正确题目")

        with self.db.transaction() as conn:
            cur = conn.execute(
                """
                INSERT INTO question_banks(name, category, description, question_count)
                VALUES (?, ?, ?, ?)
                """,
                (name.strip(), category.strip(), description.strip(), len(valid_questions)),
            )
            bank_id = int(cur.lastrowid)
            chapter_cache: dict[str, int] = {}
            for item in valid_questions:
                chapter_id = self._get_or_create_chapter(conn, bank_id, item.chapter, chapter_cache)
                conn.execute(
                    """
                    INSERT INTO questions(
                        bank_id, chapter_id, question_type, question_text, options_json,
                        correct_answer, analysis, difficulty
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bank_id,
                        chapter_id,
                        item.question_type,
                        item.question_text,
                        item.options_json(),
                        item.correct_answer,
                        item.analysis,
                        item.difficulty,
                    ),
                )
            return bank_id

    def _get_or_create_chapter(
        self,
        conn: sqlite3.Connection,
        bank_id: int,
        chapter_name: str,
        cache: dict[str, int],
    ) -> int | None:
        name = (chapter_name or "").strip()
        if not name:
            return None
        if name in cache:
            return cache[name]
        row = conn.execute("SELECT id FROM chapters WHERE bank_id=? AND name=?", (bank_id, name)).fetchone()
        if row:
            cache[name] = int(row["id"])
            return cache[name]
        count = conn.execute("SELECT COUNT(*) AS c FROM chapters WHERE bank_id=?", (bank_id,)).fetchone()["c"]
        cur = conn.execute(
            "INSERT INTO chapters(bank_id, name, sort_order) VALUES (?, ?, ?)",
            (bank_id, name, int(count) + 1),
        )
        cache[name] = int(cur.lastrowid)
        return cache[name]

    def delete_bank(self, bank_id: int) -> None:
        with self.db.transaction() as conn:
            cur = conn.execute("DELETE FROM question_banks WHERE id=?", (bank_id,))
            if cur.rowcount == 0:
                raise ValueError("题库不存在或已被删除")

    def chapters(self, bank_id: int) -> list[dict[str, Any]]:
        with self.db.connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM chapters WHERE bank_id=? ORDER BY sort_order, id", (bank_id,)
                ).fetchall()
            ]

