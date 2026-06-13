from app.utils.answer_utils import is_answer_correct, normalize_answer, normalize_judge_answer


def test_single_choice():
    assert is_answer_correct("单选题", "A", " a ")
    assert not is_answer_correct("单选题", "A", "B")


def test_multiple_order_is_ignored():
    assert is_answer_correct("多选题", "ABD", "D,B,A")
    assert normalize_answer("多选题", "A,B,D") == "ABD"


def test_judge_variants():
    assert normalize_judge_answer("True") == "正确"
    assert normalize_judge_answer("×") == "错误"
    assert is_answer_correct("判断题", "正确", "对")


def test_blank_ignore_case_and_spaces():
    assert is_answer_correct("填空题", "html|htm", " HTML ")
    assert is_answer_correct("填空题", "html|htm", "htm")
    assert not is_answer_correct("填空题", "html", "css")
