from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import DATA_DIR, DB_PATH


class DatabaseError(RuntimeError):
    pass


class Database:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or os.environ.get("QUESTION_APP_DB", DB_PATH))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as exc:
            raise DatabaseError(f"数据库连接失败：{exc}") from exc

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            conn.execute("BEGIN")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with self.connect() as conn:
                conn.executescript(SCHEMA_SQL)
        except sqlite3.Error as exc:
            raise DatabaseError(f"数据库初始化失败：{exc}") from exc


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS question_banks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT DEFAULT '',
    description TEXT DEFAULT '',
    question_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_study_at TEXT
);

CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    UNIQUE(bank_id, name),
    FOREIGN KEY(bank_id) REFERENCES question_banks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id INTEGER NOT NULL,
    chapter_id INTEGER,
    question_type TEXT NOT NULL,
    question_text TEXT NOT NULL,
    options_json TEXT DEFAULT '{}',
    correct_answer TEXT NOT NULL,
    analysis TEXT DEFAULT '',
    difficulty TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(bank_id) REFERENCES question_banks(id) ON DELETE CASCADE,
    FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS answer_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    bank_id INTEGER NOT NULL,
    user_answer TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    answer_duration INTEGER DEFAULT 0,
    practice_mode TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY(bank_id) REFERENCES question_banks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS wrong_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL UNIQUE,
    bank_id INTEGER NOT NULL,
    wrong_count INTEGER DEFAULT 1,
    continuous_correct_count INTEGER DEFAULT 0,
    mastery_status TEXT DEFAULT '未掌握',
    last_wrong_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY(bank_id) REFERENCES question_banks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL UNIQUE,
    bank_id INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY(bank_id) REFERENCES question_banks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_bank ON questions(bank_id);
CREATE INDEX IF NOT EXISTS idx_questions_chapter ON questions(chapter_id);
CREATE INDEX IF NOT EXISTS idx_records_question ON answer_records(question_id);
CREATE INDEX IF NOT EXISTS idx_records_bank ON answer_records(bank_id);
CREATE INDEX IF NOT EXISTS idx_wrong_bank ON wrong_questions(bank_id);
CREATE INDEX IF NOT EXISTS idx_favorites_bank ON favorites(bank_id);
"""


_db: Database | None = None


def get_database() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db

