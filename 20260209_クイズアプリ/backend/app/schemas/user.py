from __future__ import annotations

from pydantic import BaseModel


# ── Request ────────────────────────────────────────────


class RegisterRequest(BaseModel):
    display_name_base: str = "guest"


# ── Response ───────────────────────────────────────────


class UserInfo(BaseModel):
    user_id: str
    event_id: str
    session_id: str | None = None
    display_name: str
    display_suffix: str
    joined_at: str


class UserBrief(BaseModel):
    user_id: str
    display_name: str


class RegisterResponse(BaseModel):
    user: UserBrief
