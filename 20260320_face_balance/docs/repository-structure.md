# リポジトリ構造定義書 (Repository Structure Document)

**バージョン**: 1.0
**作成日**: 2026-03-20
**プロジェクト**: FaceGraph

---

## プロジェクト全体構造

```
facegraph/
├── docker-compose.yml            # 4コンテナ定義
├── README.md
├── backend/                      # FastAPI (Python)
├── frontend/                     # React (TypeScript)
├── docs/                         # 永続ドキュメント
└── .steering/                    # 作業単位ドキュメント
```

---

## バックエンド構造（backend/）

```
backend/
├── Dockerfile
├── requirements.txt
├── config.yml                    # 解析手法設定（Strategyパターン）
├── alembic.ini                   # マイグレーション設定
├── alembic/
│   ├── env.py
│   └── versions/                 # マイグレーションファイル
│       └── 001_initial_schema.py
└── app/
    ├── main.py                   # FastAPIエントリポイント・ルーター登録・CORS設定
    ├── config.py                 # 環境変数・config.yml読み込み
    ├── models/                   # SQLAlchemy ORM定義
    │   ├── __init__.py
    │   ├── person.py             # Person モデル
    │   ├── image.py              # Image モデル・StatusEnum
    │   ├── feature.py            # Feature モデル
    │   ├── person_feature.py     # PersonFeature モデル
    │   └── comparison.py        # Comparison モデル・SimilarityMethodEnum
    ├── schemas/                  # Pydantic スキーマ（リクエスト/レスポンス）
    │   ├── __init__.py
    │   ├── person.py             # PersonCreate / PersonResponse
    │   ├── image.py              # ImageResponse
    │   └── comparison.py        # ComparisonRequest / ComparisonResponse
    ├── routers/                  # FastAPI ルーター（薄いHTTPレイヤー）
    │   ├── __init__.py
    │   ├── persons.py            # GET/POST/DELETE /api/persons
    │   ├── images.py             # POST/GET/DELETE /api/persons/{id}/images, /api/images/{id}
    │   └── comparisons.py       # POST/GET /api/comparisons
    ├── services/                 # ビジネスロジック
    │   ├── __init__.py
    │   ├── person_service.py     # 人物CRUD・連鎖削除
    │   ├── image_service.py      # 画像アップロード・削除・バックグラウンド起動
    │   ├── comparison_service.py # キャッシュ管理・類似度計算呼び出し
    │   └── analysis/            # 解析パイプライン（Strategyパターン）
    │       ├── __init__.py
    │       ├── pipeline.py       # AnalysisPipeline: パイプライン全体の統括
    │       ├── aggregator.py     # 複数画像の特徴量統合（平均方式）
    │       ├── detectors/        # Strategy: ランドマーク検出
    │       │   ├── __init__.py
    │       │   ├── base.py       # LandmarkDetector Protocol
    │       │   └── mediapipe.py  # MediaPipeLandmarkDetector
    │       ├── extractors/       # Strategy: 特徴量抽出
    │       │   ├── __init__.py
    │       │   ├── base.py       # FeatureExtractor Protocol
    │       │   └── distance_ratio.py  # DistanceRatioExtractor（IPD正規化）
    │       └── calculators/      # Strategy: 類似度計算
    │           ├── __init__.py
    │           ├── base.py       # SimilarityCalculator Protocol
    │           └── cosine.py     # CosineSimilarityCalculator
    ├── storage/
    │   ├── __init__.py
    │   └── minio_client.py       # MinIOアップロード・ダウンロード・削除
    └── db/
        ├── __init__.py
        └── session.py            # AsyncSession ファクトリ・依存注入
```

---

## フロントエンド構造（frontend/）

```
frontend/
├── Dockerfile
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── index.html
└── src/
    ├── main.tsx                  # React エントリポイント
    ├── App.tsx                   # ルーター定義（React Router）
    ├── api/
    │   ├── client.ts             # Axios インスタンス設定
    │   └── endpoints/            # エンドポイント別API関数
    │       ├── persons.ts        # persons API
    │       ├── images.ts         # images API
    │       └── comparisons.ts    # comparisons API
    ├── pages/                    # ページコンポーネント（ルート対応）
    │   ├── PersonList.tsx        # / : 人物一覧
    │   ├── PersonDetail.tsx      # /persons/:id : 人物詳細
    │   ├── Compare.tsx           # /compare : 比較画面
    │   └── CompareHistory.tsx    # /history : 比較履歴
    ├── components/               # 再利用可能なUIコンポーネント
    │   ├── PersonCard.tsx        # 人物カード（サムネイル・名前・枚数）
    │   ├── ImageUploader.tsx     # ドラッグ&ドロップ画像アップロード
    │   ├── ImageGallery.tsx      # 画像一覧（ステータスバッジ付き）
    │   ├── CompareSelector.tsx   # 人物A・B選択ドロップダウン
    │   ├── ScoreDisplay.tsx      # 類似度スコア表示（プログレスバー）
    │   └── StatusBadge.tsx       # 解析ステータスバッジ
    ├── hooks/                    # カスタムフック
    │   ├── usePersons.ts         # TanStack Query: 人物一覧・詳細取得
    │   ├── useImages.ts          # TanStack Query: 画像一覧・ポーリング
    │   └── useComparisons.ts     # TanStack Query: 比較・履歴取得
    └── types/
        └── api.ts                # API レスポンス型定義（TypeScript）
```

