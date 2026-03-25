# FaceGraph — 顔類似度定量分析アプリケーション

**バージョン**: v1.0
**作成日**: 2026-03-20
**用途**: プロダクト要件定義 + MVPスコープ定義（詳細設計のインプット資料）

---

## 1. プロダクト概要

### 1.1 目的

子供が両親のどちらに似ているかを、顔パーツの幾何学的特徴量に基づいて定量的に算出するアプリケーション。

### 1.2 コアコンセプト

「なんとなく似ている」という主観を排し、顔のランドマーク座標から算出した数値（角度・距離・比率）で類似度をスコア化する。

### 1.3 利用形態

- ローカルPC（Mac、CPUのみ）上のDockerコンテナで動作
- ユーザー認証不要（シングルユーザー・ローカル利用）
- 任意の2人を選んで比較し、結果はDBに蓄積。再アクセス時に過去結果を表示可能
- 画像が変更された場合は過去の比較結果を無効化し、再計算する

---

## 2. 機能要件

### 2.1 人物管理

認証不要。人物レコードを登録・管理する。

| 項目 | 内容 |
|------|------|
| 登録情報 | 名前（表示名）のみ |
| 操作 | 追加・削除（MVP）。編集はPhase 2 |
| 画像 | 1人物につき複数画像を登録可能 |

### 2.2 画像登録・バリデーション

| 項目 | 内容 |
|------|------|
| アップロード | 1人物につき複数画像を登録可能 |
| 画像制約 | 正面顔のみ |
| 顔数バリデーション | 0個 → エラー「顔が検出されませんでした」 |
| | 1個 → 正常。解析パイプラインへ進む |
| | 2個以上 → エラー「複数の顔が検出されました。1人だけ写っている画像を使用してください」 |
| 保存先 | MinIO（S3互換オブジェクトストレージ） |
| 画像変更時 | 画像の追加・削除時に、当該人物の特徴量を再計算し、関連する比較結果を無効化 |

### 2.3 顔解析パイプライン

画像アップロードを起点にバックグラウンドで自動実行する。比較リクエスト時には解析済みデータを使うだけにする。

```
画像アップロード（同期）
  → 顔検出バリデーション（同期：顔の数チェック）
  → レスポンス返却（status: "analyzing"）
  → バックグラウンドタスク起動（非同期）
      → ランドマーク検出（468点）
      → 特徴量抽出・正規化
      → featuresテーブルに保存（ランドマーク座標 + 特徴量ベクトル）
      → person_featuresテーブルを再統合
      → 関連comparisonsを無効化
      → images.status = "analyzed"
```

ステータス遷移:

```
uploaded → validating → analyzing → analyzed
                ↘ error（顔0個 / 複数顔 / 解析失敗）
```

MVPではFastAPIのBackgroundTasksを使用。Celery等のジョブキューはPhase 2以降。

### 2.4 特徴量の定義

顔のランドマーク座標から以下のカテゴリで特徴量を算出する。

**A. 距離ベースの特徴量**
ランドマーク間のユークリッド距離を算出し、基準距離（両目の間隔: IPD）で正規化する。

- 両目間距離（IPD: Inter-Pupillary Distance）← 正規化の基準
- 鼻の長さ（鼻根 → 鼻尖）
- 口幅（左口角 → 右口角）
- 顔幅（左頬 → 右頬）
- 眉間距離
- 目と口の垂直距離

**B. 角度ベースの特徴量**
3点のランドマークから構成される角度を算出する。

- 目頭-鼻尖-目頭 の三角形角度
- 口角-鼻尖-口角 の角度
- 眉端-目頭-鼻根 の角度

**C. 比率ベースの特徴量**
距離の比率を算出し、顔のサイズに依存しない特徴量とする。

- 顔の縦横比（顔高さ / 顔幅）
- 目の幅 / 顔幅
- 鼻の長さ / 顔の高さ
- 口幅 / 両目間距離
- 上顔（額〜鼻根）/ 中顔（鼻根〜鼻尖）/ 下顔（鼻尖〜顎先）の三分割比率

### 2.5 複数画像の統合

1人物が複数画像を登録した場合の特徴量統合方式:

