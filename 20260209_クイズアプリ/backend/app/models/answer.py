from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"))
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("event_users.id"))
    choice_index: Mapped[int]
    delivered_at: Mapped[str]
    submitted_at: Mapped[str]
    accepted: Mapped[bool] = mapped_column(default=True)
    reject_reason: Mapped[str | None] = mapped_column(default=None)
    is_correct: Mapped[bool | None] = mapped_column(default=None)
    response_time_sec_1dp: Mapped[float | None] = mapped_column(default=None)

    __table_args__ = (
        UniqueConstraint("event_id", "question_id", "user_id"),
    )
