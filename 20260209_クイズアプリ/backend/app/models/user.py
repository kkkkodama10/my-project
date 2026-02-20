from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventSession(Base):
    __tablename__ = "event_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"))
    user_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[str]


class EventUser(Base):
    __tablename__ = "event_users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"))
    session_id: Mapped[str | None] = mapped_column(default=None)
    display_name: Mapped[str]
    display_suffix: Mapped[str]
    joined_at: Mapped[str]

    __table_args__ = (
        UniqueConstraint("event_id", "display_suffix"),
    )
