# タスクリスト: 二刀流機能（dlib スコア + 15次元解釈性補足）

## フェーズ1: データモデル拡張

- [x] 1-1. Feature モデルに interpretable_vector カラム追加
- [x] 1-2. PersonFeature モデルに interpretable_vector カラム追加
- [x] 1-3. Alembic マイグレーション作成

## フェーズ2: パイプライン拡張

- [x] 2-1. pipeline.py で DistanceRatioExtractor を追加実行し、Feature.interpretable_vector に保存
- [x] 2-2. utils.py の update_person_features() で interpretable_vector の平均も計算・保存

## フェーズ3: 比較ロジック拡張

- [x] 3-1. ComparisonResponse スキーマに FeatureBreakdownItem と breakdown フィールド追加
- [x] 3-2. ComparisonService に FEATURE_LABELS 定義とブレークダウン計算ロジック追加
- [x] 3-3. compare エンドポイント（routers/persons.py）のレスポンスに breakdown を含める

## フェーズ4: 既存データ移行

- [x] 4-1. backfill_interpretable.py スクリプト作成（landmarks → 15次元再計算）

## フェーズ5: フロントエンド

- [x] 5-1. client.ts の ComparisonResult 型に breakdown フィールド追加
- [x] 5-2. ComparePage.tsx にブレークダウン表示コンポーネント追加

---

## 実装後の振り返り

### 実装完了日
2026-03-22

### 計画と実績の差分

1. **implementation-validator の指摘による追加修正**
   - `_compute_breakdown()` にベクトル長の境界チェックを追加（次元数不一致時は None を返す）
   - `backfill_interpretable.py` に `await db.flush()` を追加（PersonFeature 集約前の Feature UPDATE 可視性を保証）
   - `ComparisonService.compare()` の戻り値を `list[dict]` → `list[FeatureBreakdownItem]` に変更し、ルーター層の変換ロジックを削除（レイヤー責務の明確化）

2. **計画どおりに進んだ点**
   - データモデルの nullable 設計、Alembic マイグレーション、パイプライン拡張、ブレークダウン計算ロジック、フロントエンドUI はすべてスペックどおりに実装
   - 既存の DistanceRatioExtractor をそのまま再利用でき、新規アルゴリズムコードは不要だった

### 学んだこと

- `FEATURE_LABELS` と `DistanceRatioExtractor.extract()` の出力順序が暗黙的に対応している。将来次元を変更する場合は、DistanceRatioExtractor 側にラベル定義を持たせるか、テストで順序を固定する仕組みが必要
- 相対差分率 `1 - |a-b| / avg(|a|,|b|)` は値域が次元ごとに異なる場合にシンプルかつ有効な正規化手法だが、値が 0 に近い次元（例: 三分割比の中顔面 ~0.33）では小さな差が大きな影響を与えるため、UIでの説明文が重要

### 次回への改善提案

1. **`FEATURE_LABELS` の一元管理**: `DistanceRatioExtractor` 内に定義し、`comparison_service.py` からインポートする方式に変更
2. **ユニットテスト**: `_compute_breakdown()` の境界値テスト（同値ベクトル→全100%、ゼロベクトル、次元数不一致）
3. **フロントエンドのしきい値定数化**: `similarityColor` の 90/70/50 を定数に抽出

### 成果物一覧

| ファイル | 操作 | 内容 |
|---------|------|------|
| `backend/app/models/feature.py` | 変更 | interpretable_vector カラム追加 |
| `backend/app/models/person_feature.py` | 変更 | interpretable_vector カラム追加 |
| `backend/alembic/versions/a1b2c3d4e5f6_add_interpretable_vector.py` | 新規 | マイグレーション |
| `backend/app/services/analysis/pipeline.py` | 変更 | DistanceRatioExtractor 追加実行 |
| `backend/app/services/analysis/utils.py` | 変更 | interpretable_vector 平均計算追加 |
| `backend/app/services/comparison_service.py` | 変更 | FEATURE_LABELS・ブレークダウン計算・戻り値型変更 |
| `backend/app/schemas/comparison.py` | 変更 | FeatureBreakdownItem・breakdown フィールド追加 |
| `backend/app/routers/persons.py` | 変更 | レスポンスに breakdown 追加 |
| `backend/scripts/backfill_interpretable.py` | 新規 | 既存データ移行スクリプト |
| `frontend/src/api/client.ts` | 変更 | FeatureBreakdownItem 型・breakdown フィールド追加 |
| `frontend/src/pages/ComparePage.tsx` | 変更 | ブレークダウン表示UI追加 |