| 方式 | 説明 | MVP |
|------|------|-----|
| 平均方式 | 全画像の特徴量ベクトルの平均値を代表値とする | ✅ デフォルト・固定 |
| 単一選択方式 | ユーザーが1枚を「代表画像」として選択 | Phase 2 |
| 中央値方式 | 外れ値に強い統合 | Phase 2 |

### 2.6 類似度の計算

**比較の単位**: 任意の2人物を選択して比較する。

**類似度メトリクス**: Strategyパターンで差し替え可能に設計する。

| 手法 | 概要 | MVP |
|------|------|-----|
| **コサイン類似度** | 特徴量ベクトル間の角度で類似度を測定。0〜100%で表現 | ✅ デフォルト・固定 |
| ユークリッド距離 | 特徴量空間での直線距離 | Phase 2 |
| Procrustes距離 | ランドマーク点群を最適重ね合わせ後の残差 | Phase 3 |

**出力形式**: スコア表示のみ（パーツ別内訳はPhase 3）。

```
人物A ↔ 人物B: 72%
```

**比較結果のキャッシュ**:
- 比較結果はDBに保存し、同じペアの再比較時はキャッシュから返す
- いずれかの人物の画像が変更された場合、その人物を含む全比較結果を無効化（is_valid = false）
- 無効化された比較にアクセスした場合、自動的に再計算する

---

## 3. 技術選定

### 3.1 顔ランドマーク検出モデル

| モデル | ランドマーク数 | 速度 | GPU要否 | MVP |
|--------|--------------|------|---------|-----|
| **MediaPipe Face Mesh** | 468点 | 高速 | 不要 | ✅ 採用 |
| dlib (68-point) | 68点 | 高速 | 不要 | 差し替え候補 |
| InsightFace (2D106) | 106点 | 中 | 推奨 | 将来候補 |

MediaPipe選定理由: GPU不要でMac Dockerで動作、468点で十分な情報量、正面顔1枚あたり数十msで実用的。

### 3.2 定量化手法

**MVP採用**: 距離比率ベクトル（IPD正規化）。正面顔制約があるため十分な精度が見込める。

### 3.3 類似度メトリクス

**MVP採用**: コサイン類似度。0〜100%のスコアに変換して出力。

### 3.4 技術スタック

| レイヤー | 技術 | 選定理由 |
|----------|------|----------|
| フロントエンド | React + TypeScript | 既存スキルセット |
| バックエンド | FastAPI (Python) | 画像解析ライブラリとの親和性。非同期処理 |
| データベース | PostgreSQL | JSONB型で特徴量を柔軟に保存 |
| オブジェクトストレージ | MinIO | S3互換。Dockerで構築容易 |
| コンテナ管理 | Docker Compose | 4コンテナを一括管理 |
| 画像解析 | MediaPipe + OpenCV | GPU不要。Pythonで統合 |
| 数値計算 | NumPy + SciPy | コサイン類似度・将来のProcrustes解析 |

### 3.5 動作環境

| 項目 | 仕様 |
|------|------|
| ホスト | Mac（CPUのみ） |
| 実行形態 | Docker Compose（4コンテナ） |
| GPU | 不要 |
| メモリ | 4GB以上推奨 |
| 推論速度 | リアルタイム不要。数秒の待機は許容 |

---

## 4. システム構成

### 4.1 全体アーキテクチャ

```
┌──────────────────────────────────────────┐
│              Frontend                     │
│          (React + TypeScript)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │人物一覧  │ │画像登録  │ │比較結果  │  │
│  │・登録    │ │・管理    │ │・履歴    │  │
│  └──────────┘ └──────────┘ └──────────┘  │
└──────────────────┬───────────────────────┘
                   │ REST API
┌──────────────────┴───────────────────────┐
│              Backend                      │
│           (FastAPI + Python)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │人物管理  │ │画像解析  │ │類似度    │  │
│  │API       │ │パイプ    │ │計算      │  │
│  │          │ │ライン    │ │エンジン  │  │
│  └──────────┘ └──────────┘ └──────────┘  │
└───────┬──────────────┬───────────────────┘
        │              │
┌───────┴──────┐ ┌─────┴──────────────────┐
│  PostgreSQL  │ │  MinIO                  │
│              │ │  (S3互換ストレージ)     │
│ - persons    │ │                         │
│ - images     │ │ - 元画像                │
│ - features   │ │ - サムネイル            │
│ - comparisons│ │                         │
└──────────────┘ └─────────────────────────┘
```

