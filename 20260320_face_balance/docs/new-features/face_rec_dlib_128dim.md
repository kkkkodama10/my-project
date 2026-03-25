# face_rec (dlib 128次元埋め込み) 本番統合 実装計画

## 概要

PoC で検証済みの `face_recognition` ライブラリ（dlib 128次元埋め込み）を
バックエンドの分析パイプラインに統合し、顔比較精度を大幅に向上させる。

### PoC 結果（採用根拠）

| 指標 | 現状 (baseline 15次元) | face_rec (dlib 128次元) | 改善幅 |
|------|----------------------|------------------------|--------|
| AUC | 0.824 | **0.952** | +15.5% |
| EER | 22.0% | **7.3%** | 誤認率 1/3 |
| d' | 1.30 | **2.18** | 識別力 1.7倍 |
| Genuine 平均 | 0.992 | 0.958 | — |
| Impostor 平均 | 0.971 | 0.845 | 分離が明確に |

---

## 現状アーキテクチャ

```
画像アップロード
  → BackgroundTasks: AnalysisPipeline.process()
    → MediaPipeLandmarkDetector.detect()     … 468点ランドマーク検出
    → DistanceRatioExtractor.extract()       … 15次元特徴量抽出  ← ★ここを差し替え
    → features テーブルに保存 (landmarks + raw_vector)
    → person_features テーブルに平均ベクトルを集約
    → comparisons テーブルの is_valid を false に

比較リクエスト
  → ComparisonService.compare()
    → person_features.feature_vector を取得
    → scipy.cosine_distance で類似度算出
    → comparisons テーブルに UPSERT
```

### 変更の影響範囲

```
backend/
├── Dockerfile                                  ← 変更: cmake + dlib ビルド依存追加
├── requirements.txt                            ← 変更: face_recognition 追加
└── app/services/analysis/
    ├── pipeline.py                             ← 変更: extractor 差し替え
    └── extractors/
        ├── base.py                             ← 変更: Protocol 拡張
        ├── distance_ratio.py                   ← 変更なし（残す）
        └── dlib_face_rec.py                    ← 新規: dlib 128次元抽出器
```

**変更しないもの:**
- DB スキーマ（`raw_vector` は `FLOAT[]` 型で次元数に依存しない）
- `person_features` テーブル（`feature_vector` も `FLOAT[]`）
- `ComparisonService`（コサイン類似度の計算ロジックはそのまま）
- API エンドポイント（変更なし）
- フロントエンド（変更なし）
- MediaPipe 検出器（ランドマーク可視化で引き続き使用）

---

## 設計方針

### 1. FeatureExtractor の拡張（Strategy パターン）

現状の `FeatureExtractor` Protocol は `LandmarkResult` を入力とする:

```python
class FeatureExtractor(Protocol):
    model_version: str
    def extract(self, result: LandmarkResult) -> list[float]: ...
```

dlib は独自の顔検出 + エンコーディングを行うため、`LandmarkResult` ではなく
**画像バイト列を直接受け取る**インターフェースが必要。

#### 方針: Protocol を拡張し、画像バイト列を受け取れるようにする

```python
class FeatureExtractor(Protocol):
    model_version: str

    def extract(self, result: LandmarkResult) -> list[float]: ...

    def extract_from_image(self, image_bytes: bytes) -> list[float] | None:
        """画像バイト列から直接特徴量を抽出する。
        デフォルト実装は NotImplementedError を raise する。
        """
        ...
```

- `DistanceRatioExtractor`: 従来通り `extract(LandmarkResult)` を使用
- `DlibFaceRecExtractor`: `extract_from_image(bytes)` を使用
- `pipeline.py` で `extract_from_image` が実装されていれば優先的に呼び出す

### 2. パイプラインでの分岐

```python
# pipeline.py
if hasattr(_extractor, 'extract_from_image') and _extractor.extract_from_image is not None:
    raw_vector = _extractor.extract_from_image(image_bytes)
    if raw_vector is None:
        # 顔検出失敗 → error ステータス
        ...
else:
    raw_vector = _extractor.extract(landmark_result)
```

### 3. MediaPipe ランドマーク検出は維持

dlib の顔検出と MediaPipe のランドマーク検出は**別の役割**を持つ:

- **dlib**: 128次元埋め込みの生成（比較用）
- **MediaPipe**: 468点ランドマークの検出（可視化用）

