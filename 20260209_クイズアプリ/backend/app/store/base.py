"""ストア層の抽象基底クラス（ABC）。

Phase 3 で RDS 実装に差し替える際のインターフェース定義。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.admin import Admin, AdminAuditLog
from app.models.answer import Answer
from app.models.event import Event
from app.models.question import Question
from app.models.user import EventSession, EventUser


# ── Event ──────────────────────────────────────────────


class BaseEventStore(ABC):
    @abstractmethod
    async def get(self, event_id: str) -> Event | None: ...

    @abstractmethod
    async def create(self, event: Event) -> Event: ...

    @abstractmethod
    async def update(self, event_id: str, **kwargs: object) -> Event | None: ...

    @abstractmethod
    async def get_question_ids(self, event_id: str) -> list[str]: ...

    @abstractmethod
    async def set_event_questions(
        self,
        event_id: str,
        question_ids: list[str],
    ) -> None: ...


# ── Question ───────────────────────────────────────────


class BaseQuestionStore(ABC):
    @abstractmethod
    async def get(self, question_id: str) -> Question | None: ...

    @abstractmethod
    async def list(self, *, enabled_only: bool = False) -> list[Question]: ...

    @abstractmethod
    async def create(self, question: Question) -> Question: ...

    @abstractmethod
    async def update(
        self,
        question_id: str,
        **kwargs: object,
    ) -> Question | None: ...

    @abstractmethod
    async def delete(self, question_id: str) -> bool: ...

    @abstractmethod
    async def reorder(self, ordered_ids: list[str]) -> None: ...

    @abstractmethod
    async def set_enabled(
        self,
        question_id: str,
        enabled: bool,
    ) -> Question | None: ...


# ── User / Session ─────────────────────────────────────


class BaseUserStore(ABC):
    @abstractmethod
    async def create_session(self, session: EventSession) -> EventSession: ...

    @abstractmethod
    async def get_session(self, session_id: str) -> EventSession | None: ...

    @abstractmethod
    async def update_session(
        self,
        session_id: str,
        **kwargs: object,
    ) -> EventSession | None: ...

    @abstractmethod
    async def create_user(self, user: EventUser) -> EventUser: ...

    @abstractmethod
    async def get_user(self, user_id: str) -> EventUser | None: ...

    @abstractmethod
    async def list_event_users(self, event_id: str) -> list[EventUser]: ...

    @abstractmethod
    async def suffix_exists(self, event_id: str, suffix: str) -> bool: ...

    @abstractmethod
    async def delete_by_event(self, event_id: str) -> int:
        """event_users と event_sessions を event_id で一括削除し、削除件数を返す。"""
        ...


# ── Answer ─────────────────────────────────────────────


class BaseAnswerStore(ABC):
    @abstractmethod
    async def create(self, answer: Answer) -> Answer: ...

    @abstractmethod
    async def get(
        self,
        event_id: str,
        question_id: str,
        user_id: str,
    ) -> Answer | None: ...

    @abstractmethod
    async def list_by_event(self, event_id: str) -> list[Answer]: ...

    @abstractmethod
    async def delete_by_event(self, event_id: str) -> int:
        """answers を event_id で一括削除し、削除件数を返す。"""
        ...


# ── Admin / AuditLog ──────────────────────────────────


class BaseAdminStore(ABC):
    @abstractmethod
    async def get_admin(self, admin_id: str) -> Admin | None: ...

    @abstractmethod
    async def get_admin_by_any(self) -> Admin | None:
        """最初の管理者を返す（Phase 2: 管理者は1人想定）。"""
        ...

    @abstractmethod
    async def create_audit_log(self, log: AdminAuditLog) -> AdminAuditLog: ...

    @abstractmethod
    async def list_audit_logs(self, limit: int = 100) -> list[AdminAuditLog]: ...
