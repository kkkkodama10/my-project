from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.comparison import ComparisonResponse
from app.schemas.person import PersonCreate, PersonListResponse, PersonResponse
from app.services.comparison_service import ComparisonService
from app.services.person_service import PersonService

router = APIRouter(prefix="/api/persons", tags=["persons"])
_service = PersonService()
_comparison_service = ComparisonService()


@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    body: PersonCreate,
    db: AsyncSession = Depends(get_db),
) -> PersonResponse:
    person = await _service.create(db, body.name)
    return PersonResponse(
        id=person.id,
        name=person.name,
        image_count=0,  # 新規作成直後は画像なし
        created_at=person.created_at,
        updated_at=person.updated_at,
    )


@router.get("", response_model=list[PersonListResponse])
async def list_persons(
    db: AsyncSession = Depends(get_db),
) -> list[PersonListResponse]:
    rows = await _service.list_all(db)
    return [
        PersonListResponse(
            id=person.id,
            name=person.name,
            image_count=image_count,
            created_at=person.created_at,
        )
        for person, image_count in rows
    ]


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: str,
    db: AsyncSession = Depends(get_db),
) -> PersonResponse:
    person, image_count = await _service.get_with_count(db, person_id)
    return PersonResponse(
        id=person.id,
        name=person.name,
        image_count=image_count,
        created_at=person.created_at,
        updated_at=person.updated_at,
    )


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await _service.delete(db, person_id)


@router.post(
    "/{person_a_id}/compare/{person_b_id}",
    response_model=ComparisonResponse,
)
async def compare_persons(
    person_a_id: str,
    person_b_id: str,
    db: AsyncSession = Depends(get_db),
) -> ComparisonResponse:
    score, is_cached, breakdown = await _comparison_service.compare(db, person_a_id, person_b_id)
    return ComparisonResponse(score=score, is_cached=is_cached, breakdown=breakdown)
