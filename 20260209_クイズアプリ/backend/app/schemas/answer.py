from __future__ import annotations

from pydantic import BaseModel


# ── Request ────────────────────────────────────────────


class AnswerRequest(BaseModel):
    choice_index: int


# ── Response ───────────────────────────────────────────


class AnswerInfo(BaseModel):
    choice_index: int
    delivered_at: str
    submitted_at: str
    accepted: bool
    reject_reason: str | None = None
    is_correct: bool | None = None
    response_time_sec_1dp: float | None = None


class AnswerResponse(BaseModel):
    result: str  # "accepted" | "rejected"
    answer: AnswerInfo