### 4.2 Strategyパターンによる差し替え設計

ランドマーク検出・特徴量抽出・類似度計算の3箇所にStrategyパターンを適用し、設定ファイルで切り替え可能にする。

```python
class LandmarkDetector(Protocol):
    def detect(self, image: np.ndarray) -> LandmarkResult: ...

class FeatureExtractor(Protocol):
    def extract(self, landmarks: LandmarkResult) -> FeatureVector: ...

class SimilarityCalculator(Protocol):
    def calculate(self, a: FeatureVector, b: FeatureVector) -> float: ...
```

```yaml
# config.yml
analysis:
  landmark_detector: "mediapipe"       # or "dlib"
  feature_extractor: "distance_ratio"  # or "procrustes", "angle"
  similarity_method: "cosine"          # or "euclidean", "procrustes"
  aggregation: "average"               # or "single", "median"
```

モデルや手法を変更した場合、features.model_versionで管理。バージョン不一致の特徴量は再計算対象とする。

---

## 5. データモデル

### 5.1 ER図

```
┌───────────┐       ┌──────────┐       ┌──────────────┐
│  Person   │1    n │  Image   │1    1 │   Feature    │
│───────────│───────│──────────│───────│──────────────│
│ id (PK)   │       │ id (PK)  │       │ id (PK)      │
│ name      │       │ person_id│       │ image_id (FK)│
│ created_at│       │ path     │       │ model_version│
│ updated_at│       │ status   │       │ landmarks    │
└───────────┘       │ metadata │       │ raw_vector   │
                    │ created_at       │ created_at   │
                    └──────────┘       └──────────────┘

┌───────────────────┐
│ PersonFeature     │  ← 複数画像の統合結果
│───────────────────│
│ id (PK)           │
│ person_id (FK, UQ)│
│ method            │  ← average / single / median
│ feature_vector    │  ← float[]
│ image_count       │
│ created_at        │
└───────────────────┘

┌───────────────────┐
│ Comparison        │  ← 比較結果キャッシュ
│───────────────────│
│ id (PK)           │
│ person_a_id (FK)  │
│ person_b_id (FK)  │
│ similarity_method │  ← cosine / euclidean / procrustes
│ score             │  ← 0.0〜1.0
│ is_valid          │  ← 画像変更時にfalseに
│ created_at        │
│ UQ(person_a_id, person_b_id, similarity_method) │
└───────────────────┘
```

### 5.2 テーブル定義

**persons**

| カラム | 型 | 説明 |
|--------|----|------|
| id | UUID (PK) | |
| name | VARCHAR(100) | 表示名 |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

**images**

| カラム | 型 | 説明 |
|--------|----|------|
| id | UUID (PK) | |
| person_id | UUID (FK → persons) | |
| storage_path | VARCHAR(500) | MinIO上のパス |
| thumbnail_path | VARCHAR(500) | サムネイルパス |
| status | ENUM | uploaded / validating / analyzing / analyzed / error |
| metadata | JSONB | 画像メタ情報（エラー理由等を含む） |
| created_at | TIMESTAMP | |

**features** — 画像単位の解析結果。ランドマーク座標をメタデータとして保持。

| カラム | 型 | 説明 |
|--------|----|------|
| id | UUID (PK) | |
| image_id | UUID (FK → images, UQ) | |
| model_version | VARCHAR(50) | 例: "mediapipe_v0.10" |
| landmarks | JSONB | 生のランドマーク座標（468点のx,y,z） |
| raw_vector | FLOAT[] | 正規化済み特徴量ベクトル |
| created_at | TIMESTAMP | |

**person_features** — 複数画像の統合結果

| カラム | 型 | 説明 |
|--------|----|------|
| id | UUID (PK) | |
| person_id | UUID (FK → persons, UQ) | |
| method | ENUM | average / single / median |
| feature_vector | FLOAT[] | 統合済み特徴量ベクトル |
| image_count | INT | 統合に使用した画像数 |
| created_at | TIMESTAMP | |

