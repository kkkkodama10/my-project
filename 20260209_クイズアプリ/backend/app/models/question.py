from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    question_text: Mapped[str]
    question_image_path: Mapped[str | None]
    correct_choice_index: Mapped[int]
    is_enabled: Mapped[bool] = mapped_column(default=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[str]
    updated_at: Mapped[str]

    choices: Mapped[list["QuestionChoice"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionChoice.choice_index",
    )


class QuestionChoice(Base):
    __tablename__ = "question_choices"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    question_id: Mapped[str] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
    )
    choice_index: Mapped[int]
    text: Mapped[str]
    image_path: Mapped[str | None]

    question: Mapped["Question"] = relationship(back_populates="choices")

    __table_args__ = (
        UniqueConstraint("question_id", "choice_index"),
    )
