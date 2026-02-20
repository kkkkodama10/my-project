"""起動時のシードデータ投入（冪等）。"""

import json
import uuid
from datetime import datetime, timezone

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import ADMIN_PASSWORD, QUESTIONS_SAMPLE_PATH
from app.models.admin import Admin
from app.models.event import Event, EventQuestion
from app.models.question import Question, QuestionChoice


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def seed_questions(session: AsyncSession) -> None:
    result = await session.execute(select(Question).limit(1))
    if result.scalar():
        return

    if not QUESTIONS_SAMPLE_PATH.exists():
        return

    data = json.loads(QUESTIONS_SAMPLE_PATH.read_text(encoding="utf-8"))
    now = _now_iso()

    for i, q in enumerate(data):
        question = Question(
            id=q["question_id"],
            question_text=q["question_text"],
            question_image_path=q.get("question_image"),
            correct_choice_index=q["correct_choice_index"],
            is_enabled=q.get("is_enabled", True),
            sort_order=i,
            created_at=now,
            updated_at=now,
        )
        session.add(question)

        for c in q.get("choices", []):
            choice = QuestionChoice(
                id=uuid.uuid4().hex,
                question_id=q["question_id"],
                choice_index=c["choice_index"],
                text=c["text"],
                image_path=c.get("image"),
            )
            session.add(choice)

    await session.flush()


async def seed_demo_event(session: AsyncSession) -> None:
    result = await session.execute(select(Event).where(Event.id == "demo"))
    if result.scalar():
        return

    result = await session.execute(
        select(Question.id).order_by(Question.sort_order),
    )
    question_ids = [row[0] for row in result.all()]

    event = Event(
        id="demo",
        title="Demo Event",
        join_code="123456",
        time_limit_sec=10,
        state="waiting",
        created_at=_now_iso(),
    )
    session.add(event)
    await session.flush()

    for i, qid in enumerate(question_ids):
        eq = EventQuestion(event_id="demo", question_id=qid, sort_order=i)
        session.add(eq)

    await session.flush()


async def seed_admin(session: AsyncSession) -> None:
    result = await session.execute(select(Admin).limit(1))
    if result.scalar():
        return

    pw_hash = bcrypt.hashpw(
        ADMIN_PASSWORD.encode(),
        bcrypt.gensalt(),
    ).decode()

    admin = Admin(
        id=uuid.uuid4().hex,
        password_hash=pw_hash,
        created_at=_now_iso(),
    )
    session.add(admin)
    await session.flush()


async def seed_all(session: AsyncSession) -> None:
    """全シードを実行してコミットする。"""
    await seed_questions(session)
    await seed_demo_event(session)
    await seed_admin(session)
    await session.commit()