ランドマーク可視化エンドポイント (`GET /api/images/{id}/landmarks`) は
引き続き MediaPipe を使用する。

ただしパイプラインでは、dlib が顔を検出できれば OK とし、
MediaPipe のランドマーク検出はオプショナルにする（可視化のため保存はする）。

### 4. model_version によるバージョン管理

`features.model_version` を使って新旧の特徴量を区別する:

- 現状: `"distance_ratio_v1"`
- 新規: `"dlib_face_rec_v1"`

**マイグレーション方針:**
- 新しい extractor に切り替えた後、既存の `features` レコードは古い `model_version` のまま
- 新規アップロード画像から `dlib_face_rec_v1` で保存
- 既存画像の再分析は、バッチスクリプトで対応（後述）

---

## 実装タスク

### Phase 1: インフラ準備

#### 1-1. Dockerfile に dlib ビルド依存を追加

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    cmake \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

追加パッケージ: `cmake`, `g++`（dlib のビルドに必要）

> **注意**: dlib のビルドには 5〜10分かかる。Docker レイヤーキャッシュを活用するため
> `requirements.txt` を先に COPY する現在の構成を維持する。

#### 1-2. requirements.txt に face_recognition を追加

```
face_recognition==1.3.0
```

`dlib` は `face_recognition` の依存として自動インストールされる。

#### 1-3. Docker イメージのビルド確認

```bash
docker compose build backend
```

### Phase 2: Extractor 実装

#### 2-1. DlibFaceRecExtractor の作成

`backend/app/services/analysis/extractors/dlib_face_rec.py`:

```python
"""dlib ベースの 128次元顔埋め込み抽出器。

face_recognition ライブラリを使用し、学習済み ResNet モデルで
128次元の顔埋め込みベクトルを生成する。
"""
import io
import logging
import threading

import numpy as np
from PIL import Image as PILImage

from app.services.analysis.detectors.base import LandmarkResult

logger = logging.getLogger(__name__)

try:
    import face_recognition
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False
    logger.warning("face_recognition is not installed. DlibFaceRecExtractor is unavailable.")


class DlibFaceRecExtractor:
    """dlib 128次元顔埋め込み抽出器。"""

    model_version: str = "dlib_face_rec_v1"

    def __init__(self) -> None:
        if not _AVAILABLE:
            raise ImportError(
                "face_recognition がインストールされていません。"
                "requirements.txt を確認してください。"
            )
        self._lock = threading.Lock()

    def extract(self, result: LandmarkResult) -> list[float]:
        """LandmarkResult からの抽出（未使用だが Protocol 互換のため実装）。"""
        raise NotImplementedError(
            "DlibFaceRecExtractor は extract_from_image() を使用してください"
        )

    def extract_from_image(self, image_bytes: bytes) -> list[float] | None:
        """画像バイト列から 128次元埋め込みベクトルを返す。

        顔が検出できない場合は None を返す。
        """
        pil = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(pil)

        with self._lock:
            encodings = face_recognition.face_encodings(img_array)

        if not encodings:
            return None

        # 複数顔が検出された場合は最初の1つを使用
        # （顔数チェックは pipeline 側の MediaPipe で実施済み）
        return encodings[0].tolist()
```

#### 2-2. FeatureExtractor Protocol の拡張

`backend/app/services/analysis/extractors/base.py`:

```python
from typing import Protocol

from app.services.analysis.detectors.base import LandmarkResult


class FeatureExtractor(Protocol):
    """特徴量抽出器インターフェース。"""

    model_version: str

    def extract(self, result: LandmarkResult) -> list[float]:
        """LandmarkResult から特徴量ベクトルを抽出して返す。"""
        ...

    def extract_from_image(self, image_bytes: bytes) -> list[float] | None:
        """画像バイト列から直接特徴量を抽出する。

        このメソッドが実装されている場合、pipeline は extract() より
        こちらを優先して呼び出す。
        顔検出失敗時は None を返す。
        """
        ...
```

#### 2-3. pipeline.py の変更

`backend/app/services/analysis/pipeline.py` の `_run()` メソッドを変更:

```python
# 変更前
_extractor = DistanceRatioExtractor()

# 変更後
from app.services.analysis.extractors.dlib_face_rec import DlibFaceRecExtractor
_extractor = DlibFaceRecExtractor()
```

