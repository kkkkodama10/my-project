import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Enum, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.feature import Feature


class ImageStatus(str, enum.Enum):
    uploaded = "uploaded"
    validating = "validating"
    analyzing = "analyzing"
    analyzed = "analyzed"
    error = "error"


class Image(Base):
    __tablename__ = "images"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")
    )
    person_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ImageStatus] = mapped_column(
        Enum(ImageStatus, name="image_status"),
        nullable=False,
        server_default=text("'uploaded'"),
    )
    # metadata は Python 予約語に近いため metadata_ として定義し、カラム名は "metadata" を維持
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    person: Mapped["Person"] = relationship("Person", back_populates="images")
    feature: Mapped["Feature | None"] = relationship(
        "Feature", back_populates="image", uselist=False, cascade="all, delete-orphan"
    )
