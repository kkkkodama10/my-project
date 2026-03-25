# 開発ガイドライン (Development Guidelines)

**バージョン**: 1.0
**作成日**: 2026-03-20
**プロジェクト**: FaceGraph

---

## コーディング規約

### 命名規則

#### バックエンド（Python）

```python
# ✅ 良い例
person_id: UUID               # 変数: snake_case
async def get_person_by_id()  # 関数: snake_case・動詞始まり
class PersonService:          # クラス: PascalCase
MODEL_VERSION = "mediapipe_v0.10"  # 定数: UPPER_SNAKE_CASE
is_valid: bool                # Boolean: is_ / has_ プレフィックス

# ❌ 悪い例
pid: UUID
async def person():
class personservice:
modelVersion = "mediapipe"
valid: bool
```

**原則**:
- 変数・関数: snake_case
- クラス: PascalCase
- 定数: UPPER_SNAKE_CASE
- Boolean: `is_` / `has_` / `can_` プレフィックス
- Enum値: snake_case（`"analyzed"`, `"cosine"`）

#### フロントエンド（TypeScript）

```typescript
// ✅ 良い例
const personId: string             // 変数: camelCase
function fetchPersonList()         // 関数: camelCase・動詞始まり
class PersonService {}             // クラス: PascalCase
const API_BASE_URL = "..."         // 定数: UPPER_SNAKE_CASE
interface PersonResponse {}        // 型: PascalCase
type SimilarityMethod = "cosine"   // 型エイリアス: PascalCase
const isAnalyzed: boolean          // Boolean: is / has プレフィックス
function usePersons()              // カスタムフック: use プレフィックス

// ❌ 悪い例
const pid: string
function person()
const apiBaseUrl = "..."
```

---

### コードフォーマット

#### バックエンド（Python）

- **インデント**: 4スペース（Python標準）
- **行の長さ**: 最大100文字
- **フォーマッター**: `black`（設定: `line-length = 100`）
- **Linter**: `ruff`

```python
# ✅ 良い例: 型ヒント必須
async def compare_persons(
    person_a_id: UUID,
    person_b_id: UUID,
    db: AsyncSession,
) -> ComparisonResponse:
    ...
```

#### フロントエンド（TypeScript）

- **インデント**: 2スペース
- **行の長さ**: 最大100文字
- **フォーマッター**: `prettier`
- **Linter**: `eslint`（TypeScript ESLint）

```typescript
// ✅ 良い例: 型明示
async function fetchComparison(
  personAId: string,
  personBId: string,
): Promise<ComparisonResponse> {
  return client.post('/api/comparisons', { personAId, personBId });
}
```

---

### コメント規約

**バックエンド（Python）**:
```python
# ✅ 良い例: なぜそうするかを説明
# IPDで正規化することで、顔のサイズ（撮影距離）の影響を除去する
normalized = distance / ipd

# ❌ 悪い例: コードを読めば分かる
# IPDで割る
normalized = distance / ipd
```

**複雑なアルゴリズムにのみdocstring**:
```python
async def recalculate_person_feature(person_id: UUID, db: AsyncSession) -> None:
    """
    複数画像の特徴量ベクトルを平均して person_features を再統合する。

    画像の追加・削除のたびに呼び出す。analyzed 状態の画像のみ対象とする。
    """
```

**フロントエンド（TypeScript）**: シンプルな関数にコメント不要。複雑なロジックにのみ追加。

---

### エラーハンドリング

#### バックエンド

```python
# ✅ 良い例: HTTPException でステータスコードを明示
from fastapi import HTTPException

async def get_person(person_id: UUID, db: AsyncSession) -> Person:
    person = await db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="人物が見つかりません")
    return person

# 解析パイプライン内のエラー: status = "error" + metadata に記録
async def process_image(image_id: UUID) -> None:
    try:
        ...
    except Exception as e:
        image.status = "error"
        image.metadata["error"] = str(e)
        await db.commit()
        return  # 上位に伝播させない（バックグラウンドタスクのため）
```

#### フロントエンド

```typescript
// ✅ 良い例: TanStack Query の onError でトースト表示
const mutation = useMutation({
  mutationFn: uploadImage,
  onError: (error: AxiosError) => {
    const message = error.response?.data?.detail ?? 'アップロードに失敗しました';
    showToast({ type: 'error', message });
  },
});
```

---

## Git運用ルール

### ブランチ戦略

MVPはシングル開発者前提のため、シンプルな構成とする。

