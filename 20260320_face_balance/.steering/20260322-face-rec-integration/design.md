# 設計: face_rec (dlib 128次元埋め込み) 本番統合

## 変更対象ファイル

### 新規作成
- `backend/app/services/analysis/extractors/dlib_face_rec.py` — DlibFaceRecExtractor

### 変更
- `backend/app/services/analysis/extractors/base.py` — Protocol 拡張 (extract_from_image)
- `backend/app/services/analysis/pipeline.py` — extractor 差し替え + extract_from_image 対応
- `backend/Dockerfile` — cmake, g++ 追加
- `backend/requirements.txt` — face_recognition 追加

### 新規（スクリプト）
- `backend/scripts/reanalyze.py` — 既存データ再分析バッチ

### 変更なし
- DB スキーマ / Alembic マイグレーション
- API エンドポイント
- ComparisonService
- フロントエンド
- MediaPipe 検出器（ランドマーク可視化用に維持）

## 設計詳細

### 1. FeatureExtractor Protocol 拡張

```python
class FeatureExtractor(Protocol):
    model_version: str
    def extract(self, result: LandmarkResult) -> list[float]: ...
    def extract_from_image(self, image_bytes: bytes) -> list[float] | None: ...
```

### 2. DlibFaceRecExtractor

- `model_version = "dlib_face_rec_v1"`
- `extract_from_image(bytes)` → face_recognition.face_encodings() で 128次元ベクトル
- `extract(LandmarkResult)` → NotImplementedError（Protocol 互換のため定義）
- スレッドセーフ（threading.Lock）

### 3. Pipeline 変更

- `_extractor` を `DlibFaceRecExtractor()` に差し替え
- `hasattr(_extractor, 'extract_from_image')` で分岐
- MediaPipe ランドマーク検出は維持（顔数バリデーション + landmarks 保存 + 可視化）
- dlib で顔検出失敗時は error ステータス

### 4. ロールバック

pipeline.py の `_extractor = DlibFaceRecExtractor()` を
`_extractor = DistanceRatioExtractor()` に戻すだけ。
