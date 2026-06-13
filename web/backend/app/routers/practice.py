from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import current_user
from app.models import AnswerRecord, Favorite, Question, QuestionBank, User, WrongQuestion
from app.schemas import AnswerResult, AnswerSubmit
from app.services.answer_utils import is_answer_correct

router = APIRouter(prefix="/practice", tags=["practice"])


@router.post("/answer", response_model=AnswerResult)
def submit_answer(payload: AnswerSubmit, db: Session = Depends(get_db), user: User = Depends(current_user)) -> AnswerResult:
    question = db.get(Question, payload.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    bank = db.get(QuestionBank, question.bank_id)
    if not bank or (bank.owner_id != user.id and not bank.is_public):
        raise HTTPException(status_code=404, detail="题目不存在")
    correct = is_answer_correct(question.question_type, question.correct_answer, payload.user_answer)
    db.add(AnswerRecord(
        user_id=user.id,
        question_id=question.id,
        bank_id=question.bank_id,
        user_answer=payload.user_answer,
        is_correct=correct,
        answer_duration=payload.answer_duration,
        practice_mode=payload.practice_mode,
    ))
    bank.last_study_at = func.now()
    wrong = db.scalar(select(WrongQuestion).where(WrongQuestion.user_id == user.id, WrongQuestion.question_id == question.id))
    if correct:
        if wrong:
            wrong.continuous_correct_count += 1
            if wrong.continuous_correct_count >= 2:
                wrong.mastery_status = "已掌握"
    else:
        if wrong:
            wrong.wrong_count += 1
            wrong.continuous_correct_count = 0
            wrong.mastery_status = "复习中"
            wrong.last_wrong_at = func.now()
        else:
            db.add(WrongQuestion(user_id=user.id, question_id=question.id, bank_id=question.bank_id))
    db.commit()
    return AnswerResult(is_correct=correct, correct_answer=question.correct_answer, analysis=question.analysis)


@router.post("/questions/{question_id}/favorite")
def toggle_favorite(question_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    question = db.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    existing = db.scalar(select(Favorite).where(Favorite.user_id == user.id, Favorite.question_id == question_id))
    if existing:
        db.delete(existing)
        db.commit()
        return {"is_favorite": False}
    db.add(Favorite(user_id=user.id, question_id=question.id, bank_id=question.bank_id))
    db.commit()
    return {"is_favorite": True}


@router.get("/wrong")
def wrong_questions(db: Session = Depends(get_db), user: User = Depends(current_user)) -> list[dict]:
    rows = db.execute(
        select(WrongQuestion, Question, QuestionBank.name).join(Question, Question.id == WrongQuestion.question_id).join(QuestionBank, QuestionBank.id == WrongQuestion.bank_id).where(WrongQuestion.user_id == user.id).order_by(WrongQuestion.updated_at.desc())
    ).all()
    return [{
        "question_id": q.id,
        "bank_id": q.bank_id,
        "bank_name": bank_name,
        "question_text": q.question_text,
        "question_type": q.question_type,
        "options": json.loads(q.options_json or "{}"),
        "correct_answer": q.correct_answer,
        "analysis": q.analysis,
        "wrong_count": w.wrong_count,
        "mastery_status": w.mastery_status,
        "last_wrong_at": w.last_wrong_at,
    } for w, q, bank_name in rows]


@router.get("/favorites")
def favorites(db: Session = Depends(get_db), user: User = Depends(current_user)) -> list[dict]:
    rows = db.execute(
        select(Favorite, Question, QuestionBank.name).join(Question, Question.id == Favorite.question_id).join(QuestionBank, QuestionBank.id == Favorite.bank_id).where(Favorite.user_id == user.id).order_by(Favorite.created_at.desc())
    ).all()
    return [{
        "question_id": q.id,
        "bank_id": q.bank_id,
        "bank_name": bank_name,
        "question_text": q.question_text,
        "question_type": q.question_type,
        "created_at": fav.created_at,
    } for fav, q, bank_name in rows]