`_run()` 内の特徴量抽出部分:

```python
# 変更前
raw_vector = _extractor.extract(landmark_result)

# 変更後
if hasattr(_extractor, 'extract_from_image'):
    raw_vector = _extractor.extract_from_image(image_bytes)
    if raw_vector is None:
        await db.execute(
            update(Image)
            .where(Image.id == image_id)
            .values(
                status=ImageStatus.error,
                metadata_={"error": "顔の特徴量を抽出できませんでした"},
            )
        )
        await db.commit()
        return
else:
    raw_vector = _extractor.extract(landmark_result)
```

**MediaPipe ランドマーク検出は維持する。** ランドマーク可視化と顔数バリデーションのため、
dlib 切り替え後もパイプライン冒頭の `_detector.detect()` はそのまま残す。

### Phase 3: 既存データのマイグレーション

#### 3-1. 再分析バッチスクリプト

既存の `analyzed` 画像を新しい extractor で再分析するスクリプト:

`backend/scripts/reanalyze.py`:

```python
"""既存の analyzed 画像を新しい extractor で再分析する。

使い方:
    docker compose exec backend python -m scripts.reanalyze
"""
```

処理内容:
1. `features` テーブルで `model_version != 'dlib_face_rec_v1'` のレコードを取得
2. 対応する画像を MinIO からダウンロード
3. `DlibFaceRecExtractor.extract_from_image()` で再抽出
4. `features.raw_vector` と `features.model_version` を更新
5. `person_features` を再集約
6. 関連する `comparisons.is_valid` を false に設定

#### 3-2. 実行手順

```bash
# 1. 新しいイメージをビルド
docker compose build backend

# 2. コンテナを再起動
docker compose up -d backend

# 3. 既存データの再分析
docker compose exec backend python -m scripts.reanalyze

# 4. ログで確認
docker compose logs -f backend
```

### Phase 4: テストと検証

#### 4-1. 動作確認項目

- [ ] Docker イメージのビルドが成功する
- [ ] 新規画像のアップロード → 分析 → `dlib_face_rec_v1` で特徴量が保存される
- [ ] `features.raw_vector` が 128次元になっている
- [ ] ランドマーク可視化 (`GET /api/images/{id}/landmarks`) が引き続き動作する
- [ ] 2人の比較 → スコアが PoC と同等の精度で算出される
- [ ] 同一人物の比較 → 高スコア（90%台）
- [ ] 別人の比較 → 低スコア（80%台以下）
- [ ] 再分析スクリプトで既存データが更新される
- [ ] フロントエンドに変更が不要なことを確認

#### 4-2. 性能確認

- [ ] 画像1枚あたりの分析時間（目標: 5秒以内）
- [ ] Docker イメージサイズの増加量（dlib モデル ~100MB 追加）
- [ ] メモリ使用量の増加（dlib CNN 推論分）

---

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| dlib ビルド時間が長い (5-10分) | 低 | Docker レイヤーキャッシュで初回のみ。CI/CD ではキャッシュ戦略を検討 |
| Docker イメージサイズ増大 | 低 | dlib + face_recognition で ~200MB 増。slim ベースイメージを維持 |
| 128次元 → 15次元の混在期間 | 中 | `model_version` で区別。再分析スクリプトで一括移行 |
| face_recognition の更新停滞 | 低 | 安定版（1.3.0）を固定。dlib 自体は活発にメンテされている |
| メモリ使用量の増加 | 低 | dlib の HOG ベース検出は軽量。CNN モードは使わない |

---

## ロールバック手順

問題発生時は `pipeline.py` の extractor を戻すだけで即座にロールバック可能:

```python
# ロールバック: dlib → baseline
_extractor = DistanceRatioExtractor()  # 元に戻す
```

`DistanceRatioExtractor` は削除せず残しておくため、コード1行の変更で切り替えられる。

---

## スケジュール目安

| フェーズ | 作業内容 | 見積り |
|----------|----------|--------|
| Phase 1 | Dockerfile + requirements.txt + ビルド確認 | 0.5h |
| Phase 2 | Extractor 実装 + pipeline 変更 | 1h |
| Phase 3 | 再分析スクリプト + 既存データ移行 | 0.5h |
| Phase 4 | テスト + 検証 | 1h |
| **合計** | | **3h** |
