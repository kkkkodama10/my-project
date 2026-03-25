# タスクリスト: サムネイルの表示 & ランドマークの可視化

## フェーズ1: バックエンド - ビジュアライザー関数

- [x] `backend/app/services/analysis/visualizer.py` を作成
  - [x] `draw_landmarks(image_bytes, landmark_result)` を実装（OpenCV）
  - [x] ランドマーク468点を緑の点で描画
  - [x] BBox（赤い矩形）を描画
  - [x] 顔未検出/複数顔の場合はテキストオーバーレイ

## フェーズ2: バックエンド - エンドポイント追加

- [x] `backend/app/schemas/image.py` の `ImageListResponse` に `model_validator` を追加して `thumbnail_path` を API URL に変換
- [x] `backend/app/routers/images.py` に `GET /api/images/{id}/thumbnail` を追加
- [x] `backend/app/routers/images.py` に `GET /api/images/{id}/landmarks` を追加
  - [x] `_detector` singleton の共有方法を確定して import（pipeline.py に `landmark_detector` を公開）

## フェーズ3: フロントエンド - PersonDetailPage 更新

- [x] `frontend/src/pages/PersonDetailPage.tsx` に「ランドマーク確認」ボタンを追加
  - [x] `analyzed` ステータスの画像カードにのみ表示
  - [x] クリックで `/api/images/{id}/landmarks` を新タブで開く

## フェーズ4: 動作確認

- [x] コンテナリビルド（バックエンドは volume mount で反映済み、フロントエンドは src/ のみ mount）
- [x] `npm run typecheck` を通過確認
- [x] `npm run lint` を通過確認

## フェーズ5: 振り返り

- [x] tasklist.md に振り返り記録

---

## 実装後の振り返り

**実装完了日**: 2026-03-21

**計画と実績の差分**:
- `_put_overlay_text` を設計書の1行実装より改善: 半透明背景追加・画像サイズ比例スケール対応
- `face_count >= 2` のテキストを `f"Multiple faces ({face_count})"` と動的化（顔数を表示）
- `cv2.imencode` の `ok` フラグ確認による `RuntimeError` を追加（設計書にはなかった防御処理）
- `thumbnail_path` の MinIO キーは DB に残るが API レスポンスでは完全に API URL に変換されることを動作確認で確認済み

**実装検証後の追加修正**:
- 検証で指摘された重大問題なし
- MinIO ダウンロード障害時の 500 エラーは MVP 許容範囲として対応見送り

**学んだこと**:
- Pydantic の `model_validator(mode='after')` は `from_attributes=True` でORM読み込み後に実行されるため、MinIOキー→API URL の変換をスキーマレイヤーで完結できる
- MediaPipe のランドマーク座標は 0.0〜1.0 の正規化座標なので、ピクセル変換に画像の width/height をかけるだけで済む
- `docker-compose.yml` のフロントエンド volumes が `./frontend/src:/app/src` のみなので、設定ファイル変更はイメージ再ビルドが必要だが、今回は `src/` のみの変更なので再ビルド不要だった

**次回への改善提案**:
- `get_thumbnail` / `get_landmarks` の MinIO ダウンロード失敗時に 503 を返す try/except を追加する
- `draw_landmarks`（純粋関数）と `compute_thumbnail_url`（Pydantic バリデーター）は pytest ユニットテストの優先候補
- `GET /api/images/{id}/landmarks` でリアルタイム再検出ではなく `features.landmarks` DB カラムを使うと CPU 負荷を削減できる（Phase 2 の改善候補）
