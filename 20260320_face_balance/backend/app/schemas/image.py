from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.image import ImageStatus


class ImageUploadResponse(BaseModel):
    """POST /api/persons/{id}/images のレスポンス（storage_path は内部情報のため除外）"""

    id: str
    person_id: str
    status: ImageStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageListResponse(BaseModel):
    id: str
    person_id: str
    status: ImageStatus
    thumbnail_path: str | None  # MinIO キーから /api/images/{id}/thumbnail に変換される
    created_at: datetime
    metadata_: dict | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def compute_thumbnail_url(self) -> "ImageListResponse":
        """thumbnail_path を MinIO 内部キーから API URL に変換する。"""
        if self.thumbnail_path is not None:
            self.thumbnail_path = f"/api/images/{self.id}/thumbnail"
        return self
