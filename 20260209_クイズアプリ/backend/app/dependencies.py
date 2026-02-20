"""FastAPI の Depends 用ファクトリ関数。"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.answer_service import AnswerService
from app.services.event_service import EventService
from app.services.question_service import QuestionService
from app.services.ranking_service import RankingService
from app.store.sqlite_store import (
    SQLiteAdminStore,
    SQLiteAnswerStore,
    SQLiteEventStore,
    SQLiteQuestionStore,
    SQLiteUserStore,
)
from app.ws.manager import ws_manager


# ── 低レベル: ストア ───────────────────────────────────


async def get_event_store(
    session: AsyncSession = Depends(get_session),
) -> SQLiteEventStore:
    return SQLiteEventStore(session)


async def get_question_store(
    session: AsyncSession = Depends(get_session),
) -> SQLiteQuestionStore:
    return SQLiteQuestionStore(session)


async def get_user_store(
    session: AsyncSession = Depends(get_session),
) -> SQLiteUserStore:
    return SQLiteUserStore(session)


async def get_answer_store(
    session: AsyncSession = Depends(get_session),
) -> SQLiteAnswerStore:
    return SQLiteAnswerStore(session)


async def get_admin_store(
    session: AsyncSession = Depends(get_session),
) -> SQLiteAdminStore:
    return SQLiteAdminStore(session)


# ── 高レベル: サービス ─────────────────────────────────


async def get_event_service(
    session: AsyncSession = Depends(get_session),
) -> EventService:
    return EventService(
        event_store=SQLiteEventStore(session),
        question_store=SQLiteQuestionStore(session),
        user_store=SQLiteUserStore(session),
        answer_store=SQLiteAnswerStore(session),
        ws_manager=ws_manager,
    )


async def get_question_service(
    session: AsyncSession = Depends(get_session),
) -> QuestionService:
    return QuestionService(SQLiteQuestionStore(session))


async def get_answer_service(
    session: AsyncSession = Depends(get_session),
) -> AnswerService:
    return AnswerService(
        answer_store=SQLiteAnswerStore(session),
        event_store=SQLiteEventStore(session),
        question_store=SQLiteQuestionStore(session),
        user_store=SQLiteUserStore(session),
        ws_manager=ws_manager,
    )


async def get_ranking_service(
    session: AsyncSession = Depends(get_session),
) -> RankingService:
    return RankingService(
        event_store=SQLiteEventStore(session),
        user_store=SQLiteUserStore(session),
        answer_store=SQLiteAnswerStore(session),
    )


# ── 認証ヘルパー ──────────────────────────────────────


def get_session_id(request: Request) -> str:
    """Cookie から session_id を取得。なければ 401。"""
    sid = request.cookies.get("session_id")
    if not sid:
        raise HTTPException(status_code=401, detail="no session")
    return sid