---

## ディレクトリ詳細

### backend/app/routers/

**役割**: HTTPリクエスト受付・Pydanticバリデーション・レスポンス整形のみ

**配置ファイル**:
- `persons.py`: `GET/POST/DELETE /api/persons` および `GET /api/persons/{id}`
- `images.py`: `POST/GET /api/persons/{id}/images` および `DELETE /api/images/{id}`
- `comparisons.py`: `POST/GET /api/comparisons`

**命名規則**: リソース名の複数形（`persons.py`, `images.py`, `comparisons.py`）

**依存関係**:
- 依存可能: `services/`, `schemas/`, `db/session.py`
- 依存禁止: `storage/`（直接MinIOアクセス禁止）、他の `routers/`

---

### backend/app/services/

**役割**: ビジネスロジック全体の実装。トランザクション管理を含む

**配置ファイル**:
- `person_service.py`: 人物CRUD・連鎖削除（images→features→comparisons）
- `image_service.py`: 画像アップロード（MinIO保存）・削除・BackgroundTasks起動
- `comparison_service.py`: キャッシュ検索・無効比較の再計算・upsert
- `analysis/pipeline.py`: 解析パイプライン全体の統括

**命名規則**: `{Resource}Service` 形式（`person_service.py`）

**依存関係**:
- 依存可能: `models/`, `storage/`, `db/`, `services/analysis/`
- 依存禁止: `routers/`（上位レイヤーへの逆依存禁止）

---

### backend/app/services/analysis/

**役割**: Strategyパターンによる解析パイプライン。手法差し替えを容易にする

**配置ファイル**:
- `pipeline.py`: `AnalysisPipeline` クラス。各Strategyを組み合わせてフローを実行
- `aggregator.py`: `recalculate_person_feature()` 平均方式統合
- `detectors/base.py`: `LandmarkDetector` Protocol定義
- `detectors/mediapipe.py`: `MediaPipeLandmarkDetector` 実装
- `extractors/base.py`: `FeatureExtractor` Protocol定義
- `extractors/distance_ratio.py`: `DistanceRatioExtractor` 実装（IPD正規化）
- `calculators/base.py`: `SimilarityCalculator` Protocol定義
- `calculators/cosine.py`: `CosineSimilarityCalculator` 実装

**命名規則**:
- Protocol: `{役割}.py` in `base.py`
- 実装: `{手法名}.py`（`mediapipe.py`, `distance_ratio.py`, `cosine.py`）

**依存関係**:
- 依存可能: `numpy`, `scipy`, `mediapipe`, `opencv`（外部ライブラリのみ）
- 依存禁止: `db/`, `storage/`（データアクセス禁止。`pipeline.py` 経由でDBアクセス）

---

### backend/app/models/

**役割**: SQLAlchemy ORM定義。テーブル構造とリレーションの定義

**配置ファイル**: テーブル名と1対1対応（`person.py`, `image.py`, `feature.py`, `person_feature.py`, `comparison.py`）

**命名規則**: テーブル名の単数形（`person.py` ← `persons` テーブル）

**依存関係**:
- 依存可能: SQLAlchemy基底クラスのみ
- 依存禁止: `services/`, `routers/`

---

### backend/app/schemas/

**役割**: Pydanticスキーマ。APIリクエスト/レスポンスの型定義と自動バリデーション

**配置ファイル**: リソース名と1対1対応（`person.py`, `image.py`, `comparison.py`）

**1ファイルに含めるクラス例**（`person.py`）:
```
PersonCreate      # リクエストボディ
PersonResponse    # レスポンス
PersonWithImages  # 画像付き詳細レスポンス
```

---

### frontend/src/pages/

**役割**: ルートと対応するページコンポーネント。URLとの1対1マッピング

| ファイル | ルート | 説明 |
|---------|--------|------|
| `PersonList.tsx` | `/` | 人物カード一覧・追加・削除 |
| `PersonDetail.tsx` | `/persons/:id` | 画像管理・解析ステータス |
| `Compare.tsx` | `/compare` | 2人選択・スコア表示 |
| `CompareHistory.tsx` | `/history` | 比較結果履歴一覧 |

**命名規則**: PascalCase（`PersonList.tsx`）

---

### frontend/src/components/

**役割**: 複数ページで再利用するUIコンポーネント

**命名規則**: PascalCase、用途が明確な名前（`ScoreDisplay.tsx`, `StatusBadge.tsx`）

**依存関係**:
- 依存可能: `hooks/`, `types/`, `api/`（必要最小限）
- 依存禁止: `pages/`（親コンポーネントへの逆依存禁止）

---

### frontend/src/hooks/

