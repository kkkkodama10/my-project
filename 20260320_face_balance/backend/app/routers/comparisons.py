from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.comparison import ComparisonListItem
from app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/api", tags=["comparisons"])
_service = ComparisonService()


@router.get("/comparisons", response_model=list[ComparisonListItem])
async def list_comparisons(
    db: AsyncSession = Depends(get_db),
) -> list[ComparisonListItem]:
    return await _service.list_all(db)
