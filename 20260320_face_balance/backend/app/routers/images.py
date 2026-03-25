import io

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.image import ImageListResponse, ImageUploadResponse
from app.services.analysis.pipeline import analysis_pipeline, landmark_detector
from app.services.analysis.visualizer import draw_landmarks
from app.services.image_service import ImageService
from app.storage.minio_client import get_storage_client

router = APIRouter(tags=["images"])
_service = ImageService()


@router.post(
    "/api/persons/{person_id}/images",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_image(
    person_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ImageUploadResponse:
    image = await _service.upload(db, person_id, file)
    background_tasks.add_task(analysis_pipeline.process, image.id)
    return ImageUploadResponse.model_validate(image)


@router.get(
    "/api/persons/{person_id}/images",
    response_model=list[ImageListResponse],
)
async def list_images(
    person_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ImageListResponse]:
    images = await _service.list_by_person(db, person_id)
    return [ImageListResponse.model_validate(img) for img in images]


@router.delete(
    "/api/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_image(
    image_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await _service.delete(db, image_id)


@router.get("/api/images/{image_id}/thumbnail")
async def get_thumbnail(
    image_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """MinIO からサムネイルを取得してストリーミング返却する。"""
    image = await _service.get(db, image_id)
    if not image.thumbnail_path:
        raise HTTPException(status_code=404, detail="サムネイルが存在しません")
    storage = get_storage_client()
    data = storage.download(image.thumbnail_path)
    return StreamingResponse(io.BytesIO(data), media_type="image/jpeg")


@router.get("/api/images/{image_id}/landmarks")
async def get_landmarks(
    image_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """元画像に MediaPipe ランドマーク点と顔BBoxを重ねた JPEG を返す。"""
    image = await _service.get(db, image_id)
    storage = get_storage_client()
    image_bytes = storage.download(image.storage_path)
    landmark_result = landmark_detector.detect(image_bytes)
    annotated = draw_landmarks(image_bytes, landmark_result)
    return StreamingResponse(io.BytesIO(annotated), media_type="image/jpeg")
