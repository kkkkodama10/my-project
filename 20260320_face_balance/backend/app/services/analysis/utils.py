"""分析パイプライン共通ユーティリティ。"""
import numpy as np
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature import Feature
from app.models.image import Image
from app.models.person_feature import AggregationMethod, PersonFeature


async def update_person_features(db: AsyncSession, person_id: str) -> None:
    """その人物の全 analyzed 画像の特徴量を平均して person_features を upsert する。

    128次元（dlib）と15次元（ハンドクラフト）の両方を集約する。
    呼び出し元でコミットする必要がある（このメソッド内では commit しない）。
    """
    stmt = (
        select(Feature.raw_vector, Feature.interpretable_vector)
        .join(Image, Image.id == Feature.image_id)
        .where(Image.person_id == person_id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    vectors_128 = [row[0] for row in rows if row[0]]
    vectors_15 = [row[1] for row in rows if row[1]]

    if not vectors_128:
        return

    avg_128 = np.mean(vectors_128, axis=0).tolist()
    avg_15 = np.mean(vectors_15, axis=0).tolist() if vectors_15 else None

    await db.execute(
        pg_insert(PersonFeature)
        .values(
            person_id=person_id,
            method=AggregationMethod.average,
            feature_vector=avg_128,
            interpretable_vector=avg_15,
            image_count=len(vectors_128),
        )
        .on_conflict_do_update(
            index_elements=["person_id"],
            set_={
                "method": AggregationMethod.average,
                "feature_vector": avg_128,
                "interpretable_vector": avg_15,
                "image_count": len(vectors_128),
            },
        )
    )
