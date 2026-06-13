from __future__ import annotations

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool = False

    model_config = {"from_attributes": True}


class BankCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = ""
    description: str = ""
    is_public: bool = False


class ImportedQuestionIn(BaseModel):
    row_number: int = 0
    question_type: str
    question_text: str
    options: dict[str, str] = {}
    correct_answer: str
    analysis: str = ""
    chapter: str = ""
    difficulty: str = ""
    errors: list[str] = []
    is_valid: bool = True


class ImportConfirm(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = ""
    description: str = ""
    is_public: bool = False
    questions: list[ImportedQuestionIn]


class BankOut(BaseModel):
    id: int
    name: str
    category: str
    description: str
    question_count: int
    is_public: bool
    done_count: int = 0
    wrong_count: int = 0
    accuracy: float = 0
    progress: float = 0


class QuestionOut(BaseModel):
    id: int
    bank_id: int
    question_type: str
    question_text: str
    options: dict[str, str]
    correct_answer: str | None = None
    analysis: str | None = None
    difficulty: str = ""
    chapter_name: str = ""
    is_favorite: bool = False


class AnswerSubmit(BaseModel):
    question_id: int
    user_answer: str
    answer_duration: int = 0
    practice_mode: str = "顺序刷题"


class AnswerResult(BaseModel):
    is_correct: bool
    correct_answer: str
    analysis: str


class AdminUserOut(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: str | None = None
    last_login_at: str | None = None
    bank_count: int = 0
    question_count: int = 0
    answer_count: int = 0
    accuracy: float = 0
    wrong_count: int = 0


class AdminOverview(BaseModel):
    user_count: int
    bank_count: int
    question_count: int
    answer_count: int
    wrong_count: int
    users: list[AdminUserOut]
