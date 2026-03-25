# タスクリスト: 類似度計算・比較 API

## フェーズ1: スキーマ定義

- [x] `schemas/comparison.py` 作成（ComparisonResponse・ComparisonListResponse）

## フェーズ2: ComparisonService

- [x] `services/comparison_service.py` 作成
  - [x] `compare(db, person_a_id, person_b_id)` — キャッシュ確認 + 計算 + UPSERT
  - [x] `list_all(db)` — 全比較結果を created_at 降順で返す

## フェーズ3: ルーター

- [x] `routers/persons.py` に `POST /{person_a_id}/compare/{person_b_id}` 追加
- [x] `routers/comparisons.py` 作成（GET /api/comparisons）
- [x] `main.py` に `comparisons.router` 登録

## フェーズ4: 動作確認

- [x] キャッシュなし → 計算して `is_cached=false` で返ることを確認
- [x] 同ペアで再リクエスト → `is_cached=true` で返ることを確認
- [x] 同一人物指定 → 400 エラー確認
- [x] person_features なし → 422 エラー確認
- [x] GET /api/comparisons → 履歴一覧が返ることを確認

## フェーズ5: 振り返り

- [x] tasklist.md に振り返り記録

---

## 実装後の振り返り

**実装完了日**: 2026-03-21

**計画と実績の差分**:
- `GET /api/comparisons` は `comparisons.py` を新規作成（計画通り）
- `POST /.../compare/...` は `persons.py` に追加（設計書通り、prefix 共有）
- 比較履歴に `updated_at` は不要だった（PRD にも記載なし）

**実装検証後の修正**:
- `_get_feature_vector` の呼び出しを正規化「前」に移動（エラーメッセージを元の person_id で返すため）
- `ComparisonResponse` に `model_config = ConfigDict(from_attributes=True)` 追加
- UPSERT 周辺に `try/except/rollback` 追加
- `list_comparisons` の手動 `model_validate` を削除（FastAPI の `response_model` に委譲）

**学んだこと**:
- ID 正規化（辞書順ソート）と エラーメッセージ用 ID は分けて考える必要がある
- `on_conflict_do_update` の `constraint=` パラメータには UNIQUE 制約名を文字列で渡す

**次回への改善提案**:
- テストコードの整備（キャッシュ判定・辞書順正規化・エッジケース）
- フロントエンドの実装（残り2機能：比較履歴表示含む）
