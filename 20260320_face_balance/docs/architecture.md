# 技術仕様書 (Architecture Design Document)

**バージョン**: 1.0
**作成日**: 2026-03-20
**プロジェクト**: FaceGraph

---

## テクノロジースタック

### 言語・ランタイム

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.11 | バックエンド・解析エンジン |
| Node.js | 20 LTS | フロントエンドビルド |
| TypeScript | 5.x | フロントエンド開発言語 |

### フレームワーク・ライブラリ（バックエンド）

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| FastAPI | 0.111 | REST API フレームワーク | 非同期対応・型ヒント活用・自動ドキュメント生成 |
| SQLAlchemy | 2.0 | ORM（非同期） | asyncioネイティブ対応・Alembicとの連携 |
| Alembic | 1.13 | DBマイグレーション | SQLAlchemy公式ツール |
| MediaPipe | 0.10 | 顔ランドマーク検出 | GPU不要・468点・Mac Docker対応 |
| OpenCV | 4.9 | 画像I/O・サムネイル生成 | MediaPipeとの親和性 |
| NumPy | 1.26 | 数値計算・ベクトル演算 | コサイン類似度計算 |
| SciPy | 1.13 | 統計計算 | 将来のProcrustes解析対応 |
| Pydantic | 2.x | リクエスト/レスポンスバリデーション | FastAPIとの統合 |
| boto3 / minio | 最新 | MinIOクライアント | S3互換API |
| asyncpg | 0.29 | PostgreSQL非同期ドライバ | SQLAlchemy asyncバックエンド |

### フレームワーク・ライブラリ（フロントエンド）

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| React | 18 | UIフレームワーク | コンポーネント再利用・エコシステム |
| Vite | 5 | ビルドツール | 高速HMR・開発体験 |
| React Router | 6 | ページルーティング | SPA構成 |
| TanStack Query | 5 | サーバー状態管理・ポーリング | 解析ステータスポーリングに活用 |
| Axios | 1.x | HTTPクライアント | リクエスト/レスポンスインターセプタ |
| Tailwind CSS | 3 | スタイリング | ユーティリティファーストで高速UI構築 |

### インフラ・開発ツール

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| Docker Compose | 2.x | コンテナ管理 | 4コンテナを1コマンドで起動 |
| PostgreSQL | 16 | リレーショナルDB | JSONB・FLOAT[]型サポート |
| MinIO | latest | オブジェクトストレージ | S3互換・Docker完結 |

---

## アーキテクチャパターン

### 全体構成（レイヤードアーキテクチャ）

```
┌──────────────────────────────────────────────────┐
│  Presentation Layer（Frontend: React）             │
│  - 画面描画・ユーザーインタラクション                │
│  - APIクライアント（TanStack Query + Axios）        │
├──────────────────────────────────────────────────┤
│  API Layer（FastAPI Routers）                      │
│  - HTTPリクエスト受付・レスポンス整形                │
│  - 入力バリデーション（Pydantic）                   │
│  - BackgroundTasks起動                            │
├──────────────────────────────────────────────────┤
│  Service Layer（Business Logic）                   │
│  - PersonService / ImageService / ComparisonService│
│  - AnalysisPipeline（Strategyパターン）            │
├──────────────────────────────────────────────────┤
│  Data Layer                                       │
│  ┌────────────────┐  ┌───────────────────────┐   │
│  │ PostgreSQL     │  │ MinIO                 │   │
│  │ (SQLAlchemy)   │  │ (boto3 client)        │   │
│  └────────────────┘  └───────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### バックエンド内部アーキテクチャ

```
routers/          ← HTTPレイヤー（薄い）
  ↓
services/         ← ビジネスロジック（主役）
  ↓
services/analysis/  ← 解析パイプライン（Strategyパターン）
  ├── detectors/     ← LandmarkDetector Protocol
  ├── extractors/    ← FeatureExtractor Protocol
  └── calculators/   ← SimilarityCalculator Protocol
  ↓
