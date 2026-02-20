from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str]
    join_code: Mapped[str]
    time_limit_sec: Mapped[int] = mapped_column(default=10)
    state: Mapped[str] = mapped_column(default="waiting")
    current_question_id: Mapped[str | None] = mapped_column(
        ForeignKey("questions.id"),
        default=None,
    )
    current_index: Mapped[int] = mapped_column(default=-1)
    current_shown_at: Mapped[str | None] = mapped_column(default=None)
    current_deadline_at: Mapped[str | None] = mapped_column(default=None)
    revealed: Mapped[bool] = mapped_column(default=False)
    closed: Mapped[bool] = mapped_column(default=False)
    started_at: Mapped[str | None] = mapped_column(default=None)
    finished_at: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[str]

    event_questions: Mapped[list["EventQuestion"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventQuestion.sort_order",
    )


class EventQuestion(Base):
    __tablename__ = "event_questions"

    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    question_id: Mapped[str] = mapped_column(
        ForeignKey("questions.id"),
        primary_key=True,
    )
    sort_order: Mapped[int]

    event: Mapped["Event"] = relationship(back_populates="event_questions")