**comparisons** — 比較結果キャッシュ

| カラム | 型 | 説明 |
|--------|----|------|
| id | UUID (PK) | |
| person_a_id | UUID (FK → persons) | |
| person_b_id | UUID (FK → persons) | |
| similarity_method | ENUM | cosine / euclidean / procrustes |
| score | FLOAT | 0.0〜1.0 |
| is_valid | BOOLEAN | 画像変更時にfalseへ |
| created_at | TIMESTAMP | |
| | UQ | (person_a_id, person_b_id, similarity_method) |

---

## 6. API設計

### 6.1 エンドポイント一覧

**人物管理**

| Method | Path | 説明 |
|--------|------|------|
| POST | /api/persons | 人物作成 `{ name: string }` |
| GET | /api/persons | 人物一覧（サムネイル・画像枚数付き） |
| GET | /api/persons/{id} | 人物詳細 |
| DELETE | /api/persons/{id} | 人物削除（画像・特徴量・比較結果を連鎖削除） |

**画像管理**

| Method | Path | 説明 |
|--------|------|------|
| POST | /api/persons/{id}/images | 画像アップロード（multipart/form-data） |
| | | 同期: 顔数バリデーション → 非同期: 解析パイプライン起動 |
| | | レスポンス: `{ id, status: "analyzing" }` |
| GET | /api/persons/{id}/images | 画像一覧（ステータス付き） |
| DELETE | /api/images/{id} | 画像削除 → 特徴量再統合 → 比較無効化 |

**比較**

| Method | Path | 説明 |
|--------|------|------|
| POST | /api/comparisons | 比較実行 `{ person_a_id, person_b_id }` |
| | | キャッシュ有効 → キャッシュ返却 / 無効or未計算 → 再計算 |
| | | レスポンス: `{ score: 0.72, is_cached: true }` |
| GET | /api/comparisons | 比較結果履歴一覧 |

### 6.2 無効化の連鎖フロー

```
画像追加/削除
  → 該当image.featureを再計算（追加時）/ 削除（削除時）
  → 該当person_featureを再統合（平均の再計算）
  → comparisons WHERE (person_a_id = X OR person_b_id = X) を is_valid = false
  → 次回アクセス時に自動再計算
```

### 6.3 解析パイプライン擬似コード

```python
async def process_image(image_id: UUID) -> None:
    """画像アップロード後のバックグラウンド処理"""
    image = await get_image(image_id)
    image.status = "validating"

    # 1. MinIOから画像を取得
    img = await download_from_minio(image.storage_path)

    # 2. 顔検出バリデーション
    faces = face_detector.detect_faces(img)
    if len(faces) == 0:
        image.status = "error"
        image.metadata["error"] = "顔が検出されませんでした"
        return
    if len(faces) > 1:
        image.status = "error"
        image.metadata["error"] = f"複数の顔が検出されました（{len(faces)}人）"
        return

    image.status = "analyzing"

    # 3. ランドマーク検出
    landmarks = landmark_detector.detect(img)

    # 4. 特徴量抽出
    feature_vector = feature_extractor.extract(landmarks)

    # 5. featuresテーブルに保存
    await save_feature(
        image_id=image.id,
        model_version="mediapipe_v0.10",
        landmarks=landmarks.to_dict(),
        raw_vector=feature_vector.tolist()
    )
    image.status = "analyzed"

    # 6. person_featuresを再統合
    await recalculate_person_feature(image.person_id)

    # 7. 関連comparisonsを無効化
    await invalidate_comparisons(image.person_id)
```

---

## 7. 画面構成

### 7.1 画面一覧（MVP: 4画面）

| 画面 | 概要 |
|------|------|
| 人物一覧 | 登録済み人物のカード一覧。サムネイル・画像枚数表示。人物追加・削除 |
| 人物詳細 | 画像の登録・削除。登録済み画像のギャラリー。解析ステータス表示 |
| 比較画面 | 2人物をドロップダウンで選択し、類似度スコアを表示 |
| 比較履歴 | 過去の比較結果一覧。有効/無効ステータス付き |

### 7.2 画面ワイヤーフレーム

