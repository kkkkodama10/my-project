"""回答提出のビジネスロジック。

締切判定・回答時間計測・二重提出チェックを行う。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.models.answer import Answer
from app.schemas.answer import AnswerInfo, AnswerResponse
from app.store.base import BaseAnswerStore, BaseEventStore, BaseQuestionStore, BaseUserStore
from app.ws.manager import ConnectionManager


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(t: datetime) -> str:
    return t.isoformat()


class AnswerService:
    def __init__(
        self,
        answer_store: BaseAnswerStore,
        event_store: BaseEventStore,
        question_store: BaseQuestionStore,
        user_store: BaseUserStore,
        ws_manager: ConnectionManager,
    ) -> None:
        self.answer_store = answer_store
        self.event_store = event_store
        self.question_store = question_store
        self.user_store = user_store
        self.ws_manager = ws_manager

    async def submit(
        self,
        event_id: str,
        question_id: str,
        session_id: str,
        choice_index: int,
    ) -> AnswerResponse:
        # セッション・ユーザ確認
        session = await self.user_store.get_session(session_id)
        if not session or session.event_id != event_id:
            raise HTTPException(status_code=401, detail="no session")
        if not session.user_id:
            raise HTTPException(status_code=400, detail="not registered")

        user_id = session.user_id

        # イベント・問題確認
        event = await self.event_store.get(event_id)
        if not event or event.current_question_id != question_id:
            raise HTTPException(status_code=400, detail="question not active")

        # 二重提出チェック
        existing = await self.answer_store.get(event_id, question_id, user_id)
        if existing:
            raise HTTPException(status_code=409, detail="already answered")

        submitted_at = _now_utc()

        # delivered_at: WS 送信時刻 or 回答時刻
        delivered_str = self.ws_manager.get_delivered_at(event_id, session_id)
        if not delivered_str:
            delivered_str = _iso(submitted_at)

        # 締切判定
        accepted = True
        reason = None
        if event.current_deadline_at:
            try:
                deadline = datetime.fromisoformat(event.current_deadline_at)
                if submitted_at > deadline + timedelta(seconds=2):
                    accepted = False
                    reason = "deadline_passed"
            except (ValueError, TypeError):
                pass

        # 回答時間計測
        rt_1dp = None
        try:
            delivered_dt = datetime.fromisoformat(delivered_str)
            rt = (submitted_at - delivered_dt).total_seconds()
            rt_1dp = round(rt, 1)
        except (ValueError, TypeError):
            pass

        # 正解判定
        is_correct = None
        if accepted:
            question = await self.question_store.get(question_id)
            if question:
                is_correct = choice_index == question.correct_choice_index

        answer = Answer(
            id=uuid.uuid4().hex,
            event_id=event_id,
            question_id=question_id,
            user_id=user_id,
            choice_index=choice_index,
            delivered_at=delivered_str,
            submitted_at=_iso(submitted_at),
            accepted=accepted,
            reject_reason=reason,
            is_correct=is_correct,
            response_time_sec_1dp=rt_1dp,
        )
        await self.answer_store.create(answer)

        info = AnswerInfo(
            choice_index=answer.choice_index,
            delivered_at=answer.delivered_at,
            submitted_at=answer.submitted_at,
            accepted=answer.accepted,
            reject_reason=answer.reject_reason,
            is_correct=answer.is_correct,
            response_time_sec_1dp=answer.response_time_sec_1dp,
        )

        return AnswerResponse(
            result="accepted" if accepted else "rejected",
            answer=info,
        )
