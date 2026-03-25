from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.image import Image
    from app.models.person_feature import PersonFeature
    from app.models.comparison import Comparison


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    images: Mapped[list["Image"]] = relationship(
        "Image", back_populates="person", cascade="all, delete-orphan"
    )
    person_feature: Mapped["PersonFeature | None"] = relationship(
        "PersonFeature", back_populates="person", uselist=False, cascade="all, delete-orphan"
    )
    comparisons_as_a: Mapped[list["Comparison"]] = relationship(
        "Comparison",
        foreign_keys="Comparison.person_a_id",
        back_populates="person_a",
        cascade="all, delete-orphan",
    )
    comparisons_as_b: Mapped[list["Comparison"]] = relationship(
        "Comparison",
        foreign_keys="Comparison.person_b_id",
        back_populates="person_b",
        cascade="all, delete-orphan",
    )
