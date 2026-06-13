from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_db()


def migrate_db() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if "is_admin" not in columns:
            if dialect == "postgresql":
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))
        if "last_login_at" not in columns:
            if dialect == "postgresql":
                conn.execute(text("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP WITH TIME ZONE"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_login_at DATETIME"))
        if settings.admin_username:
            conn.execute(text("UPDATE users SET is_admin = :value"), {"value": False})
            conn.execute(
                text("UPDATE users SET is_admin = :value WHERE username = :username"),
                {"value": True, "username": settings.admin_username},
            )
            return
        admin_count = conn.execute(text("SELECT COUNT(*) FROM users WHERE is_admin = :value"), {"value": True}).scalar() or 0
        if admin_count == 0:
            first_id = conn.execute(text("SELECT MIN(id) FROM users")).scalar()
            if first_id is not None:
                conn.execute(text("UPDATE users SET is_admin = :value WHERE id = :id"), {"value": True, "id": first_id})
