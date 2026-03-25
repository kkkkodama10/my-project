"""既存の Feature レコードに interpretable_vector を backfill する。

使い方:
    docker compose exec backend python -m scripts.backfill_interpretable

処理内容:
    1. interpretable_vector が NULL の Feature レコードを取得
    2. Feature.landmarks (JSONB) から numpy 配列を復元
    3. DistanceRatioExtractor.extract(LandmarkResult) で15次元を算出
    4. Feature.interpretable_vector を UPDATE
    5. 影響人物の PersonFeature.interpretable_vector を再集約
"""
import asyncio
import logging
import sys

import numpy as np
from sqlalchemy import select, update

from app.db.session import AsyncSessionLocal
from app.models.feature import Feature
from app.models.image import Image
from app.services.analysis.detectors.base import LandmarkResult
from app.services.analysis.extractors.distance_ratio import DistanceRatioExtractor
from app.services.analysis.utils import update_person_features

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def backfill_all() -> None:
    extractor = DistanceRatioExtractor()

    async with AsyncSessionLocal() as db:
        try:
            # interpretable_vector が NULL の features を取得
            stmt = (
                select(Feature.id, Feature.image_id, Feature.landmarks)
                .where(Feature.interpretable_vector.is_(None))
            )
            result = await db.execute(stmt)
            rows = result.all()

            if not rows:
                logger.info("backfill 対象のレコードはありません")
                return

            logger.info("backfill 対象: %d レコード", len(rows))
            affected_person_ids: set[str] = set()
            success = 0
            failed = 0

            for i, (feature_id, image_id, landmarks_data) in enumerate(rows):
                logger.info("  処理中: %d/%d", i + 1, len(rows))

                try:
                    # landmarks JSONB → numpy 配列に復元
                    landmarks_array = np.array(landmarks_data, dtype=np.float64)
                    landmark_result = LandmarkResult(
                        face_count=1,
                        landmarks=landmarks_array,
                    )

                    interpretable_vector = extractor.extract(landmark_result)

                    await db.execute(
                        update(Feature)
                        .where(Feature.id == feature_id)
                        .values(interpretable_vector=interpretable_vector)
                    )

                    # person_id を取得
                    image = await db.get(Image, image_id)
                    if image is not None:
                        affected_person_ids.add(image.person_id)

                    success += 1
                except Exception:
                    logger.warning("  失敗: feature_id=%s", feature_id, exc_info=True)
                    failed += 1
                    continue

            # Feature UPDATE を可視化してから PersonFeature を集約
            await db.flush()
            for person_id in affected_person_ids:
                await update_person_features(db, person_id)

            await db.commit()
            logger.info(
                "完了: 成功 %d, 失敗 %d, 影響人物 %d 人",
                success, failed, len(affected_person_ids),
            )

        except Exception:
            await db.rollback()
            logger.exception("backfill で予期しないエラーが発生しました。全件ロールバックします")
            sys.exit(1)


def main() -> None:
    asyncio.run(backfill_all())


if __name__ == "__main__":
    main()
