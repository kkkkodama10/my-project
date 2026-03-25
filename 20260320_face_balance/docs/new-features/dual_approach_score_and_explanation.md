# 二刀流機能: dlib スコア + 15次元解釈性補足

## 概要

dlib 128次元埋め込みによる正確な類似度スコアに加え、既存の15次元ハンドクラフト特徴量（DistanceRatioExtractor）を用いた「なぜ似ているか」の言語化を提供する。

**目的**: ユーザーに「72%似ている」だけでなく「目の間隔や鼻の長さが特に似ている」という解釈可能な説明を返す。

## 現状のアーキテクチャ

```
画像アップロード
  → pipeline.py: DlibFaceRecExtractor.extract_from_image(bytes) → 128次元
  → Feature.raw_vector (FLOAT[]) に保存
  → Feature.landmarks (JSONB) に MediaPipe 468点を保存
  → PersonFeature.feature_vector に人物平均ベクトル（128次元）を保存

比較リクエスト
  → ComparisonService.compare()
  → PersonFeature.feature_vector 同士のコサイン類似度 → score (0〜100)
  → ComparisonResponse(score, is_cached) を返却
```

## 設計方針

### 方針: パイプライン拡張 + 比較時オンデマンド計算

15次元特徴量はパイプライン内で Feature テーブルに追加保存し、比較時に PersonFeature から集約済み15次元ベクトルを取得して次元ごとの類似度を計算する。

### なぜこの方針か

1. **Feature.landmarks にはすでに MediaPipe 468点が保存されている** → 15次元はランドマークから決定論的に算出可能。ただし毎回比較時に再計算するのは非効率なため、パイプラインで事前計算して保存する。
2. **PersonFeature に15次元の集約ベクトルも保持する** → 比較時にパフォーマンスを確保。
3. **既存の DistanceRatioExtractor をそのまま再利用** → 新規コード最小限。

## データモデル変更

### Feature テーブル

```python
# 追加カラム
interpretable_vector: Mapped[list[float] | None] = mapped_column(
    ARRAY(Float), nullable=True  # 既存データとの互換性のため nullable
)
```

- 15次元のハンドクラフト特徴量を格納
- 既存の `raw_vector`（128次元 dlib）はそのまま

### PersonFeature テーブル

```python
# 追加カラム
interpretable_vector: Mapped[list[float] | None] = mapped_column(
    ARRAY(Float), nullable=True
)
```

- 人物ごとの15次元平均ベクトル

### Alembic マイグレーション

```python
# alembic/versions/xxxx_add_interpretable_vector.py
def upgrade():
    op.add_column('features', sa.Column('interpretable_vector', ARRAY(sa.Float), nullable=True))
    op.add_column('person_features', sa.Column('interpretable_vector', ARRAY(sa.Float), nullable=True))

def downgrade():
    op.drop_column('person_features', 'interpretable_vector')
    op.drop_column('features', 'interpretable_vector')
```

## パイプライン変更

### pipeline.py の変更

```python
from app.services.analysis.extractors.distance_ratio import DistanceRatioExtractor

_interpretable_extractor = DistanceRatioExtractor()

# _run() 内の analyzing フェーズで追加:
# dlib 128次元（既存）
raw_vector = _extractor.extract_from_image(image_bytes)

# 15次元ハンドクラフト（追加）
interpretable_vector = _interpretable_extractor.extract(landmark_result)
```

Feature の INSERT に `interpretable_vector` カラムを追加する。

### utils.py の変更

`update_person_features()` で `interpretable_vector` の平均も計算・保存する。

```python
async def update_person_features(db: AsyncSession, person_id: str) -> None:
    stmt = (
        select(Feature.raw_vector, Feature.interpretable_vector)
        .join(Image, Image.id == Feature.image_id)
        .where(Image.person_id == person_id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    vectors_128 = [r[0] for r in rows if r[0]]
    vectors_15 = [r[1] for r in rows if r[1]]

    avg_128 = np.mean(vectors_128, axis=0).tolist() if vectors_128 else None
    avg_15 = np.mean(vectors_15, axis=0).tolist() if vectors_15 else None

    # UPSERT で両方のベクトルを保存
```

