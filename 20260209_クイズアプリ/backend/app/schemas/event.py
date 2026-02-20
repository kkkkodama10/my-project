from __future__ import annotations

from pydantic import BaseModel

from app.schemas.answer import AnswerInfo
from app.schemas.question import QuestionPublic
from app.schemas.user import UserInfo


# ── Request ────────────────────────────────────────────


class JoinRequest(BaseModel):
    join_code: str


class EventCreateRequest(BaseModel):
    title: str
    join_code: str | None = None
    time_limit_sec: int = 10
    question_ids: list[str] = []


class JoinCodeUpdateRequest(BaseModel):
    join_code: str


# ── Response ───────────────────────────────────────────


class EventBrief(BaseModel):
    event_id: str
    title: str
    state: str


class JoinResponse(BaseModel):
    status: str
    event: EventBrief


class EventStateInfo(BaseModel):
    state: str
    server_time: str
    current_question_id: str | None = None
    question_started_at: str | None = None
    answer_deadline_at: str | None = None


class MeStateResponse(BaseModel):
    event: EventStateInfo
    me: UserInfo | None = None
    current_question: QuestionPublic | None = None
    my_answer: AnswerInfo | None = None


class StartResponse(BaseModel):
    status: str
    state: str


class NextResponse(BaseModel):
    status: str
    question_id: str | None = None
    started_at: str | None = None
    deadline_at: str | None = None
    state: str | None = None


class CloseResponse(BaseModel):
    status: str
    closed_at: str


class RevealResponse(BaseModel):
    status: str
    revealed_at: str
    correct_choice_index: int


class FinishResponse(BaseModel):
    status: str
    state: str


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    display_name: str
    correct_count: int
    unanswered_count: int
    accuracy: float
    correct_time_sum_sec_1dp: float


class EventSummary(BaseModel):
    total_questions: int
    finished_at: str


class ResultsResponse(BaseModel):
    leaderboard: list[LeaderboardEntry]
    event_summary: EventSummary


class CurrentQuestionResponse(BaseModel):
    event_state: str
    question: QuestionPublic | None = None
    started_at: str | None = None
    deadline_at: str | None = None
