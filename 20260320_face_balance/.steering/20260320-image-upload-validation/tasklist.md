# タスクリスト: 画像登録・バリデーション

## 🚨 タスク完全完了の原則
全てのタスクを`[x]`にすること。未完了タスクを残したまま作業を終了しない。

---

## フェーズ1: MinIO クライアント作成

- [x] `backend/app/storage/__init__.py` を作成する
- [x] `backend/app/storage/minio_client.py` を作成する（bucket 自動作成・upload・delete）

## フェーズ2: Pydantic スキーマ作成

- [x] `backend/app/schemas/image.py` を作成する（ImageResponse, ImageListResponse）

## フェーズ3: ImageService 作成

- [x] `backend/app/services/image_service.py` を作成する（upload, list_by_person, get, delete）

## フェーズ4: ルーター作成・main.py 登録

- [x] `backend/app/routers/images.py` を作成する（POST/GET/DELETE エンドポイント）
- [x] `backend/app/main.py` に images ルーターを追加する

## フェーズ5: 動作確認

- [x] `docker compose exec backend python -c "from app.routers.images import router; print('OK')"` でインポートエラーがないことを確認する
- [x] 人物を作成し、画像をアップロードして 202 が返ることを確認する
- [x] 画像一覧 GET で返ること確認する
- [x] MinIO コンソール（localhost:9001）でファイルが保存されていることを確認する（storage_path / thumbnail_path のレスポンスで確認）
- [x] 存在しない person_id で 404 が返ることを確認する
- [x] 20MB 超ファイルで 413 が返ることを確認する（ダミーデータ使用）
- [x] 非画像ファイル（テキスト）で 400 が返ることを確認する
- [x] DELETE で 204 が返り一覧が空になることを確認する

## フェーズ6: 振り返り記録

- [x] 実装後の振り返りを記録する

---

## 実装後の振り返り

### 実装完了日
2026-03-20

### 計画と実績の差分
- **計画通り**: MinIO クライアント（boto3 S3）・画像バリデーション（PIL magic bytes）・DB レコード作成・削除副作用すべて実装
- **追加対応**: PIL の RGBA/P → RGB 変換（JPEG サムネイル生成時に必要）を実装
- **設計変更**: Image.id を Python 側で `uuid.uuid4()` で生成し MinIO パスと DB で共用（`server_default=gen_random_uuid()` は使わない）- これによりアップロード前にパスを決定できる
- **バックグラウンドタスク**: 解析パイプライン統合点をコメントで明示し、次フィーチャーに委譲

### 学んだこと
- `PIL.Image.open()` は magic bytes でフォーマットを自動判別するため、`Content-Type` ヘッダーより信頼性が高い
- boto3 の `delete_object` は存在しないキーでもエラーを投げないため、`try/except ClientError` で `head_object` などと組み合わせなくてよい
- SQLAlchemy の `server_default=text("gen_random_uuid()")` はサーバー側で生成されるため、`db.refresh()` 前に Python 側でオブジェクトの ID を参照できない。画像パスと ID を事前に揃えるには Python 側で UUID を生成する必要がある
- MinIO の `head_bucket` で存在確認 → `create_bucket` のパターンが安全（レースコンディションはあるが MVP スケールで問題なし）

### 次回への改善提案
- 解析パイプライン実装時: `image_service.py` の `# NOTE: バックグラウンド解析パイプラインのフックポイント` コメントを実際の `background_tasks.add_task()` 呼び出しに置き換える（ルーターに `BackgroundTasks` 引数を追加）
- `_invalidate_comparisons` は `image_service.py` にあるが、将来的には `comparison_service.py` に移動すべき
- MinIO クライアントのグローバル singleton は FastAPI lifespan イベントで初期化する方式に統一するとよりクリーン