```
main
  └─ feature/{機能名}     # 新機能開発
  └─ fix/{修正内容}       # バグ修正
  └─ chore/{作業内容}     # 設定・ドキュメント等
```

**フロー**:
1. `main` からブランチを切る
2. 機能実装・コミット
3. `main` へマージ（セルフレビュー後）

**命名例**:
```
feature/backend-person-api
feature/frontend-compare-screen
fix/image-status-polling
chore/docker-compose-setup
```

---

### コミットメッセージ規約

**フォーマット（Conventional Commits）**:
```
<type>(<scope>): <subject>

<body>（任意）
```

**Type**:

| type | 用途 |
|------|------|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `docs` | ドキュメント |
| `style` | コードフォーマット（動作に影響なし） |
| `refactor` | リファクタリング |
| `test` | テスト追加・修正 |
| `chore` | ビルド・設定・依存関係 |

**Scope例**: `backend`, `frontend`, `db`, `pipeline`, `docker`

**例**:
```
feat(backend): 人物管理APIを実装

POST/GET/DELETE /api/persons エンドポイントを追加。
連鎖削除（images→features→comparisons）をTransactionで実装。

feat(pipeline): MediaPipe顔解析パイプラインを実装

fix(frontend): 画像ステータスのポーリングが停止しない問題を修正

解析完了（analyzed）でポーリングを停止するように修正。
TanStack QueryのrefetchIntervalを条件分岐で制御。

chore(docker): docker-compose.yml初期設定
```

---

### プルリクエストプロセス

**作成前のセルフチェック**:
- [ ] `docker compose up` でビルドが通る
- [ ] 実装した機能が動作することを手動確認
- [ ] 不要なデバッグコード・コンソールログが残っていない
- [ ] 環境変数・秘密情報がコードにハードコードされていない

**PRテンプレート**:
```markdown
## 概要
[変更内容の簡潔な説明]

## 変更内容
- [変更点1]
- [変更点2]

## 動作確認
- [ ] [確認項目1]
- [ ] [確認項目2]

## 関連ドキュメント
- 関連する .steering/ ファイル: `.steering/YYYYMMDD-{task-name}/`
```

---

## テスト戦略

### MVP段階（手動テスト）

MVP完了基準に基づいて手動で動作確認する。各機能の実装完了時に以下を確認:

| 確認項目 | 手順 |
|---------|------|
| 人物作成・一覧 | UIから人物を追加し、カードが表示されること |
| 画像アップロード（正常） | 正面顔1名の画像をアップロードし `analyzed` になること |
| 画像バリデーション | 顔なし・複数顔の画像でエラーメッセージが表示されること |
| 類似度比較 | 2人を選択してスコア（0〜100%）が表示されること |
| キャッシュ動作 | 同じペアを再比較し即座に結果が返ること |
| 無効化動作 | 画像削除後に比較履歴が「無効」になること |
| 比較履歴 | 過去の比較が一覧表示されること |

### Phase 2以降（自動テスト）

**テストピラミッド方針**:

```
        [E2E: Playwright]
       ↑ ユーザーシナリオ全体
      [統合テスト: pytest + httpx]
     ↑ APIエンドポイント・DB連携
    [ユニットテスト: pytest]
   ↑ 解析アルゴリズム・ビジネスロジック
```

**優先的にテストする対象**（Phase 2以降）:
1. `DistanceRatioExtractor`: 特徴量抽出計算の正確性
2. `CosineSimilarityCalculator`: スコア変換（-1〜1 → 0〜1）
3. `recalculate_person_feature`: 平均統合ロジック
4. `invalidate_comparisons`: 無効化の整合性
5. APIエンドポイント（人物CRUD・比較フロー）

**テスト命名規則**:
```python
# パターン: test_{対象}_{条件}_{期待結果}
def test_cosine_calculator_identical_vectors_returns_one():
def test_cosine_calculator_opposite_vectors_returns_zero():
def test_upload_image_no_face_sets_error_status():
def test_upload_image_multiple_faces_sets_error_status():
```

---

## 開発環境セットアップ

### 必要なツール

