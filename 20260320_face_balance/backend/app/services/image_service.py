import io
import uuid

from fastapi import HTTPException, UploadFile
from PIL import Image as PILImage
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comparison import Comparison
from app.models.image import Image, ImageStatus
from app.services.person_service import PersonService
from app.storage.minio_client import get_storage_client

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_PIL_FORMATS = {"JPEG", "PNG", "WEBP", "MPO"}
FORMAT_TO_EXT = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp", "MPO": "jpg"}
FORMAT_TO_CONTENT_TYPE = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "MPO": "image/jpeg",  # iPhone の Multi-Picture Object（JPEG 互換）
}

_person_service = PersonService()


class ImageService:
    async def upload(self, db: AsyncSession, person_id: str, file: UploadFile) -> Image:
        # 人物存在確認
        await _person_service.get(db, person_id)

        # ファイル読み込み
        data = await file.read()

        # サイズバリデーション
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="ファイルサイズは20MB以下にしてください")

        # PIL で magic bytes からフォーマットチェック
        try:
            pil_img = PILImage.open(io.BytesIO(data))
            pil_format = pil_img.format
        except Exception:
            raise HTTPException(status_code=400, detail="画像ファイルを選択してください")

        if pil_format not in ALLOWED_PIL_FORMATS:
            raise HTTPException(
                status_code=400,
                detail="JPEG / PNG / WebP 形式の画像を選択してください",
            )

        # ストレージキーを生成（Python側でUUIDを決定してパスと共用）
        image_id = str(uuid.uuid4())
        ext = FORMAT_TO_EXT[pil_format]
        storage_key = f"originals/{person_id}/{image_id}.{ext}"
        thumbnail_key = f"thumbnails/{person_id}/{image_id}.jpg"
        content_type = FORMAT_TO_CONTENT_TYPE[pil_format]

        storage = get_storage_client()

        # 元画像をアップロード
        storage.upload(storage_key, data, content_type)

        # サムネイル生成（最長辺 256px）・アップロード
        thumbnail_data = _generate_thumbnail(pil_img)
        storage.upload(thumbnail_key, thumbnail_data, "image/jpeg")

        # DB レコード作成
        image = Image(
            id=image_id,
            person_id=person_id,
            storage_path=storage_key,
            thumbnail_path=thumbnail_key,
            status=ImageStatus.uploaded,
            metadata_={},
        )
        db.add(image)
        await db.commit()
        await db.refresh(image)

        return image

    async def list_by_person(self, db: AsyncSession, person_id: str) -> list[Image]:
        stmt = (
            select(Image)
            .where(Image.person_id == person_id)
            .order_by(Image.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, image_id: str) -> Image:
        image = await db.get(Image, image_id)
        if image is None:
            raise HTTPException(status_code=404, detail="画像が見つかりません")
        return image

    async def delete(self, db: AsyncSession, image_id: str) -> None:
        image = await self.get(db, image_id)
        person_id = image.person_id

        # MinIO からファイル削除（original + thumbnail）
        storage = get_storage_client()
        storage.delete(image.storage_path)
        if image.thumbnail_path:
            storage.delete(image.thumbnail_path)

        # DB 削除 + comparisons 無効化を1トランザクションで実行
        # （ガイドライン: 途中失敗時のデータ不整合を防ぐために1トランザクション必須）
        await db.delete(image)
        await db.execute(
            update(Comparison)
            .where(
                or_(
                    Comparison.person_a_id == person_id,
                    Comparison.person_b_id == person_id,
                )
            )
            .values(is_valid=False)
        )
        await db.commit()


def _generate_thumbnail(pil_img: PILImage.Image, max_size: int = 256) -> bytes:
    """PIL Image から最長辺 max_size px の JPEG サムネイルを生成する。"""
    # コピーして元画像を保護（thumbnail() はインプレース操作のため）
    img = pil_img.copy()
    # RGBA / P（パレット）→ RGB 変換（JPEG は透過チャンネル非対応）
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((max_size, max_size))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()