models/ + db/     ← データアクセス（SQLAlchemy）
storage/          ← MinIOアクセス
```

#### 各レイヤーの責務

| レイヤー | 責務 | 禁止事項 |
|---------|------|---------|
| routers | HTTPリクエスト受付・Pydanticバリデーション・レスポンス整形 | ビジネスロジック実装 |
| services | ビジネスロジック・トランザクション管理 | HTTP詳細への依存 |
| analysis | 解析アルゴリズム（Strategy実装） | DB/HTTP直接アクセス |
| models/db | DBアクセス | ビジネスロジック実装 |
| storage | MinIOアクセス | ビジネスロジック実装 |

---

## データ永続化戦略

### ストレージ方式

| データ種別 | ストレージ | フォーマット | 理由 |
|-----------|----------|-------------|------|
| 人物・画像・比較メタデータ | PostgreSQL | リレーショナル | 整合性保証・UNIQUEConstraint |
| 顔ランドマーク座標（468点） | PostgreSQL JSONB | `{ "0": {"x":..,"y":..,"z":..}, ... }` | 柔軟なスキーマ・クエリ可能 |
| 特徴量ベクトル | PostgreSQL FLOAT[] | `[0.12, 0.34, ...]` | NumPyとの相互変換が容易 |
| 画像ファイル（元画像） | MinIO | JPEG / PNG / WebP | S3互換・バイナリ管理 |
| サムネイル | MinIO | JPEG（最長辺256px） | 一覧表示の高速化 |

### MinIOバケット構成

```
facegraph-images/
├── originals/{person_id}/{image_id}.{ext}    # 元画像
└── thumbnails/{person_id}/{image_id}.jpg     # サムネイル
```

### バックアップ戦略

- **頻度**: MVP段階では手動バックアップ（`docker volume` のtarアーカイブ）
- **保存先**: `./backups/` ディレクトリ（ホストマシン）
- **対象**: `pgdata` ボリューム（PostgreSQL）、`miniodata` ボリューム（MinIO）
- **復元**: `docker compose down` → ボリュームリストア → `docker compose up`

---

## Strategyパターン詳細設計

### 差し替えポイント

```python
# config.yml で制御
analysis:
  landmark_detector: "mediapipe"       # MVP固定
  feature_extractor: "distance_ratio"  # MVP固定
  similarity_method: "cosine"          # MVP固定
  aggregation: "average"               # MVP固定