```
┌─────────────────────────────────────────────────┐
│  人物一覧（トップページ）                         │
│                                                  │
│  [+ 人物を追加]                    [比較する →]  │
│                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐               │
│  │ 写真   │ │ 写真   │ │ 写真   │               │
│  │ 名前   │ │ 名前   │ │ 名前   │               │
│  │ 画像3枚│ │ 画像1枚│ │ 画像2枚│               │
│  │ [削除] │ │ [削除] │ │ [削除] │               │
│  └────────┘ └────────┘ └────────┘               │
└─────────────────────────────────────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐   ┌─────────────────────────┐
│  人物詳細       │   │  比較画面               │
│                 │   │                         │
│  名前: ○○      │   │  [人物A ▼] vs [人物B ▼] │
│                 │   │                         │
│  画像一覧:      │   │  [比較する]             │
│  ┌───┐┌───┐    │   │                         │
│  │img││img│    │   │  類似度: 72%            │
│  │ ✓ ││解析中│  │   │  ████████░░ 72%         │
│  └───┘└───┘    │   │                         │
│                 │   │  [比較履歴を見る]       │
│  [+ 画像追加]   │   └─────────────────────────┘
│  [× 画像削除]   │               │
└─────────────────┘               ▼
                          ┌─────────────────────┐
                          │  比較履歴           │
                          │                     │
                          │  A vs B  72%  有効  │
                          │  A vs C  58%  無効  │
                          │  B vs C  65%  有効  │
                          └─────────────────────┘
```

---

## 8. MVPスコープ

### 8.1 方針

「2人の正面顔画像をアップロードし、類似度スコアを1つ表示できる」を最小ゴール。UIの完成度より解析パイプラインの正確さを優先する。

### 8.2 MVPに含めるもの

| カテゴリ | 機能 |
|----------|------|
| インフラ | Docker Compose（4コンテナ: frontend / backend / postgres / minio） |
| 人物管理 | 登録（名前のみ）、一覧（サムネイル付き）、削除（連鎖削除） |
| 画像管理 | アップロード（複数枚）、顔数バリデーション（0個/2個以上→エラー）、バッチ解析、ステータス表示、削除 |
| 解析 | MediaPipe Face Mesh（468点）、距離比率ベクトル（IPD正規化）、平均方式統合 |
| 比較 | 2人物選択、コサイン類似度スコア表示、キャッシュ、無効化・自動再計算 |
| 比較履歴 | 一覧表示（有効/無効ステータス付き） |

### 8.3 MVPに含めないもの

| 機能 | 理由 | 対象Phase |
|------|------|-----------|
| パーツ別内訳 | スコア表示で十分 | Phase 3 |
| メトリクス切り替えUI | コサイン類似度固定 | Phase 2 |
| 統合方法切り替えUI | 平均方式固定 | Phase 2 |
| モデル差し替え（dlib等） | MediaPipe固定 | Phase 3 |
| 人物の編集（名前変更） | 削除→再作成で代替 | Phase 2 |
| 3人以上の一括比較 | 2人ペアで十分 | Phase 3 |
| Procrustes解析 | コサイン類似度で十分 | Phase 3 |
| ジョブキュー（Celery等） | BackgroundTasksで十分 | Phase 2 |
| レスポンシブ対応 | PC利用前提 | Phase 2 |
| 自動テスト | 手動テストで進める | Phase 2 |

### 8.4 MVP完了基準

1. `docker compose up` で4コンテナが起動し、ブラウザからアクセスできる
2. 人物を作成し、正面顔画像をアップロードできる
3. 顔が検出されない画像・複数顔の画像でエラーが返る
4. アップロード後、自動的にランドマーク検出・特徴量抽出が実行される
5. 2人の人物を選択し、コサイン類似度スコア（0〜100%）が表示される
6. 同じペアを再比較した場合、キャッシュから結果が返る
7. 画像を追加・削除した場合、関連する比較結果が無効化される
8. 比較履歴一覧で過去の結果を確認できる

---

## 9. ディレクトリ構成

