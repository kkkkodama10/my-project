from fastapi import HTTPException
from scipy.spatial.distance import cosine as cosine_distance
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comparison import Comparison, SimilarityMethod
from app.models.person_feature import PersonFeature
from app.schemas.comparison import FeatureBreakdownItem
from app.services.person_service import PersonService

_person_service = PersonService()

# 15次元ハンドクラフト特徴量のラベル定義（DistanceRatioExtractor の出力順序に対応）
FEATURE_LABELS = [
    # 距離 (5)
    {"key": "nose_length", "label": "鼻の長さ", "category": "距離"},
    {"key": "mouth_width", "label": "口の幅", "category": "距離"},
    {"key": "face_width", "label": "顔の幅", "category": "距離"},
    {"key": "brow_gap", "label": "眉間の距離", "category": "距離"},
    {"key": "eye_mouth_distance", "label": "目と口の距離", "category": "距離"},
    # 角度 (3)
    {"key": "eye_nose_angle", "label": "目-鼻の角度", "category": "角度"},
    {"key": "mouth_nose_angle", "label": "口-鼻の角度", "category": "角度"},
    {"key": "brow_eye_nose_angle", "label": "眉-目-鼻の角度", "category": "角度"},
    # 比率 (7)
    {"key": "face_aspect_ratio", "label": "顔の縦横比", "category": "比率"},
    {"key": "eye_face_ratio", "label": "目幅/顔幅", "category": "比率"},
    {"key": "nose_face_ratio", "label": "鼻長/顔高", "category": "比率"},
    {"key": "mouth_ipd_ratio", "label": "口幅/目幅", "category": "比率"},
    {"key": "upper_third", "label": "上顔面比率", "category": "比率"},
    {"key": "middle_third", "label": "中顔面比率", "category": "比率"},
    {"key": "lower_third", "label": "下顔面比率", "category": "比率"},
]


class ComparisonService:
    async def compare(
        self, db: AsyncSession, person_a_id: str, person_b_id: str
    ) -> tuple[float, bool, list[FeatureBreakdownItem] | None]:
        """2人の類似度スコア（0〜100）、is_cached フラグ、ブレークダウンを返す。

        Returns:
            (score, is_cached, breakdown)
        """
        if person_a_id == person_b_id:
            raise HTTPException(status_code=400, detail="同一人物は比較できません")

        # 両人物の存在確認（404 を返す）
        await _person_service.get(db, person_a_id)
        await _person_service.get(db, person_b_id)

        # person_features 取得（エラーメッセージは元の person_id で返す）
        vec_a = await self._get_feature_vector(db, person_a_id)
        vec_b = await self._get_feature_vector(db, person_b_id)

        # person_id を辞書順ソートして正規化（A→B と B→A の重複防止）
        a_id, b_id = sorted([person_a_id, person_b_id])

        # キャッシュ確認（スコアのみキャッシュ、ブレークダウンは毎回計算）
        cached = await self._find_cached(db, a_id, b_id)
        if cached is not None and cached.is_valid:
            breakdown = await self._compute_breakdown(db, person_a_id, person_b_id)
            return cached.score, True, breakdown

        # コサイン類似度計算（負値は 0 にクリップ）
        dist = cosine_distance(vec_a, vec_b)
        similarity = max(0.0, 1.0 - dist)
        score = round(similarity * 100, 2)

        # comparisons テーブルに UPSERT
        try:
            await db.execute(
                pg_insert(Comparison)
                .values(
                    person_a_id=a_id,
                    person_b_id=b_id,
                    similarity_method=SimilarityMethod.cosine,
                    score=score,
                    is_valid=True,
                )
                .on_conflict_do_update(
                    constraint="uq_comparison",
                    set_={"score": score, "is_valid": True},
                )
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        breakdown = await self._compute_breakdown(db, person_a_id, person_b_id)
        return score, False, breakdown

    async def list_all(self, db: AsyncSession) -> list[Comparison]:
        stmt = select(Comparison).order_by(Comparison.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _find_cached(
        self, db: AsyncSession, a_id: str, b_id: str
    ) -> Comparison | None:
        stmt = select(Comparison).where(
            Comparison.person_a_id == a_id,
            Comparison.person_b_id == b_id,
            Comparison.similarity_method == SimilarityMethod.cosine,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_feature_vector(self, db: AsyncSession, person_id: str) -> list[float]:
        stmt = select(PersonFeature.feature_vector).where(
            PersonFeature.person_id == person_id
        )
        result = await db.execute(stmt)
        vector = result.scalar_one_or_none()
        if vector is None:
            raise HTTPException(
                status_code=422,
                detail=f"解析済みの画像がありません（person_id: {person_id}）",
            )
        return vector

    async def _get_interpretable_vector(
        self, db: AsyncSession, person_id: str
    ) -> list[float] | None:
        stmt = select(PersonFeature.interpretable_vector).where(
            PersonFeature.person_id == person_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _compute_breakdown(
        self, db: AsyncSession, person_a_id: str, person_b_id: str
    ) -> list[FeatureBreakdownItem] | None:
        """15次元の次元ごとの類似度を計算し、ラベル付きで返す。"""
        vec_a = await self._get_interpretable_vector(db, person_a_id)
        vec_b = await self._get_interpretable_vector(db, person_b_id)

        if vec_a is None or vec_b is None:
            return None

        # 次元数が期待値と一致しない旧データは安全のためスキップ
        if len(vec_a) != len(FEATURE_LABELS) or len(vec_b) != len(FEATURE_LABELS):
            return None

        breakdown: list[FeatureBreakdownItem] = []
        for i, meta in enumerate(FEATURE_LABELS):
            # 相対差分率で類似度を算出（値域が次元ごとに異なるため）
            diff = abs(vec_a[i] - vec_b[i])
            avg_val = (abs(vec_a[i]) + abs(vec_b[i])) / 2 + 1e-9
            sim = max(0.0, 1.0 - diff / avg_val) * 100

            breakdown.append(FeatureBreakdownItem(
                key=meta["key"],
                label=meta["label"],
                category=meta["category"],
                similarity=round(sim, 1),
                value_a=round(vec_a[i], 4),
                value_b=round(vec_b[i], 4),
            ))

        # 類似度の高い順にソート
        breakdown.sort(key=lambda x: x.similarity, reverse=True)
        return breakdown