```

### モデルバージョン管理

`features.model_version` で解析手法のバージョンを記録する。
設定変更によりバージョンが変わった場合、旧バージョンの `features` レコードは再計算対象となる。

```python
MODEL_VERSION = "mediapipe_v0.10_distance_ratio_v1"
# バージョン不一致の場合: pipeline.process()が再実行される
```

---

## パフォーマンス要件

### レスポンスタイム目標

| 操作 | 目標時間 | 測定環境 |
|------|---------|---------|
| 画像アップロード（同期部分） | 5秒以内 | Mac CPU、ファイルサイズ < 20MB |
| 顔解析パイプライン（バックグラウンド） | 30秒以内 | Mac CPU、MediaPipe推論 |
| 比較結果取得（キャッシュヒット） | 500ms以内 | ローカル環境 |
| 比較結果取得（再計算） | 3秒以内 | ローカル環境 |
| 人物一覧取得（最大100人） | 1秒以内 | ローカル環境 |
| ブラウザ画面表示 | 2秒以内 | ローカル環境 |

### リソース使用量（4コンテナ合計）

| リソース | 上限 | 主な消費元 |
|---------|------|-----------|
| メモリ | 4GB | MediaPipe推論（~500MB）+ PostgreSQL（~256MB）+ MinIO（~256MB）|
| CPU（推論時） | 100%（シングルコア） | MediaPipe Face Mesh |
| ディスク | 10GB | 画像ファイル蓄積（MinIOボリューム） |

---

## セキュリティアーキテクチャ

### データ保護

- **ローカル専用**: `localhost` のみアクセス許可。外部公開設計なし
- **顔画像の外部送信なし**: 全処理をローカルDockerコンテナ内で完結
- **環境変数管理**: DB接続情報・MinIO認証情報は `docker-compose.yml` の `environment` で管理（ローカル開発用途のため許容）

### 入力検証

- **ファイルタイプ**: `Content-Type` + PIL magic bytes で JPEG/PNG/WebP のみ許可
- **ファイルサイズ**: 1ファイル最大20MB（FastAPI `UploadFile` + サイズチェック）
- **名前フィールド**: Pydantic `constr(min_length=1, max_length=100)` でバリデーション
- **UUID検証**: Pydantic `UUID` 型でパスパラメータを自動検証

### CORS設定

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## スケーラビリティ設計

### MVP時点の想定上限

| 項目 | 上限 | 対策 |
|------|------|------|
| 登録人物数 | 100人 | インデックス最適化 |
| 1人物あたりの画像数 | 20枚 | サムネイル帯域削減 |
| 比較結果キャッシュ | 数千件 | UNIQUE制約で重複防止 |
| 同時接続 | 1（シングルユーザー） | BackgroundTasksで十分 |

### Phase 2以降の拡張ポイント

- **Celeryジョブキュー**: BackgroundTasksからCelery + Redisへ。大量処理・失敗リトライ対応
- **複数ユーザー対応**: 認証機能追加（JWT等）と人物データのユーザー分離
- **手法切り替えUI**: Strategyパターン設計済みのため、設定ファイル変更なしにUI操作で差し替え可能
- **水平スケール**: 現設計はシングルホスト前提。将来はDBをホスト分離可能

---

## テスト戦略

### MVP段階（手動テスト）

MVP完了基準の8項目を手動で確認する:

1. `docker compose up` でブラウザアクセス確認
2. 人物作成・一覧表示
3. 顔画像アップロード（正常・顔0個・複数顔）
4. 解析ステータス遷移（`analyzed` への遷移確認）
5. 2人比較・スコア表示
6. キャッシュ動作（再比較でキャッシュ返却）
7. 画像削除後の比較無効化
8. 比較履歴一覧表示

### Phase 2以降（自動テスト）

| テスト種別 | フレームワーク | 対象 |
|-----------|--------------|------|
| ユニットテスト | pytest | AnalysisPipeline・特徴量抽出・コサイン類似度計算 |
| 統合テスト | pytest + httpx | API エンドポイント（DBあり）|
| E2Eテスト | Playwright | 主要ユーザーフロー（アップロード→比較） |

---

## 技術的制約

### 環境要件

- **OS**: macOS（AppleシリコンまたはIntel）
- **最小メモリ**: 4GB（Docker割り当て）
- **必要ディスク容量**: 3GB（Dockerイメージ） + データ蓄積分
- **必要な外部依存**: Docker Desktop（最新版）

### パフォーマンス制約

- MediaPipeはGPU不要だがCPU推論のため、同時並行解析は非効率（MVP:直列処理）
- PostgreSQLの `FLOAT[]` 型はpgvectorのような専用ベクトルインデックスを持たないため、大規模比較では線形スキャンになる（MVPの規模では問題なし）

### 設計上の制約

- 解析パイプラインは `FastAPI BackgroundTasks` で実装するため、サーバー再起動時にキューが消える。Phase 2でCeleryに移行する
- 正面顔画像のみ対応。横顔・斜め顔はMediaPipeで検出されても特徴量の精度が低下する

---

## 依存関係管理

### バックエンド（requirements.txt）

| ライブラリ | 用途 | バージョン管理方針 |
|-----------|------|-------------------|
| fastapi | REST API | `==0.111.*` 固定 |
| uvicorn | ASGIサーバー | `==0.30.*` 固定 |
| sqlalchemy[asyncio] | ORM | `==2.0.*` 固定 |
| alembic | DBマイグレーション | `==1.13.*` 固定 |
| asyncpg | PostgreSQL非同期ドライバ | `==0.29.*` 固定 |
| mediapipe | 顔ランドマーク検出 | `==0.10.*` 固定 |
| opencv-python-headless | 画像処理 | `==4.9.*` 固定 |
| numpy | 数値計算 | `==1.26.*` 固定 |
| scipy | 統計計算 | `==1.13.*` 固定 |
| boto3 | MinIOクライアント | `>=1.34` 範囲指定 |
| pydantic | バリデーション | `==2.*` 固定 |
| python-multipart | ファイルアップロード対応 | `>=0.0.9` 範囲指定 |
| pillow | 画像バリデーション | `>=10.0` 範囲指定 |

### フロントエンド（package.json）

| ライブラリ | 用途 | バージョン管理方針 |
|-----------|------|-------------------|
| react / react-dom | UIフレームワーク | `^18.0.0` 固定メジャー |
| react-router-dom | ルーティング | `^6.0.0` 固定メジャー |
| @tanstack/react-query | サーバー状態管理 | `^5.0.0` 固定メジャー |
| axios | HTTPクライアント | `^1.0.0` 固定メジャー |
| tailwindcss | CSS | `^3.0.0` 固定メジャー |
| typescript | 型チェック | `^5.0.0` 固定メジャー |
| vite | ビルドツール | `^5.0.0` 固定メジャー |

---

## docker-compose.yml 設計

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, minio]
    environment:
      DATABASE_URL: postgresql+asyncpg://facegraph:facegraph@postgres:5432/facegraph
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
      MINIO_BUCKET: facegraph-images
    volumes:
      - ./backend:/app  # 開発時ホットリロード用（本番時は除去）

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
    environment:
      VITE_API_BASE_URL: http://localhost:8000

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: facegraph
      POSTGRES_USER: facegraph
      POSTGRES_PASSWORD: facegraph
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports: ["5432:5432"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"  # MinIO管理コンソール
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - miniodata:/data

volumes:
  pgdata:
  miniodata:
```
