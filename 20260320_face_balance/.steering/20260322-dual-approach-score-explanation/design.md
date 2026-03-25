# 設計: 二刀流機能（dlib スコア + 15次元解釈性補足）

## 変更対象ファイル

### バックエンド

| ファイル | 変更内容 |
|---------|---------|
| `backend/app/models/feature.py` | `interpretable_vector` カラム追加（ARRAY(Float), nullable） |
| `backend/app/models/person_feature.py` | `interpretable_vector` カラム追加（ARRAY(Float), nullable） |
| `backend/alembic/versions/xxxx_add_interpretable_vector.py` | マイグレーション新規作成 |
| `backend/app/services/analysis/pipeline.py` | DistanceRatioExtractor 追加実行、interpretable_vector 保存 |
| `backend/app/services/analysis/utils.py` | update_person_features() で interpretable_vector 平均も保存 |
| `backend/app/services/comparison_service.py` | ブレークダウン計算ロジック追加、戻り値変更 |
| `backend/app/schemas/comparison.py` | FeatureBreakdownItem、ComparisonResponse.breakdown 追加 |
| `backend/app/routers/persons.py` | compare_persons レスポンスに breakdown 追加 |
| `backend/scripts/backfill_interpretable.py` | 既存データ移行スクリプト新規作成 |

### フロントエンド

| ファイル | 変更内容 |
|---------|---------|
| `frontend/src/api/client.ts` | ComparisonResult に breakdown フィールド追加 |
| `frontend/src/pages/ComparePage.tsx` | ブレークダウン表示UI追加 |

## 設計方針

- 詳細は `docs/new-features/dual_approach_score_and_explanation.md` を参照
- ブレークダウン計算は相対差分率（`1 - |a-b| / avg(|a|,|b|)`）で正規化
- キャッシュヒット時もブレークダウンはオンデマンド計算（comparisons テーブルには保存しない）
- 15次元ラベルは FEATURE_LABELS 定数として comparison_service.py に定義
