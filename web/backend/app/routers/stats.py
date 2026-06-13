from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import current_user
from app.models import AnswerRecord, QuestionBank, User, WrongQuestion

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    records = db.scalars(select(AnswerRecord).where(AnswerRecord.user_id == user.id)).all()
    total = len(records)
    correct = sum(1 for item in records if item.is_correct)
    wrong = total - correct
    by_bank = []
    banks = db.scalars(select(QuestionBank).where((QuestionBank.owner_id == user.id) | (QuestionBank.is_public == True))).all()
    for bank in banks:
        bank_records = [r for r in records if r.bank_id == bank.id]
        bank_correct = sum(1 for r in bank_records if r.is_correct)
        wrong_count = db.scalar(select(func.count()).select_from(WrongQuestion).where(WrongQuestion.user_id == user.id, WrongQuestion.bank_id == bank.id)) or 0
        by_bank.append({
            "bank_id": bank.id,
            "bank_name": bank.name,
            "total": len(bank_records),
            "accuracy": round(bank_correct * 100 / len(bank_records), 1) if bank_records else 0,
            "wrong_count": wrong_count,
            "last_study_at": bank.last_study_at,
        })
    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "accuracy": round(correct * 100 / total, 1) if total else 0,
        "banks": by_bank,
    }
