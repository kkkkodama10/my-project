from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Float, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.image import Image


class Feature(Base):
    __tablename__ = "features"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")
    )
    image_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    landmarks: Mapped[dict] = mapped_column(JSONB, nullable=False)
    raw_vector: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    # 15次元ハンドクラフト特徴量（二刀流機能: 解釈性補足用）
    interpretable_vector: Mapped[Optional[list[float]]] = mapped_column(
        ARRAY(Float), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    image: Mapped["Image"] = relationship("Image", back_populates="feature")
