# 設計: 類似度計算・比較 API

## 新規ファイル

```
backend/app/
├── schemas/comparison.py          # ComparisonResponse / ComparisonListResponse
├── services/comparison_service.py # ComparisonService（計算・キャッシュ制御）
└── routers/comparisons.py         # 2エンドポイント
```

## 変更ファイル

- `routers/__init__.py` なし（直接 main.py でインポート）
- `main.py`: `comparisons.router` 登録

## エンドポイント設計

### POST /api/persons/{person_a_id}/compare/{person_b_id}

**ルーター**: `persons.py` に追加（`/api/persons` prefix を共有）

レスポンス `200 OK`:
```json
{ "score": 72.45, "is_cached": true }
```

エラー:
- `400` 同一人物
- `422` person_features 未存在（解析未完了）
- `404` person_a or person_b が存在しない

### GET /api/comparisons

**ルーター**: `comparisons.py`（prefix `/api`）

レスポンス `200 OK`:
```json
[
  {
    "id": "...",
    "person_a_id": "...",
    "person_b_id": "...",
    "score": 72.45,
    "is_valid": true,
    "created_at": "..."
  }
]
```

## ComparisonService ロジック

```
compare(db, person_a_id, person_b_id):
  1. a_id == b_id → 400
  2. 両 person 存在確認（person_service.get）
  3. person_id を辞書順ソート（正規化）
  4. comparisons テーブルから (a_id, b_id, cosine) で既存レコード検索
  5. is_valid == True → score 返す (is_cached=True)
  6. それ以外（未存在 or is_valid=False）:
     a. 両 person_features 取得（なければ 422）
     b. scipy.spatial.distance.cosine で類似度計算
     c. score_pct = round((1 - cosine_dist) * 100, 2)
     d. comparisons に UPSERT（is_valid=True）
     e. score 返す (is_cached=False)
```

## コサイン類似度の正規化ノート

`scipy.spatial.distance.cosine` は 0（完全一致）〜 2 の cosine distance を返す。
`similarity = 1 - cosine_distance`（-1〜1）を 100 倍してスコアとする。
負値が発生した場合は 0 にクリップ（`max(0, similarity * 100)`）。
