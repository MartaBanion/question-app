from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.deps import admin_user
from app.models import AnswerRecord, Question, QuestionBank, User, WrongQuestion

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), _: User = Depends(admin_user)) -> dict:
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    rows: list[dict] = []
    for user in users:
        bank_count = db.scalar(select(func.count()).select_from(QuestionBank).where(QuestionBank.owner_id == user.id)) or 0
        question_count = db.scalar(
            select(func.count()).select_from(Question).join(QuestionBank, QuestionBank.id == Question.bank_id).where(QuestionBank.owner_id == user.id)
        ) or 0
        answer_count = db.scalar(select(func.count()).select_from(AnswerRecord).where(AnswerRecord.user_id == user.id)) or 0
        correct_count = db.scalar(select(func.count()).select_from(AnswerRecord).where(AnswerRecord.user_id == user.id, AnswerRecord.is_correct == True)) or 0
        wrong_count = db.scalar(select(func.count()).select_from(WrongQuestion).where(WrongQuestion.user_id == user.id)) or 0
        rows.append({
            "id": user.id,
            "username": user.username,
            "is_admin": user.username == settings.admin_username,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
            "bank_count": bank_count,
            "question_count": question_count,
            "answer_count": answer_count,
            "accuracy": round(correct_count * 100 / answer_count, 1) if answer_count else 0,
            "wrong_count": wrong_count,
        })
    return {
        "user_count": len(users),
        "bank_count": db.scalar(select(func.count()).select_from(QuestionBank)) or 0,
        "question_count": db.scalar(select(func.count()).select_from(Question)) or 0,
        "answer_count": db.scalar(select(func.count()).select_from(AnswerRecord)) or 0,
        "wrong_count": db.scalar(select(func.count()).select_from(WrongQuestion)) or 0,
        "users": rows,
    }
