from __future__ import annotations

from pydantic import BaseModel


# ── Request ────────────────────────────────────────────


class AdminLoginRequest(BaseModel):
    password: str


# ── Response ───────────────────────────────────────────


class StatusResponse(BaseModel):
    status: str


class AuditLogEntry(BaseModel):
    ts: str
    action: str
    event_id: str | None = None
    payload: dict | None = None