## 比較ロジック変更

### ComparisonService の変更

```python
async def compare(self, db, person_a_id, person_b_id) -> tuple[float, bool, list[dict] | None]:
    # ... 既存のスコア計算（128次元コサイン類似度）は変更なし ...

    # 15次元ブレークダウン計算（追加）
    breakdown = await self._compute_breakdown(db, person_a_id, person_b_id)

    return score, is_cached, breakdown
```

### ブレークダウン計算

```python
FEATURE_LABELS = [
    # 距離 (5)
    {"key": "nose_length",         "label": "鼻の長さ",    "category": "距離"},
    {"key": "mouth_width",         "label": "口の幅",      "category": "距離"},
    {"key": "face_width",          "label": "顔の幅",      "category": "距離"},
    {"key": "brow_gap",            "label": "眉間の距離",   "category": "距離"},
    {"key": "eye_mouth_distance",  "label": "目と口の距離", "category": "距離"},
    # 角度 (3)
    {"key": "eye_nose_angle",      "label": "目-鼻の角度",         "category": "角度"},
    {"key": "mouth_nose_angle",    "label": "口-鼻の角度",         "category": "角度"},
    {"key": "brow_eye_nose_angle", "label": "眉-目-鼻の角度",     "category": "角度"},
    # 比率 (7)
    {"key": "face_aspect_ratio",   "label": "顔の縦横比",   "category": "比率"},
    {"key": "eye_face_ratio",      "label": "目幅/顔幅",    "category": "比率"},
    {"key": "nose_face_ratio",     "label": "鼻長/顔高",    "category": "比率"},
    {"key": "mouth_ipd_ratio",     "label": "口幅/目幅",    "category": "比率"},
    {"key": "upper_third",         "label": "上顔面比率",   "category": "比率"},
    {"key": "middle_third",        "label": "中顔面比率",   "category": "比率"},
    {"key": "lower_third",         "label": "下顔面比率",   "category": "比率"},
]

async def _compute_breakdown(self, db, person_a_id, person_b_id) -> list[dict] | None:
    """15次元の次元ごとの類似度を計算し、ラベル付きで返す。"""
    vec_a = await self._get_interpretable_vector(db, person_a_id)
    vec_b = await self._get_interpretable_vector(db, person_b_id)

    if vec_a is None or vec_b is None:
        return None  # 旧データで15次元未計算の場合は None

    breakdown = []
    for i, meta in enumerate(FEATURE_LABELS):
        # 各次元の差の絶対値 → 類似度に変換
        # 値域が次元ごとに異なるため、相対差分率で評価
        diff = abs(vec_a[i] - vec_b[i])
        avg_val = (abs(vec_a[i]) + abs(vec_b[i])) / 2 + 1e-9
        similarity = max(0.0, 1.0 - diff / avg_val) * 100

        breakdown.append({
            "key": meta["key"],
            "label": meta["label"],
            "category": meta["category"],
            "similarity": round(similarity, 1),
            "value_a": round(vec_a[i], 4),
            "value_b": round(vec_b[i], 4),
        })

    # 類似度の高い順にソート
    breakdown.sort(key=lambda x: x["similarity"], reverse=True)
    return breakdown
```

## API レスポンス変更

### ComparisonResponse スキーマ

```python
class FeatureBreakdownItem(BaseModel):
    key: str            # "nose_length"
    label: str          # "鼻の長さ"
    category: str       # "距離" | "角度" | "比率"
    similarity: float   # 0.0〜100.0（次元ごとの類似度）
    value_a: float      # person_a の値
    value_b: float      # person_b の値

class ComparisonResponse(BaseModel):
    score: float           # 0.0〜100.0（dlib 128次元ベース、変更なし）
    is_cached: bool
    breakdown: list[FeatureBreakdownItem] | None  # 15次元の詳細（追加）
```

### レスポンス例

