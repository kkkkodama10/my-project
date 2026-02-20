from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    password_hash: Mapped[str]
    created_at: Mapped[str]


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    admin_id: Mapped[str | None]
    action: Mapped[str]
    event_id: Mapped[str | None]
    payload: Mapped[str | None]  # JSON string
    created_at: Mapped[str]
