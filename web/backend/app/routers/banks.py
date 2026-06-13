from __future__ import annotations

import json
from random import shuffle

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import current_user
from app.models import AnswerRecord, Chapter, Favorite, Question, QuestionBank, User, WrongQuestion
from app.schemas import BankOut, ImportConfirm, QuestionOut
from app.services.importer import import_excel_upload

router = APIRouter(prefix="/banks", tags=["banks"])


def _can_access(bank: QuestionBank, user: User) -> bool:
    return bank.owner_id == user.id or bank.is_public


def _chapter_id(db: Session, bank_id: int, name: str, cache: dict[str, int]) -> int | None:
    clean = (name or "").strip()
    if not clean:
        return None
    if clean in cache:
        return cache[clean]
    chapter = db.scalar(select(Chapter).where(Chapter.bank_id == bank_id, Chapter.name == clean))
    if not chapter:
        count = db.scalar(select(func.count()).select_from(Chapter).where(Chapter.bank_id == bank_id)) or 0
        chapter = Chapter(bank_id=bank_id, name=clean, sort_order=count + 1)
        db.add(chapter)
        db.flush()
    cache[clean] = chapter.id
    return chapter.id


@router.get("", response_model=list[BankOut])
def list_banks(db: Session = Depends(get_db), user: User = Depends(current_user)) -> list[BankOut]:
    banks = db.scalars(select(QuestionBank).where((QuestionBank.owner_id == user.id) | (QuestionBank.is_public == True)).order_by(QuestionBank.updated_at.desc())).all()
    result: list[BankOut] = []
    for bank in banks:
        records = db.execute(select(AnswerRecord.is_correct, AnswerRecord.question_id).where(AnswerRecord.user_id == user.id, AnswerRecord.bank_id == bank.id)).all()
        done_count = len({r.question_id for r in records})
        total_records = len(records)
        correct = sum(1 for r in records if r.is_correct)
        wrong_count = db.scalar(select(func.count()).select_from(WrongQuestion).where(WrongQuestion.user_id == user.id, WrongQuestion.bank_id == bank.id)) or 0
        result.append(BankOut(
            id=bank.id,
            name=bank.name,
            category=bank.category,
            description=bank.description,
            question_count=bank.question_count,
            is_public=bank.is_public,
            done_count=done_count,
            wrong_count=wrong_count,
            accuracy=round(correct * 100 / total_records, 1) if total_records else 0,
            progress=round(done_count * 100 / bank.question_count, 1) if bank.question_count else 0,
        ))
    return result


@router.post("/import/preview")
async def import_preview(file: UploadFile = File(...), user: User = Depends(current_user)) -> dict:
    try:
        return await import_excel_upload(file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/confirm")
def import_confirm(payload: ImportConfirm, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    valid_questions = [q for q in payload.questions if q.is_valid and not q.errors]
    if not valid_questions:
        raise HTTPException(status_code=400, detail="没有可导入的正确题目")
    bank = QuestionBank(
        owner_id=user.id,
        name=payload.name.strip(),
        category=payload.category.strip(),
        description=payload.description.strip(),
        is_public=payload.is_public,
        question_count=len(valid_questions),
    )
    db.add(bank)
    db.flush()
    chapter_cache: dict[str, int] = {}
    for item in valid_questions:
        db.add(Question(
            bank_id=bank.id,
            chapter_id=_chapter_id(db, bank.id, item.chapter, chapter_cache),
            question_type=item.question_type,
            question_text=item.question_text,
            options_json=json.dumps(item.options, ensure_ascii=False),
            correct_answer=item.correct_answer,
            analysis=item.analysis,
            difficulty=item.difficulty,
        ))
    db.commit()
    return {"bank_id": bank.id, "question_count": len(valid_questions)}


@router.get("/{bank_id}")
def bank_detail(bank_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    bank = db.get(QuestionBank, bank_id)
    if not bank or not _can_access(bank, user):
        raise HTTPException(status_code=404, detail="题库不存在")
    chapters = db.execute(
        select(Chapter.name, func.count(Question.id)).join(Question, Question.chapter_id == Chapter.id, isouter=True).where(Chapter.bank_id == bank.id).group_by(Chapter.id).order_by(Chapter.sort_order)
    ).all()
    return {
        "id": bank.id,
        "name": bank.name,
        "category": bank.category,
        "description": bank.description,
        "question_count": bank.question_count,
        "is_public": bank.is_public,
        "last_study_at": bank.last_study_at,
        "chapters": [{"name": name, "question_count": count} for name, count in chapters],
    }


@router.delete("/{bank_id}")
def delete_bank(bank_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    bank = db.get(QuestionBank, bank_id)
    if not bank or bank.owner_id != user.id:
        raise HTTPException(status_code=404, detail="题库不存在或无权限删除")
    db.delete(bank)
    db.commit()
    return {"ok": True}


@router.get("/{bank_id}/questions", response_model=list[QuestionOut])
def list_questions(bank_id: int, mode: str = "顺序刷题", limit: int | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)) -> list[QuestionOut]:
    bank = db.get(QuestionBank, bank_id)
    if not bank or not _can_access(bank, user):
        raise HTTPException(status_code=404, detail="题库不存在")
    stmt = select(Question, Chapter.name, Favorite.id).join(Chapter, Chapter.id == Question.chapter_id, isouter=True).join(Favorite, and_(Favorite.question_id == Question.id, Favorite.user_id == user.id), isouter=True).where(Question.bank_id == bank.id).order_by(Question.id)
    if mode == "错题练习":
        stmt = stmt.join(WrongQuestion, and_(WrongQuestion.question_id == Question.id, WrongQuestion.user_id == user.id)).order_by(WrongQuestion.updated_at.desc())
    rows = db.execute(stmt).all()
    if mode == "随机刷题":
        rows = list(rows)
        shuffle(rows)
    if limit:
        rows = rows[:limit]
    show_answer = mode == "背题模式"
    return [QuestionOut(
        id=q.id,
        bank_id=q.bank_id,
        question_type=q.question_type,
        question_text=q.question_text,
        options=json.loads(q.options_json or "{}"),
        correct_answer=q.correct_answer if show_answer else None,
        analysis=q.analysis if show_answer else None,
        difficulty=q.difficulty,
        chapter_name=chapter_name or "未分章",
        is_favorite=bool(favorite_id),
    ) for q, chapter_name, favorite_id in rows]