**役割**: TanStack Query を用いたサーバー状態取得・ポーリングのカスタムフック

**配置例**:
```typescript
// useImages.ts
export function useImageStatus(imageId: string) {
  return useQuery({
    queryKey: ['images', imageId],
    queryFn: () => getImage(imageId),
    refetchInterval: (data) =>
      data?.status === 'analyzed' ? false : 3000,  // 解析完了まで3秒ポーリング
  });
}
```

---

## ファイル配置規則

### バックエンド

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| ORM モデル | `app/models/` | `{resource_singular}.py` | `person.py` |
| Pydantic スキーマ | `app/schemas/` | `{resource_singular}.py` | `comparison.py` |
| ルーター | `app/routers/` | `{resource_plural}.py` | `persons.py` |
| サービス | `app/services/` | `{resource_singular}_service.py` | `image_service.py` |
| Strategy Protocol | `app/services/analysis/*/base.py` | `base.py` | `detectors/base.py` |
| Strategy 実装 | `app/services/analysis/*/` | `{手法名}.py` | `mediapipe.py` |
| マイグレーション | `alembic/versions/` | `{連番}_{説明}.py` | `001_initial_schema.py` |

### フロントエンド

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| ページ | `src/pages/` | `PascalCase.tsx` | `PersonList.tsx` |
| コンポーネント | `src/components/` | `PascalCase.tsx` | `ScoreDisplay.tsx` |
| カスタムフック | `src/hooks/` | `use{Name}.ts` | `usePersons.ts` |
| API関数 | `src/api/endpoints/` | `{resource}.ts` | `persons.ts` |
| 型定義 | `src/types/` | `{対象}.ts` | `api.ts` |

---

## 命名規則

### バックエンド（Python）

- **ファイル名**: snake_case（`person_service.py`）
- **クラス名**: PascalCase（`PersonService`, `DistanceRatioExtractor`）
- **関数名・変数名**: snake_case（`calculate_similarity`, `person_id`）
- **定数**: UPPER_SNAKE_CASE（`MODEL_VERSION = "mediapipe_v0.10"`）
- **Enum値**: snake_case（`image.status = "analyzed"`）

### フロントエンド（TypeScript）

- **ファイル名**: PascalCase（コンポーネント）、camelCase（フック・API関数）
- **コンポーネント名**: PascalCase（`PersonCard`）
- **フック名**: `use` プレフィックス + PascalCase（`usePersons`）
- **型名・インターフェース名**: PascalCase（`PersonResponse`, `ComparisonResult`）
- **定数**: UPPER_SNAKE_CASE（`API_BASE_URL`）

---

## 依存関係のルール

### バックエンドレイヤー間の依存

```
routers/
    ↓ (OK)
services/
    ↓ (OK)
services/analysis/   ←── config.yml（手法設定）
    ↓ (OK: 外部ライブラリのみ)
models/ + storage/ + db/
```

**禁止**:
- `models/` → `services/` （データレイヤーからサービスへの逆依存）
- `services/analysis/` → `db/` / `storage/` （解析ロジックはデータアクセス禁止）
- `routers/` 間の相互参照

### フロントエンドの依存ルール

```
pages/
    ↓ (OK)
components/   hooks/
    ↓ (OK)    ↓ (OK)
api/endpoints/
    ↓ (OK)
types/
```

**禁止**:
- `components/` → `pages/`
- `api/` → `hooks/`（逆依存）

---

## 特殊ディレクトリ

### .steering/（作業単位ドキュメント）

```
.steering/
└── 20260320-initial-setup/
    ├── requirements.md
    ├── design.md
    └── tasklist.md
```

**命名規則**: `YYYYMMDD-{task-name}` 形式（例: `20260321-backend-api`）

### docs/（永続ドキュメント）

```
docs/
├── ideas/
│   └── initial-requirements.md   # 壁打ち成果物
├── product-requirements.md
├── functional-design.md
├── architecture.md
├── repository-structure.md        # 本ドキュメント
├── development-guidelines.md
└── glossary.md
```

---

## 除外設定（.gitignore）

```
# Python
__pycache__/
*.pyc
.venv/
.env

# Node
node_modules/
dist/
.env.local

# Docker
*.log

# OS
.DS_Store

# IDE
.vscode/
.idea/
```

---

## スケーリング戦略

### 新しい解析手法の追加（Strategyパターン）

例: dlibランドマーク検出の追加

```
app/services/analysis/detectors/
├── base.py          # 変更不要
├── mediapipe.py     # 変更不要
└── dlib.py          # 新規追加
```

`config.yml` で `landmark_detector: "dlib"` に切り替えるだけで有効化。

### 新しいAPIリソースの追加

1. `models/{resource}.py` を追加
2. `schemas/{resource}.py` を追加
3. `services/{resource}_service.py` を追加
4. `routers/{resource}s.py` を追加
5. `main.py` でルーターを登録
6. `alembic/versions/` にマイグレーションを追加

### ファイルサイズの目安

- 1ファイル300行以下を推奨
- サービスクラスが大きくなった場合はメソッド単位でモジュール分割を検討
