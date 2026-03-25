import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.person import Person


class SimilarityMethod(str, enum.Enum):
    cosine = "cosine"
    euclidean = "euclidean"
    procrustes = "procrustes"


class Comparison(Base):
    __tablename__ = "comparisons"
    __table_args__ = (
        UniqueConstraint("person_a_id", "person_b_id", "similarity_method", name="uq_comparison"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")
    )
    person_a_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    person_b_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    similarity_method: Mapped[SimilarityMethod] = mapped_column(
        Enum(SimilarityMethod, name="similarity_method"),
        nullable=False,
        server_default=text("'cosine'"),
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    person_a: Mapped["Person"] = relationship(
        "Person", foreign_keys=[person_a_id], back_populates="comparisons_as_a"
    )
    person_b: Mapped["Person"] = relationship(
        "Person", foreign_keys=[person_b_id], back_populates="comparisons_as_b"
    )