| ツール | バージョン | インストール方法 |
|--------|-----------|-----------------|
| Docker Desktop | 最新 | [公式サイト](https://www.docker.com/products/docker-desktop/) |
| Git | 2.x | `brew install git` |
| （任意）TablePlus / DBeaver | 最新 | PostgreSQL直接確認用 |
| （任意）MinIO Console | — | `http://localhost:9001` でアクセス |

### セットアップ手順

```bash
# 1. リポジトリのクローン
git clone <URL>
cd facegraph

# 2. コンテナ起動（初回はイメージビルドが発生）
docker compose up --build

# 3. ブラウザアクセス
open http://localhost:3000          # フロントエンド
open http://localhost:8000/docs     # FastAPI Swagger UI
open http://localhost:9001          # MinIO管理コンソール
#   （MinIO: minioadmin / minioadmin）

# 4. DBマイグレーション（初回のみ）
docker compose exec backend alembic upgrade head
```

### 開発時の便利コマンド

```bash
# コンテナ起動（バックグラウンド）
docker compose up -d

# バックエンドログ確認
docker compose logs -f backend

# バックエンドのみ再起動（コード変更時）
docker compose restart backend

# DBマイグレーション実行
docker compose exec backend alembic upgrade head

# DBマイグレーション新規作成
docker compose exec backend alembic revision --autogenerate -m "add_xxx_column"

# バックエンドの依存関係更新
docker compose exec backend pip install -r requirements.txt

# 全コンテナ停止・削除（ボリュームは保持）
docker compose down

# 全コンテナ + ボリューム削除（データリセット）
docker compose down -v
```

### 推奨 VS Code 拡張

| 拡張 | 用途 |
|------|------|
| Python (ms-python) | Python言語サポート |
| Pylance | Python型チェック |
| ESLint | TypeScript Lint |
| Prettier | コードフォーマット |
| Docker | Dockerfile・Compose編集 |
| Thunder Client | API手動テスト（Postman代替） |

---

## コードレビュー基準

### レビューポイント（セルフレビュー）

**機能性**:
- [ ] PRDの受け入れ条件を満たしているか
- [ ] エラーケース（顔なし・複数顔・解析未完了等）が処理されているか
- [ ] 比較結果の無効化が正しくトリガーされるか

**可読性**:
- [ ] 命名規則に従っているか
- [ ] 複雑なアルゴリズムにコメントがあるか

**保守性**:
- [ ] Strategyパターンのプロトコルに従っているか（新手法追加時）
- [ ] `routers/` にビジネスロジックが混入していないか
- [ ] `services/analysis/` がDB/HTTPアクセスをしていないか

**セキュリティ**:
- [ ] 環境変数・認証情報がコードにハードコードされていないか
- [ ] ファイルタイプ・サイズバリデーションが漏れていないか

### レビューコメントの書き方

```markdown
## ✅ 良い例
[推奨] `recalculate_person_feature` はトランザクション外で呼んでいますが、
特徴量の保存に失敗した場合に不整合が生じる可能性があります。
`async with db.begin()` でラップすることを検討してください。

## ❌ 悪い例
ここはダメです。直してください。
```

**優先度プレフィックス**:
- `[必須]`: マージ前に修正必須
- `[推奨]`: 可能なら修正
- `[提案]`: 将来の改善案（今は対応不要）
- `[質問]`: 理解のための確認

---

## 実装時の注意事項

### Strategyパターンの拡張方法

新しい解析手法（例: dlib）を追加する場合:

```python
# 1. Protocolを実装するクラスを作成
# app/services/analysis/detectors/dlib.py
class DlibLandmarkDetector:
    def detect(self, image: np.ndarray) -> LandmarkResult:
        ...

# 2. config.ymlを変更するだけで切り替え可能
# landmark_detector: "dlib"

# 3. pipeline.py の factory 関数に追加
def build_detector(config: Config) -> LandmarkDetector:
    if config.landmark_detector == "mediapipe":
        return MediaPipeLandmarkDetector()
    if config.landmark_detector == "dlib":
        return DlibLandmarkDetector()
    raise ValueError(f"Unknown detector: {config.landmark_detector}")
```

### 比較無効化の整合性

画像の追加・削除時は、必ず以下の順番でDBを更新する:

```
1. features 保存/削除
2. person_features 再統合
3. comparisons.is_valid = False（関連レコード）
4. images.status 更新
```

これらは1トランザクションで実行し、途中失敗時のデータ不整合を防ぐ。

### ポーリング実装（フロントエンド）

TanStack Query で解析ステータスをポーリングする:

```typescript
// ✅ 解析完了でポーリング停止
useQuery({
  queryKey: ['image', imageId],
  queryFn: () => getImage(imageId),
  refetchInterval: (data) => {
    if (data?.status === 'analyzed' || data?.status === 'error') return false;
    return 3000; // 3秒ごとにポーリング
  },
});
```
