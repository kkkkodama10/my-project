"""SQLite 実装のストア層。

全クラスは AsyncSession を受け取り、flush まで行う。
commit / rollback はセッションスコープ側（FastAPI Depends）で管理する。
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import Admin, AdminAuditLog
from app.models.answer import Answer
from app.models.event import Event, EventQuestion
from app.models.question import Question, QuestionChoice
from app.models.user import EventSession, EventUser
from app.store.base import (
    BaseAdminStore,
    BaseAnswerStore,
    BaseEventStore,
    BaseQuestionStore,
    BaseUserStore,
)


# ── Event ──────────────────────────────────────────────


class SQLiteEventStore(BaseEventStore):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, event_id: str) -> Event | None:
        return await self.session.get(Event, event_id)

    async def create(self, event: Event) -> Event:
        self.session.add(event)
        await self.session.flush()
        return event

    async def update(self, event_id: str, **kwargs: object) -> Event | None:
        event = await self.get(event_id)
        if not event:
            return None
        for key, value in kwargs.items():
            setattr(event, key, value)
        await self.session.flush()
        return event

    async def get_question_ids(self, event_id: str) -> list[str]:
        result = await self.session.execute(
            select(EventQuestion.question_id)
            .where(EventQuestion.event_id == event_id)
            .order_by(EventQuestion.sort_order),
        )
        return [row[0] for row in result.all()]

    async def set_event_questions(
        self,
        event_id: str,
        question_ids: list[str],
    ) -> None:
        # 既存を削除
        await self.session.execute(
            delete(EventQuestion).where(EventQuestion.event_id == event_id),
        )
        # 新規登録
        for i, qid in enumerate(question_ids):
            self.session.add(
                EventQuestion(event_id=event_id, question_id=qid, sort_order=i),
            )
        await self.session.flush()


# ── Question ───────────────────────────────────────────


class SQLiteQuestionStore(BaseQuestionStore):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, question_id: str) -> Question | None:
        result = await self.session.execute(
            select(Question)
            .options(selectinload(Question.choices))
            .where(Question.id == question_id),
        )
        return result.scalar_one_or_none()

    async def list(self, *, enabled_only: bool = False) -> list[Question]:
        stmt = (
            select(Question)
            .options(selectinload(Question.choices))
            .order_by(Question.sort_order)
        )
        if enabled_only:
            stmt = stmt.where(Question.is_enabled.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, question: Question) -> Question:
        self.session.add(question)
        await self.session.flush()
        return question

    async def update(
        self,
        question_id: str,
        **kwargs: object,
    ) -> Question | None:
        question = await self.get(question_id)
        if not question:
            return None
        for key, value in kwargs.items():
            setattr(question, key, value)
        await self.session.flush()
        return question

    async def delete(self, question_id: str) -> bool:
        question = await self.get(question_id)
        if not question:
            return False
        await self.session.delete(question)
        await self.session.flush()
        return True

    async def reorder(self, ordered_ids: list[str]) -> None:
        for i, qid in enumerate(ordered_ids):
            question = await self.session.get(Question, qid)
            if question:
                question.sort_order = i
        await self.session.flush()

    async def set_enabled(
        self,
        question_id: str,
        enabled: bool,
    ) -> Question | None:
        return await self.update(question_id, is_enabled=enabled)


# ── User / Session ─────────────────────────────────────


class SQLiteUserStore(BaseUserStore):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, es: EventSession) -> EventSession:
        self.session.add(es)
        await self.session.flush()
        return es

    async def get_session(self, session_id: str) -> EventSession | None:
        return await self.session.get(EventSession, session_id)

    async def update_session(
        self,
        session_id: str,
        **kwargs: object,
    ) -> EventSession | None:
        es = await self.get_session(session_id)
        if not es:
            return None
        for key, value in kwargs.items():
            setattr(es, key, value)
        await self.session.flush()
        return es

    async def create_user(self, user: EventUser) -> EventUser:
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_user(self, user_id: str) -> EventUser | None:
        return await self.session.get(EventUser, user_id)

    async def list_event_users(self, event_id: str) -> list[EventUser]:
        result = await self.session.execute(
            select(EventUser).where(EventUser.event_id == event_id),
        )
        return list(result.scalars().all())

    async def suffix_exists(self, event_id: str, suffix: str) -> bool:
        result = await self.session.execute(
            select(EventUser.id).where(
                EventUser.event_id == event_id,
                EventUser.display_suffix == suffix,
            ),
        )
        return result.scalar() is not None

    async def delete_by_event(self, event_id: str) -> int:
        # FK 制約順: event_users (→ event_sessions) → event_sessions
        r1 = await self.session.execute(
            delete(EventUser).where(EventUser.event_id == event_id),
        )
        r2 = await self.session.execute(
            delete(EventSession).where(EventSession.event_id == event_id),
        )
        await self.session.flush()
        return r1.rowcount + r2.rowcount


# ── Answer ─────────────────────────────────────────────


class SQLiteAnswerStore(BaseAnswerStore):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, answer: Answer) -> Answer:
        self.session.add(answer)
        await self.session.flush()
        return answer

    async def get(
        self,
        event_id: str,
        question_id: str,
        user_id: str,
    ) -> Answer | None:
        result = await self.session.execute(
            select(Answer).where(
                Answer.event_id == event_id,
                Answer.question_id == question_id,
                Answer.user_id == user_id,
            ),
        )
        return result.scalar_one_or_none()

    async def list_by_event(self, event_id: str) -> list[Answer]:
        result = await self.session.execute(
            select(Answer).where(Answer.event_id == event_id),
        )
        return list(result.scalars().all())

    async def delete_by_event(self, event_id: str) -> int:
        result = await self.session.execute(
            delete(Answer).where(Answer.event_id == event_id),
        )
        await self.session.flush()
        return result.rowcount


# ── Admin / AuditLog ──────────────────────────────────


class SQLiteAdminStore(BaseAdminStore):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_admin(self, admin_id: str) -> Admin | None:
        return await self.session.get(Admin, admin_id)

    async def get_admin_by_any(self) -> Admin | None:
        result = await self.session.execute(select(Admin).limit(1))
        return result.scalar_one_or_none()

    async def create_audit_log(self, log: AdminAuditLog) -> AdminAuditLog:
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_audit_logs(self, limit: int = 100) -> list[AdminAuditLog]:
        result = await self.session.execute(
            select(AdminAuditLog)
            .order_by(AdminAuditLog.created_at.desc())
            .limit(limit),
        )
        return list(result.scalars().all())
