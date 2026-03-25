import logging

from sqlalchemy import or_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.comparison import Comparison
from app.models.feature import Feature
from app.models.image import Image, ImageStatus
from app.services.analysis.detectors.mediapipe_detector import MediaPipeLandmarkDetector
from app.services.analysis.extractors.dlib_face_rec import DlibFaceRecExtractor
from app.services.analysis.extractors.distance_ratio import DistanceRatioExtractor
from app.services.analysis.utils import update_person_features
from app.storage.minio_client import get_storage_client

logger = logging.getLogger(__name__)

_detector = MediaPipeLandmarkDetector()
_extractor = DlibFaceRecExtractor()
_interpretable_extractor = DistanceRatioExtractor()


class AnalysisPipeline:
    """画像アップロード後の非同期解析パイプライン。

    BackgroundTasks から呼び出される。リクエストセッションは終了済みのため、
    内部で AsyncSessionLocal を使って新規セッションを確立する。
    """

    async def process(self, image_id: str) -> None:
        async with AsyncSessionLocal() as db:
            try:
                await self._run(db, image_id)
            except Exception:
                logger.exception("Pipeline error for image_id=%s", image_id)
                # エラー発生時はステータスを error に更新
                try:
                    await db.execute(
                        update(Image)
                        .where(Image.id == image_id)
                        .values(
                            status=ImageStatus.error,
                            metadata_={"error": "解析中に予期しないエラーが発生しました"},
                        )
                    )
                    await db.commit()
                except Exception:
                    logger.exception("Failed to set error status for image_id=%s", image_id)

    async def _run(self, db: AsyncSession, image_id: str) -> None:
        # --- validating フェーズ ---
        await db.execute(
            update(Image)
            .where(Image.id == image_id)
            .values(status=ImageStatus.validating)
        )
        await db.commit()

        # 画像レコード取得
        image = await db.get(Image, image_id)
        if image is None:
            logger.warning("Image not found: %s", image_id)
            return

        # MinIO から画像をダウンロード
        storage = get_storage_client()
        image_bytes = storage.download(image.storage_path)

        # MediaPipe で顔数チェック
        landmark_result = _detector.detect(image_bytes)

        if landmark_result.face_count == 0:
            await db.execute(
                update(Image)
                .where(Image.id == image_id)
                .values(
                    status=ImageStatus.error,
                    metadata_={"error": "顔が検出されませんでした"},
                )
            )
            await db.commit()
            return

        if landmark_result.face_count >= 2:
            await db.execute(
                update(Image)
                .where(Image.id == image_id)
                .values(
                    status=ImageStatus.error,
                    metadata_={
                        "error": "複数の顔が検出されました。1人だけ写っている画像を使用してください"
                    },
                )
            )
            await db.commit()
            return

        # --- analyzing フェーズ ---
        await db.execute(
            update(Image)
            .where(Image.id == image_id)
            .values(status=ImageStatus.analyzing)
        )
        await db.commit()

        # 特徴量抽出（extract_from_image があれば画像バイト列から直接抽出）
        # Note: DistanceRatioExtractor は extract_from_image を持たないため
        # ロールバック時は else 分岐（extract(LandmarkResult)）が使われる
        if hasattr(_extractor, 'extract_from_image'):
            raw_vector = _extractor.extract_from_image(image_bytes)
            if raw_vector is None:
                await db.execute(
                    update(Image)
                    .where(Image.id == image_id)
                    .values(
                        status=ImageStatus.error,
                        metadata_={"error": "顔の特徴量を抽出できませんでした"},
                    )
                )
                await db.commit()
                return
        else:
            raw_vector = _extractor.extract(landmark_result)

        # landmarks を JSONB 用に変換（list of [x, y, z]）
        landmarks_data = landmark_result.landmarks.tolist()
        person_id = image.person_id

        # 15次元ハンドクラフト特徴量（解釈性補足用）
        interpretable_vector = _interpretable_extractor.extract(landmark_result)

        # features 保存 → person_features 再統合 → comparisons 無効化 → analyzed 更新
        # を1コミットで完結させ、途中失敗時のデータ不整合を防ぐ
        await db.execute(
            pg_insert(Feature)
            .values(
                image_id=image_id,
                model_version=_extractor.model_version,
                landmarks=landmarks_data,
                raw_vector=raw_vector,
                interpretable_vector=interpretable_vector,
            )
            .on_conflict_do_update(
                index_elements=["image_id"],
                set_={
                    "model_version": _extractor.model_version,
                    "landmarks": landmarks_data,
                    "raw_vector": raw_vector,
                    "interpretable_vector": interpretable_vector,
                },
            )
        )

        await update_person_features(db, person_id)

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

        await db.execute(
            update(Image)
            .where(Image.id == image_id)
            .values(status=ImageStatus.analyzed)
        )
        await db.commit()


analysis_pipeline = AnalysisPipeline()

# 他モジュールからランドマーク検出器を再利用できるよう公開する
landmark_detector = _detector
