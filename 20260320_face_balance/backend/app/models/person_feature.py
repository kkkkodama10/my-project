import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, Integer, Float, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.person import Person


class AggregationMethod(str, enum.Enum):
    average = "average"
    single = "single"
    median = "median"


class PersonFeature(Base):
    __tablename__ = "person_features"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")
    )
    person_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    method: Mapped[AggregationMethod] = mapped_column(
        Enum(AggregationMethod, name="aggregation_method"),
        nullable=False,
        server_default=text("'average'"),
    )
    feature_vector: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    # 15次元ハンドクラフト特徴量の人物平均（二刀流機能: 解釈性補足用）
    interpretable_vector: Mapped[Optional[list[float]]] = mapped_column(
        ARRAY(Float), nullable=True
    )
    image_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    person: Mapped["Person"] = relationship("Person", back_populates="person_feature")