```json
{
  "score": 72.35,
  "is_cached": false,
  "breakdown": [
    {"key": "face_aspect_ratio", "label": "顔の縦横比", "category": "比率", "similarity": 95.2, "value_a": 1.32, "value_b": 1.34},
    {"key": "nose_length", "label": "鼻の長さ", "category": "距離", "similarity": 91.8, "value_a": 0.45, "value_b": 0.44},
    {"key": "eye_mouth_distance", "label": "目と口の距離", "category": "距離", "similarity": 88.3, "value_a": 0.78, "value_b": 0.73},
    ...
  ]
}
```

## フロントエンド変更

### ComparePage.tsx

スコア表示の下に、ブレークダウンのバーチャートを追加:

```
┌─────────────────────────────┐
│     72.35% 似ている          │  ← 既存（dlib スコア）
│                             │
│  ▸ 詳細を見る               │  ← 折りたたみトグル（追加）
│  ┌─────────────────────┐   │
│  │ 顔の縦横比    ████████ 95%│
│  │ 鼻の長さ      ███████░ 92%│
│  │ 目と口の距離  ██████░░ 88%│
│  │ ...                      │
│  └─────────────────────┘   │
└─────────────────────────────┘
```

- `breakdown` が `null` の場合は「詳細を見る」を非表示
- カテゴリ（距離・角度・比率）ごとにグルーピング表示も検討

## 既存データの移行

### 移行スクリプト: `scripts/backfill_interpretable.py`

既存の Feature レコード（`landmarks` は保存済み）から15次元を再計算:

```python
# 1. Feature.landmarks (JSONB) から numpy 配列を復元
# 2. DistanceRatioExtractor.extract(LandmarkResult) で15次元を算出
# 3. Feature.interpretable_vector を UPDATE
# 4. PersonFeature.interpretable_vector を再集約
```

既存データの landmarks は保存済みなので、画像の再ダウンロードは不要。

## キャッシュ無効化

比較結果のキャッシュ（`comparisons` テーブル）には `breakdown` を保存しない。理由:

1. `breakdown` は `score` と比べてデータ量が大きい（15要素のJSON）
2. `score`（128次元ベース）のキャッシュ判定は既存のまま使える
3. `breakdown` は `person_features.interpretable_vector` から毎回計算してもコストが低い（15次元の引き算のみ）

したがって、キャッシュヒット時も `breakdown` はオンデマンドで計算する。

## タスク概要

### フェーズ1: データモデル拡張
1. Feature モデルに `interpretable_vector` カラム追加
2. PersonFeature モデルに `interpretable_vector` カラム追加
3. Alembic マイグレーション作成

### フェーズ2: パイプライン拡張
4. pipeline.py で DistanceRatioExtractor を追加実行し、Feature.interpretable_vector に保存
5. utils.py の update_person_features() で interpretable_vector の平均も計算・保存

### フェーズ3: 比較ロジック拡張
6. FEATURE_LABELS 定義とブレークダウン計算ロジックを ComparisonService に追加
7. ComparisonResponse スキーマに breakdown フィールド追加
8. compare エンドポイントのレスポンスに breakdown を含める

### フェーズ4: 既存データ移行
9. backfill_interpretable.py スクリプト作成（landmarks → 15次元再計算）

### フェーズ5: フロントエンド
10. ComparePage.tsx にブレークダウン表示コンポーネント追加

## リスクと対策

| リスク | 対策 |
|--------|------|
| 15次元の次元ごと類似度が直感的でない | 相対差分率で正規化。PoCで妥当性検証済み（AUC=0.857） |
| 既存データに interpretable_vector が NULL | nullable カラム + backfill スクリプトで移行。breakdown は null 許容 |
| パイプライン処理時間の増加 | DistanceRatioExtractor.extract() は純Python計算で ~1ms。dlib の ~50ms と比べ無視できるレベル |
| 128次元スコアと15次元ブレークダウンの乖離 | UIで明示：「総合スコアは AI が算出、詳細は顔のパーツごとの比較」と説明 |

## ロールバック計画

1. `interpretable_vector` は nullable カラムのため、無視すれば既存動作に影響なし
2. `ComparisonResponse.breakdown` を `None` に固定すればフロントエンドも既存動作に戻る
3. Alembic downgrade でカラム削除可能
