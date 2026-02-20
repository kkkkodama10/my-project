"""ユーザ系 API ルーター。"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.dependencies import (
    get_answer_service,
    get_event_service,
    get_event_store,
    get_question_store,
    get_ranking_service,
    get_session_id,
    get_user_store,
)
from app.models.user import EventSession, EventUser
from app.schemas.answer import AnswerRequest
from app.schemas.event import CurrentQuestionResponse, EventBrief, JoinRequest, JoinResponse
from app.schemas.user import RegisterRequest, RegisterResponse, UserBrief
from app.services.answer_service import AnswerService
from app.services.event_service import EventService
from app.services.ranking_service import RankingService
from app.schemas.question import ChoiceResponse, QuestionPublic
from app.store.sqlite_store import SQLiteEventStore, SQLiteQuestionStore, SQLiteUserStore

router = APIRouter()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _gen_suffix(user_store: SQLiteUserStore, event_id: str) -> str:
    for _ in range(10):
        s = f"{random.randint(0, 9999):04d}"
        if not await user_store.suffix_exists(event_id, s):
            return s
    return f"{random.randint(0, 9999):04d}"


# ── 参加・登録 ─────────────────────────────────────────


@router.post("/events/{event_id}/join")
async def join_event(
    event_id: str,
    req: JoinRequest,
    response: Response,
    event_store: SQLiteEventStore = Depends(get_event_store),
    user_store: SQLiteUserStore = Depends(get_user_store),
) -> JoinResponse:
    event = await event_store.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    if req.join_code != event.join_code:
        raise HTTPException(status_code=403, detail="invalid join code")

    sid = uuid.uuid4().hex
    await user_store.create_session(
        EventSession(id=sid, event_id=event_id, created_at=_now_iso()),
    )
    response.set_cookie(key="session_id", value=sid, httponly=True)

    return JoinResponse(
        status="ok",
        event=EventBrief(
            event_id=event_id,
            title=event.title,
            state=event.state,
        ),
    )


@router.post("/events/{event_id}/users/register")
async def register_user(
    event_id: str,
    req: RegisterRequest,
    session_id: str = Depends(get_session_id),
    user_store: SQLiteUserStore = Depends(get_user_store),
    event_store: SQLiteEventStore = Depends(get_event_store),
) -> RegisterResponse:
    session = await user_store.get_session(session_id)
    if not session or session.event_id != event_id:
        raise HTTPException(status_code=401, detail="no session")

    event = await event_store.get(event_id)
    if event and event.state in ("finished", "aborted"):
        raise HTTPException(status_code=409, detail="quiz_finished")

    base = req.display_name_base or "guest"
    suffix = await _gen_suffix(user_store, event_id)
    display_name = f"{base}-{suffix}"

    uid = uuid.uuid4().hex
    user = EventUser(
        id=uid,
        event_id=event_id,
        session_id=session_id,
        display_name=display_name,
        display_suffix=suffix,
        joined_at=_now_iso(),
    )
    await user_store.create_user(user)
    await user_store.update_session(session_id, user_id=uid)

    return RegisterResponse(user=UserBrief(user_id=uid, display_name=display_name))


# ── ログアウト ─────────────────────────────────────────


@router.post("/events/{event_id}/logout")
async def logout_event(response: Response) -> dict:
    """session_id Cookie を削除してログアウト。"""
    response.delete_cookie(key="session_id")
    return {"status": "ok"}


# ── 状態取得 ───────────────────────────────────────────


@router.get("/events/{event_id}/me/state")
async def me_state(
    event_id: str,
    session_id: str = Depends(get_session_id),
    event_service: EventService = Depends(get_event_service),
):
    return await event_service.get_user_state(event_id, session_id)


# ── 回答 ──────────────────────────────────────────────


@router.post("/events/{event_id}/questions/{question_id}/answers")
async def submit_answer(
    event_id: str,
    question_id: str,
    req: AnswerRequest,
    session_id: str = Depends(get_session_id),
    answer_service: AnswerService = Depends(get_answer_service),
):
    return await answer_service.submit(
        event_id,
        question_id,
        session_id,
        req.choice_index,
    )


# ── 結果 ──────────────────────────────────────────────


@router.get("/events/{event_id}/results")
async def event_results(
    event_id: str,
    ranking_service: RankingService = Depends(get_ranking_service),
):
    return await ranking_service.calculate(event_id)


# ── ポーリングフォールバック ────────────────────────────


@router.get("/events/{event_id}/questions/current")
async def current_question(
    event_id: str,
    event_store: SQLiteEventStore = Depends(get_event_store),
    question_store: SQLiteQuestionStore = Depends(get_question_store),
) -> CurrentQuestionResponse:
    event = await event_store.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")

    if not event.current_question_id:
        return CurrentQuestionResponse(event_state=event.state)

    q = await question_store.get(event.current_question_id)
    question_public = None
    if q:
        question_public = QuestionPublic(
            question_id=q.id,
            question_text=q.question_text,
            question_image=q.question_image_path,
            choices=[
                ChoiceResponse(choice_index=c.choice_index, text=c.text, image=c.image_path)
                for c in q.choices
            ],
            correct_choice_index=q.correct_choice_index if event.revealed else None,
        )

    return CurrentQuestionResponse(
        event_state=event.state,
        question=question_public,
        started_at=event.current_shown_at,
        deadline_at=event.current_deadline_at,
    )


# ── CSV エクスポート ────────────────────────────────────


@router.get("/events/{event_id}/results/csv")
async def export_results_csv(
    event_id: str,
    ranking_service: RankingService = Depends(get_ranking_service),
) -> StreamingResponse:
    csv_text = await ranking_service.export_csv(event_id)

    def _iter():
        yield csv_text.encode("utf-8-sig")  # BOM付きで Excel 対応

    return StreamingResponse(
        _iter(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="results_{event_id}.csv"',
        },
    )
