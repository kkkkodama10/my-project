# 要求仕様: 類似度計算・比較 API

## 概要

PRD §コア機能6・7 の実装。
2人の人物を指定してコサイン類似度スコアを計算・表示する API と、比較履歴一覧 API を実装する。

## エンドポイント

- `POST /api/persons/{person_a_id}/compare/{person_b_id}` — 2人の類似度を計算して返す
- `GET /api/comparisons` — 全比較履歴を一覧で返す

## 受け入れ条件（PRD §6・7 より）

### 類似度計算
- [ ] `POST /api/persons/{a_id}/compare/{b_id}` でコサイン類似度スコア（0〜100%）を返す
- [ ] `is_valid = true` の既存キャッシュがある場合は再計算せずにそのまま返す（`is_cached: true`）
- [ ] `is_valid = false` または未計算の場合は `person_features.feature_vector` でコサイン類似度を計算する
- [ ] 計算結果を `comparisons` テーブルに UPSERT する
- [ ] レスポンス形式: `{ score: float(0-100), is_cached: bool }`
- [ ] 一方または両方の人物に `person_features` がない場合: 422 エラー「解析済みの画像がありません」
- [ ] `person_a_id == person_b_id` の場合: 400 エラー「同一人物は比較できません」

### 比較履歴
- [ ] `GET /api/comparisons` で全比較結果を `created_at` 降順で返す
- [ ] レスポンスに `is_valid` ステータスを含む

## 計算仕様

- 類似度メソッド: `cosine`（`SimilarityMethod.cosine`）
- コサイン類似度: `scipy.spatial.distance.cosine` → `1 - cosine_distance`
- スコア変換: `score_pct = round(similarity * 100, 2)`（0〜100の float）
- `person_a_id` と `person_b_id` は辞書順で正規化（`a_id < b_id`）して保存する
  （A→B と B→A の重複レコードを防ぐため）
