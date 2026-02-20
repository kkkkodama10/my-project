from __future__ import annotations

from pydantic import BaseModel


# ── Shared ─────────────────────────────────────────────


class ChoiceResponse(BaseModel):
    choice_index: int
    text: str
    image: str | None = None


class QuestionPublic(BaseModel):
    """ユーザ向け問題データ。correct_choice_index は reveal 時のみ付与。"""

    question_id: str
    question_text: str
    question_image: str | None = None
    choices: list[ChoiceResponse]
    correct_choice_index: int | None = None


# ── Admin Request ──────────────────────────────────────


class ChoiceInput(BaseModel):
    choice_index: int
    text: str
    image: str | None = None


class QuestionCreateRequest(BaseModel):
    question_text: str
    question_image: str | None = None
    choices: list[ChoiceInput]
    correct_choice_index: int
    is_enabled: bool = True


class QuestionUpdateRequest(BaseModel):
    question_text: str | None = None
    question_image: str | None = None
    choices: list[ChoiceInput] | None = None
    correct_choice_index: int | None = None
    is_enabled: bool | None = None


class ReorderRequest(BaseModel):
    ordered_ids: list[str]


class EnabledRequest(BaseModel):
    enabled: bool


# ── Admin Response ─────────────────────────────────────


class QuestionResponse(BaseModel):
    """管理者向け問題データ（正解含む）。"""

    question_id: str
    question_text: str
    question_image: str | None = None
    choices: list[ChoiceResponse]
    correct_choice_index: int
    is_enabled: bool
    sort_order: int
    created_at: str
    updated_at: str
