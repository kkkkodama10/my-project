"""イベント進行のビジネスロジック。

管理者操作 (start / next / close / reveal / finish / abort) と
ユーザ向け状態取得 (get_user_state) を提供する。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

import uuid

from app.models.event import Event
from app.schemas.answer import AnswerInfo
from app.schemas.event import (
    CloseResponse,
    EventBrief,
    EventCreateRequest,
    EventStateInfo,
    FinishResponse,
    MeStateResponse,
    NextResponse,
    RevealResponse,
    StartResponse,
)
from app.schemas.question import ChoiceResponse, QuestionPublic
from app.schemas.user import UserInfo
from app.store.base import BaseAnswerStore, BaseEventStore, BaseQuestionStore, BaseUserStore
from app.ws.manager import ConnectionManager


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(t: datetime) -> str:
    return t.isoformat()


class EventService:
    def __init__(
        self,
        event_store: BaseEventStore,
        question_store: BaseQuestionStore,
        user_store: BaseUserStore,
        answer_store: BaseAnswerStore,
        ws_manager: ConnectionManager,
    ) -> None:
        self.event_store = event_store
        self.question_store = question_store
        self.user_store = user_store
        self.answer_store = answer_store
        self.ws_manager = ws_manager

    # ── helpers ────────────────────────────────────────

    async def _get_event_or_404(self, event_id: str):
        event = await self.event_store.get(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="event not found")
        return event

    def _question_to_public(self, q, *, include_answer: bool = False) -> QuestionPublic:
        return QuestionPublic(
            question_id=q.id,
            question_text=q.question_text,
            question_image=q.question_image_path,
            choices=[
                ChoiceResponse(
                    choice_index=c.choice_index,
                    text=c.text,
                    image=c.image_path,
                )
                for c in q.choices
            ],
            correct_choice_index=q.correct_choice_index if include_answer else None,
        )

    # ── 管理者操作 ─────────────────────────────────────

    async def start(self, event_id: str) -> StartResponse:
        event = await self._get_event_or_404(event_id)
        if event.state != "waiting":
            raise HTTPException(status_code=400, detail="event not in waiting state")

        now = _iso(_now_utc())
        await self.event_store.update(
            event_id,
            state="running",
            current_index=-1,
            started_at=now,
        )

        await self.ws_manager.broadcast(event_id, {
            "type": "event.state_changed",
            "data": {"state": "running", "server_time": now},
        })

        return StartResponse(status="ok", state="running")

    async def next_question(self, event_id: str) -> NextResponse:
        event = await self._get_event_or_404(event_id)
        qids = await self.event_store.get_question_ids(event_id)

        next_index = event.current_index + 1

        # 全問終了 → finish
        if next_index >= len(qids):
            return await self._finish_event(event_id)

        question_id = qids[next_index]
        question = await self.question_store.get(question_id)
        if not question:
            raise HTTPException(status_code=500, detail="question not found")

        now = _now_utc()
        deadline = now + timedelta(seconds=event.time_limit_sec)

        await self.event_store.update(
            event_id,
            state="running",
            current_question_id=question_id,
            current_index=next_index,
            current_shown_at=_iso(now),
            current_deadline_at=_iso(deadline),
            revealed=False,
            closed=False,
        )

        q_public = self._question_to_public(question, include_answer=False)
        payload = {
            "type": "question.shown",
            "data": {
                "question_id": question_id,
                "question": q_public.model_dump(),
                "started_at": _iso(now),
                "deadline_at": _iso(deadline),
            },
        }
        await self.ws_manager.broadcast_question(event_id, payload)

        return NextResponse(
            status="ok",
            question_id=question_id,
            started_at=_iso(now),
            deadline_at=_iso(deadline),
        )

    async def close_question(self, event_id: str, question_id: str) -> CloseResponse:
        event = await self._get_event_or_404(event_id)
        if event.current_question_id != question_id:
            raise HTTPException(status_code=400, detail="question not active")

        now = _iso(_now_utc())
        await self.event_store.update(
            event_id,
            current_deadline_at=now,
            closed=True,
        )

        await self.ws_manager.broadcast(event_id, {
            "type": "question.closed",
            "data": {"question_id": question_id, "closed_at": now},
        })

        return CloseResponse(status="ok", closed_at=now)

    async def reveal_answer(self, event_id: str, question_id: str) -> RevealResponse:
        event = await self._get_event_or_404(event_id)
        if event.current_question_id != question_id:
            raise HTTPException(status_code=400, detail="question not active")

        question = await self.question_store.get(question_id)
        correct = question.correct_choice_index if question else 0

        await self.event_store.update(event_id, revealed=True)

        await self.ws_manager.broadcast(event_id, {
            "type": "question.revealed",
            "data": {
                "question_id": question_id,
                "correct_choice_index": correct,
            },
        })

        return RevealResponse(
            status="ok",
            revealed_at=_iso(_now_utc()),
            correct_choice_index=correct,
        )

    async def finish(self, event_id: str) -> FinishResponse:
        return await self._finish_event(event_id)

    async def reset(self, event_id: str) -> StartResponse:
        """イベントを waiting 状態にリセットし、回答・参加者データを全削除する。"""
        await self._get_event_or_404(event_id)

        # フルリセット: 回答 → ユーザ/セッション の順に削除
        await self.answer_store.delete_by_event(event_id)
        await self.user_store.delete_by_event(event_id)

        await self.event_store.update(
            event_id,
            state="waiting",
            current_index=-1,
            current_question_id=None,
            current_shown_at=None,
            current_deadline_at=None,
            revealed=False,
            closed=False,
            started_at=None,
            finished_at=None,
        )

        await self.ws_manager.broadcast(event_id, {
            "type": "event.state_changed",
            "data": {"state": "waiting"},
        })

        return StartResponse(status="ok", state="waiting")

    async def create_event(self, req: EventCreateRequest) -> EventBrief:
        now = _iso(_now_utc())
        event_id = uuid.uuid4().hex[:12]
        join_code = req.join_code or uuid.uuid4().hex[:6]

        event = Event(
            id=event_id,
            title=req.title,
            join_code=join_code,
            time_limit_sec=req.time_limit_sec,
            state="waiting",
            created_at=now,
        )
        await self.event_store.create(event)

        if req.question_ids:
            await self.event_store.set_event_questions(event_id, req.question_ids)

        return EventBrief(event_id=event_id, title=req.title, state="waiting")

    async def update_join_code(self, event_id: str, join_code: str) -> EventBrief:
        event = await self._get_event_or_404(event_id)
        await self.event_store.update(event_id, join_code=join_code)
        return EventBrief(event_id=event_id, title=event.title, state=event.state)

    async def abort(self, event_id: str) -> FinishResponse:
        """Phase 2: 途中終了。"""
        await self._get_event_or_404(event_id)
        now = _iso(_now_utc())
        await self.event_store.update(
            event_id,
            state="aborted",
            finished_at=now,
        )
        await self.ws_manager.broadcast(event_id, {
            "type": "event.finished",
            "data": {"event_id": event_id},
        })
        return FinishResponse(status="ok", state="aborted")

    async def _finish_event(self, event_id: str) -> NextResponse | FinishResponse:
        now = _iso(_now_utc())
        await self.event_store.update(
            event_id,
            state="finished",
            finished_at=now,
        )
        await self.ws_manager.broadcast(event_id, {
            "type": "event.finished",
            "data": {"event_id": event_id},
        })
        return FinishResponse(status="ok", state="finished")

    # ── ユーザ向け状態取得 ─────────────────────────────

    async def get_user_state(
        self,
        event_id: str,
        session_id: str,
    ) -> MeStateResponse:
        event = await self._get_event_or_404(event_id)
        session = await self.user_store.get_session(session_id)
        if not session or session.event_id != event_id:
            raise HTTPException(status_code=401, detail="no session")

        # me
        me = None
        user = None
        if session.user_id:
            user = await self.user_store.get_user(session.user_id)
            if user:
                me = UserInfo(
                    user_id=user.id,
                    event_id=user.event_id,
                    session_id=user.session_id,
                    display_name=user.display_name,
                    display_suffix=user.display_suffix,
                    joined_at=user.joined_at,
                )

        # current_question
        current_question = None
        if event.current_question_id:
            q = await self.question_store.get(event.current_question_id)
            if q:
                current_question = self._question_to_public(
                    q,
                    include_answer=event.revealed,
                )

        # my_answer
        my_answer = None
        if user and event.current_question_id:
            ans = await self.answer_store.get(
                event_id,
                event.current_question_id,
                user.id,
            )
            if ans:
                my_answer = AnswerInfo(
                    choice_index=ans.choice_index,
                    delivered_at=ans.delivered_at,
                    submitted_at=ans.submitted_at,
                    accepted=ans.accepted,
                    reject_reason=ans.reject_reason,
                    is_correct=ans.is_correct if event.revealed else None,
                    response_time_sec_1dp=ans.response_time_sec_1dp,
                )

        return MeStateResponse(
            event=EventStateInfo(
                state=event.state,
                server_time=_iso(_now_utc()),
                current_question_id=event.current_question_id,
                question_started_at=event.current_shown_at,
                answer_deadline_at=event.current_deadline_at,
            ),
            me=me,
            current_question=current_question,
            my_answer=my_answer,
        )
