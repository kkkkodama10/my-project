"""管理者系 API ルーター。"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone

import bcrypt
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from app.dependencies import (
    get_admin_store,
    get_event_service,
    get_question_service,
)
from app.models.admin import AdminAuditLog
from app.config import UPLOADS_DIR, REDIS_URL
from app.schemas.admin import AdminLoginRequest, AuditLogEntry, StatusResponse
from app.schemas.event import EventCreateRequest, JoinCodeUpdateRequest
from app.schemas.question import (
    EnabledRequest,
    QuestionCreateRequest,
    QuestionResponse,
    QuestionUpdateRequest,
    ReorderRequest,
)
from app.services.event_service import EventService
from app.services.question_service import QuestionService
from app.store.sqlite_store import SQLiteAdminStore

router = APIRouter(prefix="/admin")


# ── admin session（Valkey または インメモリ fallback） ────────────────────────

# ローカル環境用 fallback（REDIS_URL がない場合）
_admin_sessions: dict[str, str] = {}
_redis: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis | None:
    """Redis接続を取得（Valkey URL がある場合のみ）。"""
    global _redis
    if not REDIS_URL:
        logger.warning("[admin.py] REDIS_URL not set, using in-memory fallback")
        return None
    if _redis is None:
        try:
            logger.info(f"[admin.py] Connecting to Valkey: {REDIS_URL}")
            _redis = await aioredis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("[admin.py] Valkey connection successful")
        except Exception as e:
            logger.error(f"[admin.py] Valkey connection failed: {type(e).__name__}: {e}", exc_info=True)
            return None
    return _redis


async def _get_admin_session(token: str) -> str | None:
    """admin_session を Valkey または メモリから取得。"""
    redis = await _get_redis()
    if redis:
        # Valkey から取得
        key = f"admin_session:{token}"
        result = await redis.get(key)
        logger.debug(f"[admin.py] Got session from Valkey: token={token[:8]}..., found={result is not None}")
        return result
    else:
        # メモリから取得（ローカル）
        result = _admin_sessions.get(token)
        logger.debug(f"[admin.py] Got session from memory: token={token[:8]}..., found={result is not None}")
        return result


async def _set_admin_session(token: str, timestamp: str) -> None:
    """admin_session を Valkey または メモリに保存。"""
    redis = await _get_redis()
    if redis:
        # Valkey に保存（24時間 TTL）
        key = f"admin_session:{token}"
        await redis.set(key, timestamp, ex=86400)
        logger.info(f"[admin.py] Saved session to Valkey: token={token[:8]}...")
    else:
        # メモリに保存（ローカル）
        _admin_sessions[token] = timestamp
        logger.warning(f"[admin.py] SAVED SESSION TO IN-MEMORY (Valkey not available): token={token[:8]}...")


async def _delete_admin_session(token: str) -> None:
    """admin_session を Valkey または メモリから削除。"""
    redis = await _get_redis()
    if redis:
        # Valkey から削除
        key = f"admin_session:{token}"
        await redis.delete(key)
    else:
        # メモリから削除（ローカル）
        if token in _admin_sessions:
            del _admin_sessions[token]

# ── ログイン失敗ロック ──────────────────────────────────

_LOCK_THRESHOLD = 5
_LOCK_DURATION_SEC = 15 * 60  # 15分
_failed_attempts: list[float] = []  # unix timestamps


def _check_login_lockout() -> None:
    now = time.time()
    cutoff = now - _LOCK_DURATION_SEC
    _failed_attempts[:] = [t for t in _failed_attempts if t > cutoff]
    if len(_failed_attempts) >= _LOCK_THRESHOLD:
        earliest = min(_failed_attempts)
        remaining = int(earliest + _LOCK_DURATION_SEC - now)
        raise HTTPException(
            status_code=429,
            detail=f"too many failed attempts, retry after {remaining}s",
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def require_admin(request: Request) -> None:
    token = request.cookies.get("admin_session")
    if not token:
        raise HTTPException(status_code=401, detail="admin auth required")

    # Valkey またはメモリから確認
    session_data = await _get_admin_session(token)
    if not session_data:
        raise HTTPException(status_code=401, detail="admin auth required")


async def _log(
    admin_store: SQLiteAdminStore,
    action: str,
    event_id: str | None = None,
    payload: dict | None = None,
) -> None:
    await admin_store.create_audit_log(
        AdminAuditLog(
            id=uuid.uuid4().hex,
            action=action,
            event_id=event_id,
            payload=json.dumps(payload, ensure_ascii=False) if payload else None,
            created_at=_now_iso(),
        ),
    )


# ── ログイン ───────────────────────────────────────────


@router.post("/login")
async def admin_login(
    req: AdminLoginRequest,
    response: Response,
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
) -> StatusResponse:
    _check_login_lockout()

    admin = await admin_store.get_admin_by_any()
    ok = admin and bcrypt.checkpw(req.password.encode(), admin.password_hash.encode())
    if not ok:
        _failed_attempts.append(time.time())
        raise HTTPException(status_code=401, detail="invalid password")

    _failed_attempts.clear()
    token = uuid.uuid4().hex
    timestamp = _now_iso()
    await _set_admin_session(token, timestamp)
    response.set_cookie(key="admin_session", value=token, httponly=True, samesite="lax")
    return StatusResponse(status="ok")


# ── セッション確認 ─────────────────────────────────────


@router.get("/verify")
async def admin_verify(_: None = Depends(require_admin)) -> StatusResponse:
    """Cookie が有効な管理者セッションを持っているか確認。"""
    return StatusResponse(status="ok")


# ── イベント進行 ───────────────────────────────────────


@router.post("/events")
async def admin_create_event(
    req: EventCreateRequest,
    _: None = Depends(require_admin),
    event_service: EventService = Depends(get_event_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
):
    result = await event_service.create_event(req)
    await _log(admin_store, "create_event", result.event_id, {"title": req.title})
    return result


@router.put("/events/{event_id}/join-code")
async def admin_update_join_code(
    event_id: str,
    req: JoinCodeUpdateRequest,
    _: None = Depends(require_admin),
    event_service: EventService = Depends(get_event_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
):
    result = await event_service.update_join_code(event_id, req.join_code)
    await _log(admin_store, "update_join_code", event_id, {"join_code": req.join_code})
    return result


@router.post("/events/{event_id}/start")
async def admin_start(
    event_id: str,
    _: None = Depends(require_admin),
    event_service: EventService = Depends(get_event_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
):
    result = await event_service.start(event_id)
    await _log(admin_store, "start", event_id, {"state": result.state})
    return result


@router.post("/events/{event_id}/questions/next")
async def admin_next(
    event_id: str,
    _: None = Depends(require_admin),
    event_service: EventService = Depends(get_event_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
):
    result = await event_service.next_question(event_id)
    payload = {"state": result.state} if result.state else {"question_id": result.question_id}
    await _log(admin_store, "next", event_id, payload)
    return result


@router.post("/events/{event_id}/questions/{question_id}/close")
async def admin_close(
    event_id: str,
    question_id: str,
    _: None = Depends(require_admin),
    event_service: EventService = Depends(get_event_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
):
    result = await event_service.close_question(event_id, question_id)
    await _log(admin_store, "close", event_id, {"question_id": question_id})
    return result


@router.post("/events/{event_id}/questions/{question_id}/reveal")
async def admin_reveal(
    event_id: str,
    question_id: str,
    _: None = Depends(require_admin),
    event_service: EventService = Depends(get_event_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
):
    result = await event_service.reveal_answer(event_id, question_id)
    await _log(
        admin_store,
        "reveal",
        event_id,
        {"question_id": question_id, "correct_choice_index": result.correct_choice_index},
    )
    return result


@router.post("/events/{event_id}/finish")
async def admin_finish(
    event_id: str,
    _: None = Depends(require_admin),
    event_service: EventService = Depends(get_event_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
):
    result = await event_service.finish(event_id)
    await _log(admin_store, "finish", event_id, {"state": result.state})
    return result


@router.post("/events/{event_id}/reset")
async def admin_reset(
    event_id: str,
    _: None = Depends(require_admin),
    event_service: EventService = Depends(get_event_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
):
    result = await event_service.reset(event_id)
    await _log(admin_store, "reset", event_id, {"state": result.state})
    return result


@router.post("/events/{event_id}/abort")
async def admin_abort(
    event_id: str,
    _: None = Depends(require_admin),
    event_service: EventService = Depends(get_event_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
):
    result = await event_service.abort(event_id)
    await _log(admin_store, "abort", event_id, {"state": result.state})
    return result


# ── 問題管理 CRUD ─────────────────────────────────────


@router.get("/questions")
async def admin_list_questions(
    enabled_only: bool = False,
    _: None = Depends(require_admin),
    question_service: QuestionService = Depends(get_question_service),
) -> list[QuestionResponse]:
    return await question_service.list_all(enabled_only=enabled_only)


@router.post("/questions")
async def admin_create_question(
    req: QuestionCreateRequest,
    _: None = Depends(require_admin),
    question_service: QuestionService = Depends(get_question_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
) -> QuestionResponse:
    result = await question_service.create(req)
    await _log(admin_store, "create_question", None, {"question_id": result.question_id})
    return result


@router.put("/questions/reorder")
async def admin_reorder_questions(
    req: ReorderRequest,
    _: None = Depends(require_admin),
    question_service: QuestionService = Depends(get_question_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
) -> StatusResponse:
    await question_service.reorder(req.ordered_ids)
    await _log(admin_store, "reorder_questions", None, None)
    return StatusResponse(status="ok")


@router.put("/questions/{question_id}/enabled")
async def admin_set_question_enabled(
    question_id: str,
    req: EnabledRequest,
    _: None = Depends(require_admin),
    question_service: QuestionService = Depends(get_question_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
) -> QuestionResponse:
    result = await question_service.set_enabled(question_id, req.enabled)
    await _log(admin_store, "set_question_enabled", None, {"question_id": question_id, "enabled": req.enabled})
    return result


@router.put("/questions/{question_id}")
async def admin_update_question(
    question_id: str,
    req: QuestionUpdateRequest,
    _: None = Depends(require_admin),
    question_service: QuestionService = Depends(get_question_service),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
) -> QuestionResponse:
    result = await question_service.update(question_id, req)
    await _log(admin_store, "update_question", None, {"question_id": question_id})
    return result


# ── ログ閲覧 ───────────────────────────────────────────


@router.get("/logs")
async def admin_logs(
    limit: int = 100,
    _: None = Depends(require_admin),
    admin_store: SQLiteAdminStore = Depends(get_admin_store),
) -> list[AuditLogEntry]:
    logs = await admin_store.list_audit_logs(limit)
    return [
        AuditLogEntry(
            ts=log.created_at,
            action=log.action,
            event_id=log.event_id,
            payload=json.loads(log.payload) if log.payload else None,
        )
        for log in logs
    ]


# ── 画像アップロード ────────────────────────────────────

_ALLOWED_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
_ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


@router.post("/assets/images")
async def admin_upload_image(
    file: UploadFile,
    _: None = Depends(require_admin),
) -> JSONResponse:
    import mimetypes
    from pathlib import Path

    content_type = file.content_type or ""
    ext = Path(file.filename or "").suffix.lower()

    if content_type not in _ALLOWED_TYPES and ext not in _ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail="unsupported file type")

    # 拡張子を確定（content_type 優先）
    if not ext or ext not in _ALLOWED_EXTS:
        ext = mimetypes.guess_extension(content_type) or ".bin"

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOADS_DIR / filename
    content = await file.read()
    dest.write_bytes(content)

    return JSONResponse({"url": f"/uploads/{filename}", "filename": filename})
