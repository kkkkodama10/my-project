# 設計: サムネイルの表示 & ランドマークの可視化

## バックエンド変更

### 1. ImageListResponse の thumbnail_path を API URL に変換

`backend/app/schemas/image.py`

```python
from pydantic import model_validator

class ImageListResponse(BaseModel):
    ...
    thumbnail_path: str | None  # MinIO キー → API URL に変換

    @model_validator(mode='after')
    def compute_thumbnail_url(self) -> 'ImageListResponse':
        if self.thumbnail_path is not None:
            self.thumbnail_path = f"/api/images/{self.id}/thumbnail"
        return self
```

### 2. 新エンドポイント: GET /api/images/{id}/thumbnail

`backend/app/routers/images.py` に追加。

```python
@router.get("/api/images/{image_id}/thumbnail")
async def get_thumbnail(image_id: str, db: AsyncSession) -> StreamingResponse:
    image = await _service.get(db, image_id)
    if not image.thumbnail_path:
        raise HTTPException(404, "サムネイルが存在しません")
    storage = get_storage_client()
    data = storage.download(image.thumbnail_path)
    return StreamingResponse(io.BytesIO(data), media_type="image/jpeg")
```

### 3. 新エンドポイント: GET /api/images/{id}/landmarks

`backend/app/routers/images.py` に追加。

```python
@router.get("/api/images/{image_id}/landmarks")
async def get_landmarks(image_id: str, db: AsyncSession) -> StreamingResponse:
    image = await _service.get(db, image_id)
    storage = get_storage_client()
    image_bytes = storage.download(image.storage_path)
    result = _detector.detect(image_bytes)
    annotated = draw_landmarks(image_bytes, result)
    return StreamingResponse(io.BytesIO(annotated), media_type="image/jpeg")
```

### 4. draw_landmarks 関数

`backend/app/services/analysis/visualizer.py`

```python
import cv2
import numpy as np
from PIL import Image as PILImage

def draw_landmarks(image_bytes: bytes, landmark_result: LandmarkResult) -> bytes:
    # PIL で読み込み → BGR numpy array (OpenCV)
    pil = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]

    if landmark_result.face_count == 1:
        lm = landmark_result.landmarks  # (468, 3) - 値は 0.0～1.0 の正規化座標
        xs = (lm[:, 0] * w).astype(int)
        ys = (lm[:, 1] * h).astype(int)

        # BBox
        x1, y1, x2, y2 = xs.min(), ys.min(), xs.max(), ys.max()
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)  # 赤

        # ランドマーク点（緑）
        for x, y in zip(xs, ys):
            cv2.circle(img, (int(x), int(y)), 2, (0, 255, 0), -1)
    else:
        # 顔未検出 or 複数顔
        label = "No face detected" if landmark_result.face_count == 0 else "Multiple faces"
        cv2.putText(img, label, (20, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, (0, 140, 255), 2)  # オレンジ

    # JPEG エンコード
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return bytes(buf)
```

## フロントエンド変更

### PersonDetailPage に「ランドマーク確認」ボタン追加

各画像カードに `analyzed` ステータスの場合のみ表示するボタン:

```tsx
{image.status === 'analyzed' && (
  <a
    href={`/api/images/${image.id}/landmarks`}
    target="_blank"
    rel="noopener noreferrer"
    className="text-xs text-blue-500 hover:underline mt-1 inline-block"
  >
    ランドマーク確認
  </a>
)}
```

## データフロー

```
ブラウザ
  │ GET /api/images/{id}/thumbnail
  ↓
FastAPI router
  │ image.thumbnail_path (MinIO key)
  ↓
StorageClient.download(key)
  │ bytes
  ↓
StreamingResponse(image/jpeg)

ブラウザ
  │ GET /api/images/{id}/landmarks
  ↓
FastAPI router
  │ image.storage_path (MinIO key)
  ↓
StorageClient.download(key)
  │ bytes
  ↓
MediaPipeLandmarkDetector.detect()
  │ LandmarkResult(landmarks, face_count)
  ↓
draw_landmarks()
  │ annotated JPEG bytes
  ↓
StreamingResponse(image/jpeg)
```

## 注意点

- `_detector` (MediaPipeLandmarkDetector) は `pipeline.py` のシングルトンを再利用する
  → `from app.services.analysis.pipeline import _detector` とするのではなく、
    同じシングルトンを使うため `pipeline.py` から export するか、別途 detector の singleton を共有する方式にする
- ランドマーク座標は MediaPipe の正規化座標（0.0〜1.0）→ 画像サイズ掛け算でピクセル座標に変換
- `routers/images.py` は現在 router-only なので、`_detector` を使うために `pipeline` の detector インスタンスを import する
