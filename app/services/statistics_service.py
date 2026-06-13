from __future__ import annotations

from typing import Any

from app.database import get_database


class StatisticsService:
    def overview(self) -> dict[str, Any]:
        with get_database().connect() as conn:
            totals = conn.execute(
                """
                SELECT COUNT(*) total, SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) correct,
                       SUM(CASE WHEN is_correct=0 THEN 1 ELSE 0 END) wrong,
                       SUM(CASE WHEN date(created_at)=date('now','localtime') THEN 1 ELSE 0 END) today,
                       MAX(created_at) last_time
                FROM answer_records
                """
            ).fetchone()
            by_bank = conn.execute(
                """
                SELECT b.name bank_name, COUNT(r.id) total,
                       CASE WHEN COUNT(r.id)>0 THEN ROUND(SUM(CASE WHEN r.is_correct=1 THEN 1 ELSE 0 END)*100.0/COUNT(r.id),1) ELSE 0 END accuracy,
                       COALESCE(w.wrong_count,0) wrong_count, MAX(r.created_at) last_time
                FROM question_banks b
                LEFT JOIN answer_records r ON r.bank_id=b.id
                LEFT JOIN (SELECT bank_id, COUNT(*) wrong_count FROM wrong_questions GROUP BY bank_id) w ON w.bank_id=b.id
                GROUP BY b.id ORDER BY b.updated_at DESC
                """
            ).fetchall()
            chapters = conn.execute(
                """
                SELECT COALESCE(c.name,'未分章') chapter_name, COUNT(r.id) total,
                       CASE WHEN COUNT(r.id)>0 THEN ROUND(SUM(CASE WHEN r.is_correct=1 THEN 1 ELSE 0 END)*100.0/COUNT(r.id),1) ELSE 0 END accuracy
                FROM answer_records r
                JOIN questions q ON q.id=r.question_id
                LEFT JOIN chapters c ON c.id=q.chapter_id
                GROUP BY COALESCE(c.name,'未分章') ORDER BY total DESC
                """
            ).fetchall()
        return {
            "totals": dict(totals),
            "banks": [dict(row) for row in by_bank],
            "chapters": [dict(row) for row in chapters],
        }

    @staticmethod
    def mastery(accuracy: float) -> str:
        if accuracy >= 90:
            return "已掌握"
        if accuracy >= 70:
            return "基本掌握"
        return "需要复习"