```
facegraph/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                      # FastAPIエントリポイント
│   │   ├── config.py                    # 設定（config.yml読み込み）
│   │   ├── models/                      # SQLAlchemy models
│   │   │   ├── person.py
│   │   │   ├── image.py
│   │   │   ├── feature.py
│   │   │   └── comparison.py
│   │   ├── routers/                     # APIエンドポイント
│   │   │   ├── persons.py
│   │   │   ├── images.py
│   │   │   └── comparisons.py
│   │   ├── services/                    # ビジネスロジック
│   │   │   ├── analysis/                # 解析パイプライン
│   │   │   │   ├── pipeline.py          # パイプライン統合
│   │   │   │   ├── detectors/           # Strategy: ランドマーク検出
│   │   │   │   │   ├── base.py          # Protocol定義
│   │   │   │   │   └── mediapipe.py
│   │   │   │   ├── extractors/          # Strategy: 特徴量抽出
│   │   │   │   │   ├── base.py
│   │   │   │   │   └── distance_ratio.py
│   │   │   │   └── calculators/         # Strategy: 類似度計算
│   │   │   │       ├── base.py
│   │   │   │       └── cosine.py
│   │   │   ├── image_service.py
│   │   │   ├── person_service.py
│   │   │   └── comparison_service.py
│   │   ├── storage/
│   │   │   └── minio_client.py
│   │   └── db/
│   │       └── session.py
│   └── config.yml
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.tsx
│       ├── pages/
│       │   ├── PersonList.tsx
│       │   ├── PersonDetail.tsx
│       │   ├── Compare.tsx
│       │   └── CompareHistory.tsx
│       ├── components/
│       │   ├── PersonCard.tsx
│       │   ├── ImageUploader.tsx
│       │   ├── ImageGallery.tsx
│       │   ├── CompareSelector.tsx
│       │   └── ScoreDisplay.tsx
│       └── api/
│           └── client.ts
└── README.md
```

---

## 10. docker-compose.yml

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, minio]
    environment:
      DATABASE_URL: postgresql://facegraph:facegraph@postgres:5432/facegraph
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: facegraph
      POSTGRES_USER: facegraph
      POSTGRES_PASSWORD: facegraph
    volumes: [pgdata:/var/lib/postgresql/data]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
    volumes: [miniodata:/data]

volumes:
  pgdata:
  miniodata:
```

---

## 11. 開発ステップ

| Step | 作業 | 完了の目安 |
|------|------|------------|
| 1 | Docker Compose環境構築 | `docker compose up`で4コンテナ起動 |
| 2 | DB設計・マイグレーション（5テーブル） | テーブル作成確認 |
| 3 | MinIOセットアップ（バケット作成） | 画像のPUT/GETが成功 |
| 4 | 人物管理API（CRUD） | POST/GET/DELETEが動作 |
| 5 | 画像アップロードAPI（MinIO保存 + 顔数バリデーション） | 画像保存＋顔数チェック |
| 6 | 解析パイプライン（MediaPipe + 距離比率ベクトル） | featuresテーブルにデータ保存 |
| 7 | person_features統合（平均方式） | person_featuresに統合ベクトル保存 |
| 8 | 比較API（コサイン類似度 + キャッシュ + 無効化） | スコア算出＋キャッシュ動作確認 |
| 9 | フロントエンド（4画面） | ブラウザから全機能操作可能 |
| 10 | 結合テスト | 完了基準の8項目を全て通過 |

---

## 12. フェーズ別ロードマップ

| Phase | 内容 | 主な機能追加 |
|-------|------|-------------|
| Phase 0 | PoC | MediaPipe + コサイン類似度で2枚のスコアを算出するスクリプト |
| Phase 1 | **MVP（本資料のスコープ）** | Docker Compose環境。人物登録・画像アップロード・比較の最小機能 |
| Phase 2 | 改善 | UI改善、人物編集、メトリクス切替UI、統合方法切替、レスポンシブ、自動テスト |
| Phase 3 | 拡張 | パーツ別内訳、Procrustes解析、モデル差し替え検証、3人以上比較 |

---

## 付録A: 参考文献

- MediaPipe Face Mesh: https://developers.google.com/mediapipe/solutions/vision/face_landmarker
- dlib 68-point: http://dlib.net/face_landmark_detection.py.html
- scipy.spatial.procrustes: https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.procrustes.html
- Shi, Samal, Marx — "How effective are landmarks and their geometry for face recognition?" (CVIU, 2006)
