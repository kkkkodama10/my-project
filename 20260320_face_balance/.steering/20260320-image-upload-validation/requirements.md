# 要求仕様: 画像登録・バリデーション

## 概要

FaceGraph MVP の画像登録機能 (PRD §コア機能2) を実装する。
画像ファイルをバリデーションし、MinIO に保存して DB に記録する。
顔数チェックはバックグラウンド（次フィーチャー「解析パイプライン」）で実施。

## 要求内容

### エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/persons/{person_id}/images` | 画像をアップロード |
| GET | `/api/persons/{person_id}/images` | 人物の画像一覧を取得 |
| DELETE | `/api/images/{image_id}` | 画像を削除（MinIO + DB CASCADE） |

### 受け入れ条件（PRD より）

- [ ] 1人物につき複数画像をアップロードできる
- [ ] 存在しない人物 ID へのアップロードは 404 を返す
- [ ] ファイルが画像（JPEG / PNG / WebP）でない場合は 400 を返す
- [ ] ファイルサイズが 20MB 超の場合は 413 を返す
- [ ] 画像は MinIO（`facegraph-images` バケット）に保存される
- [ ] パス構成: `originals/{person_id}/{image_id}.{ext}` / `thumbnails/{person_id}/{image_id}.jpg`
- [ ] サムネイルは最長辺 256px で JPEG 生成・保存する
- [ ] DB に `images` レコードが作成される（status = "uploaded"）
- [ ] 画像削除時: MinIO から削除 + DB CASCADE（features も連動削除）
- [ ] 画像削除時: 対象人物の `comparisons` を `is_valid = false` に更新する

### レスポンス形式

**POST /api/persons/{id}/images レスポンス (202)**:
```json
{ "id": "uuid", "person_id": "uuid", "status": "uploaded", "created_at": "..." }
```
**エラー**:
- 404: 人物が存在しない
- 400: ファイルが画像でない
- 413: ファイルサイズが 20MB 超

**GET /api/persons/{id}/images レスポンス (200)**:
```json
[{ "id": "uuid", "person_id": "uuid", "status": "analyzed", "thumbnail_path": "...", "created_at": "..." }]
```

**DELETE /api/images/{id} レスポンス (204)**: No Content
