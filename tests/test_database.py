from app.database import Database
from app.repositories.bank_repository import BankRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.record_repository import RecordRepository
from app.utils.validators import ImportedQuestion, validate_question


def make_repo(tmp_path):
    db = Database(tmp_path / "test.db")
    return db, BankRepository(db), QuestionRepository(db), RecordRepository(db)


def valid_question(text="HTML 段落标签？"):
    q = ImportedQuestion(2, "单选题", text, {"A": "<p>", "B": "<br>"}, "A", "解析", "HTML", "简单")
    validate_question(q, set())
    return q


def test_create_bank_save_question_and_read(tmp_path):
    db, banks, questions, records = make_repo(tmp_path)
    bank_id = banks.save_bank_with_questions("网页设计", "前端", "说明", [valid_question()])
    assert banks.has_banks()
    assert banks.get_bank(bank_id)["name"] == "网页设计"
    qs = questions.list_questions(bank_id)
    assert len(qs) == 1
    assert qs[0]["question_text"] == "HTML 段落标签？"


def test_answer_record_wrong_and_favorite(tmp_path):
    db, banks, questions, records = make_repo(tmp_path)
    bank_id = banks.save_bank_with_questions("网页设计", "", "", [valid_question()])
    q = questions.list_questions(bank_id)[0]
    records.save_answer(q["id"], bank_id, "B", False, 3, "顺序刷题")
    assert len(questions.list_wrong_questions()) == 1
    questions.toggle_favorite(q["id"], bank_id)
    assert len(questions.list_favorites()) == 1
    records.save_answer(q["id"], bank_id, "A", True, 2, "顺序刷题")
    records.save_answer(q["id"], bank_id, "A", True, 2, "顺序刷题")
    assert questions.list_wrong_questions()[0]["mastery_status"] == "已掌握"


def test_delete_bank_cascades(tmp_path):
    db, banks, questions, records = make_repo(tmp_path)
    bank_id = banks.save_bank_with_questions("网页设计", "", "", [valid_question()])
    q = questions.list_questions(bank_id)[0]
    records.save_answer(q["id"], bank_id, "B", False, 3, "顺序刷题")
    questions.toggle_favorite(q["id"], bank_id)
    banks.delete_bank(bank_id)
    assert banks.list_banks() == []
    assert questions.list_wrong_questions() == []
    assert questions.list_favorites() == []
