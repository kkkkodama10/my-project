from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
from app.models.person import Person


class PersonService:
    async def create(self, db: AsyncSession, name: str) -> Person:
        person = Person(name=name)
        db.add(person)
        await db.commit()
        await db.refresh(person)
        return person

    async def list_all(self, db: AsyncSession) -> list[tuple[Person, int]]:
        # image_count をサブクエリで効率的に取得
        image_count_subq = (
            select(Image.person_id, func.count(Image.id).label("image_count"))
            .group_by(Image.person_id)
            .subquery()
        )
        stmt = (
            select(Person, func.coalesce(image_count_subq.c.image_count, 0).label("image_count"))
            .outerjoin(image_count_subq, Person.id == image_count_subq.c.person_id)
            .order_by(Person.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.all()

    async def get(self, db: AsyncSession, person_id: str) -> Person:
        person = await db.get(Person, person_id)
        if person is None:
            raise HTTPException(status_code=404, detail="人物が見つかりません")
        return person

    async def get_with_count(self, db: AsyncSession, person_id: str) -> tuple[Person, int]:
        image_count_subq = (
            select(Image.person_id, func.count(Image.id).label("image_count"))
            .group_by(Image.person_id)
            .subquery()
        )
        stmt = (
            select(Person, func.coalesce(image_count_subq.c.image_count, 0).label("image_count"))
            .outerjoin(image_count_subq, Person.id == image_count_subq.c.person_id)
            .where(Person.id == person_id)
        )
        result = await db.execute(stmt)
        row = result.first()
        if row is None:
            raise HTTPException(status_code=404, detail="人物が見つかりません")
        return row

    async def delete(self, db: AsyncSession, person_id: str) -> None:
        person = await self.get(db, person_id)
        await db.delete(person)
        await db.commit()
