"""既存の analyzed 画像を新しい extractor で再分析する。

使い方:
    docker compose exec backend python -m scripts.reanalyze

処理内容:
    1. features テーブルで model_version が現在の extractor と異なるレコードを取得
    2. 対応する画像を MinIO からダウンロード
    3. DlibFaceRecExtractor.extract_from_image() で再抽出
    4. features.raw_vector と features.model_version を更新
    5. person_features を再集約
    6. 関連する comparisons.is_valid を false に設定
"""
import asyncio
import logging
import sys

from sqlalchemy import or_, select, update

from app.db.session import AsyncSessionLocal
from app.models.comparison import Comparison
from app.models.feature import Feature
from app.models.image import Image, ImageStatus
from app.services.analysis.extractors.dlib_face_rec import DlibFaceRecExtractor
from app.services.analysis.utils import update_person_features
from app.storage.minio_client import get_storage_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def reanalyze_all() -> None:
    extractor = DlibFaceRecExtractor()
    storage = get_storage_client()
    target_version = extractor.model_version

    async with AsyncSessionLocal() as db:
        try:
            # model_version が異なる features を取得
            stmt = (
                select(Feature.id, Feature.image_id, Feature.model_version)
                .where(Feature.model_version != target_version)
            )
            result = await db.execute(stmt)
            rows = result.all()

            if not rows:
                logger.info("再分析対象のレコードはありません（全て %s）", target_version)
                return

            logger.info("再分析対象: %d レコード", len(rows))
            affected_person_ids: set[str] = set()
            success = 0
            failed = 0

            for i, (feature_id, image_id, old_version) in enumerate(rows):
                logger.info("  処理中: %d/%d", i + 1, len(rows))

                image = await db.get(Image, image_id)
                if image is None or image.status != ImageStatus.analyzed:
                    logger.warning("  スキップ: image_id=%s (not found or not analyzed)", image_id)
                    continue

                try:
                    image_bytes = storage.download(image.storage_path)
                except Exception:
                    logger.warning("  スキップ: image_id=%s (MinIO download failed)", image_id)
                    failed += 1
                    continue

                raw_vector = extractor.extract_from_image(image_bytes)
                if raw_vector is None:
                    logger.warning("  失敗: image_id=%s (顔検出失敗)", image_id)
                    failed += 1
                    continue

                await db.execute(
                    update(Feature)
                    .where(Feature.id == feature_id)
                    .values(
                        model_version=target_version,
                        raw_vector=raw_vector,
                    )
                )
                affected_person_ids.add(image.person_id)
                success += 1
                logger.info(
                    "  更新: image_id=%s (%s → %s)", image_id, old_version, target_version
                )

            # person_features を再集約 + comparisons を無効化
            for person_id in affected_person_ids:
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

            await db.commit()
            logger.info("完了: 成功 %d, 失敗 %d, 影響人物 %d 人", success, failed, len(affected_person_ids))

        except Exception:
            await db.rollback()
            logger.exception("再分析バッチで予期しないエラーが発生しました。全件ロールバックします")
            sys.exit(1)


def main() -> None:
    asyncio.run(reanalyze_all())


if __name__ == "__main__":
    main()
