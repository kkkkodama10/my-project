from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeatureBreakdownItem(BaseModel):
    """15次元ハンドクラフト特徴量の次元ごとの類似度。"""

    key: str            # "nose_length" など
    label: str          # "鼻の長さ" など（日本語ラベル）
    category: str       # "距離" | "角度" | "比率"
    similarity: float   # 0.0〜100.0（次元ごとの類似度）
    value_a: float      # person_a の値
    value_b: float      # person_b の値


class ComparisonResponse(BaseModel):
    """POST /api/persons/{a_id}/compare/{b_id} のレスポンス。"""

    score: float        # 0.0〜100.0（dlib 128次元ベース）
    is_cached: bool
    breakdown: list[FeatureBreakdownItem] | None = None  # 15次元の詳細

    model_config = ConfigDict(from_attributes=True)


class ComparisonListItem(BaseModel):
    """GET /api/comparisons の1件分。"""

    id: str
    person_a_id: str
    person_b_id: str
    score: float
    is_valid: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
