# 設計: 画像登録・バリデーション

## ディレクトリ構成（新規作成ファイル）

```
backend/app/
├── storage/
│   ├── __init__.py          # 新規
│   └── minio_client.py      # 新規: MinIO クライアント（boto3）
├── schemas/
│   └── image.py             # 新規: ImageResponse, ImageListResponse
├── services/
│   └── image_service.py     # 新規: ImageService
└── routers/
    └── images.py            # 新規: /api/persons/{id}/images + /api/images/{id}
main.py                      # 更新: images ルーター追加
```

## MinIO クライアント設計 (storage/minio_client.py)

- `boto3.client("s3")` を使用（endpoint_url で MinIO を指定）
- モジュール初期化時にバケットが存在しない場合は作成
- 遅延初期化（関数 `get_storage_client()` を公開）
- メソッド:
  - `upload(key: str, data: bytes, content_type: str) -> None`
  - `delete(key: str) -> None`

## 画像バリデーション

```python
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

# PIL で magic bytes チェック（Content-Type は信頼しない）
img = PILImage.open(io.BytesIO(data))
if img.format not in ALLOWED_FORMATS:
    raise HTTPException(status_code=400, detail="...")
```

## パス生成

```python
def _make_storage_key(person_id: str, image_id: str, ext: str) -> str:
    return f"originals/{person_id}/{image_id}.{ext}"

def _make_thumbnail_key(person_id: str, image_id: str) -> str:
    return f"thumbnails/{person_id}/{image_id}.jpg"
```

## ImageService 設計 (services/image_service.py)

```python
class ImageService:
    async def upload(db, person_id, file: UploadFile) -> Image
    async def list_by_person(db, person_id) -> list[Image]
    async def get(db, image_id) -> Image
    async def delete(db, image_id) -> None
        # 1. MinIO 削除（original + thumbnail）
        # 2. DB 削除（CASCADE → features）
        # 3. comparisons.is_valid = False（関連レコード）
```

## ルーター設計 (routers/images.py)

- `POST /api/persons/{person_id}/images` → status 202
- `GET /api/persons/{person_id}/images` → status 200
- `DELETE /api/images/{image_id}` → status 204
- `file: UploadFile = File(...)` で multipart/form-data 受付

## アーキテクチャ方針

- MinIO クライアントは同期 boto3 を使用（FastAPI の `run_in_executor` なし・MVP 規模で十分）
- サムネイル生成は PIL の `thumbnail()` メソッドを使用（JPEG 変換）
- 画像 ID は DB の `gen_random_uuid()` ではなく Python 側で `uuid.uuid4()` を生成し、MinIO パスと DB レコードで共用する
- 背景タスク（解析パイプライン）のフックポイントをコメントで明示し、次フィーチャーで実装
