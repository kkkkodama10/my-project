# MS3: バックエンド改修 実装完了レポート

実装日: 2026-02-17

## 概要

Phase 2（ローカル版）のバックエンドを AWS デプロイ可能な構成に改修しました。
SQLite → PostgreSQL、インメモリ → Valkey、ローカルストレージ → S3 に対応しました。

## 実装した変更

### 1. 依存パッケージの追加 (`requirements.txt`)

```txt
# Phase 3: AWS 対応
asyncpg>=0.29.0          # PostgreSQL 非同期ドライバ
redis[hiredis]>=5.0.0     # Redis/Valkey クライアント
boto3>=1.34.0             # AWS SDK（S3 画像アップロード用）
```

### 2. 環境変数の追加 (`app/config.py`)

| 変数名 | 説明 | 例 |
|---|---|---|
| `DATABASE_URL` | DB接続URL（既存） | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | Valkey/Redis URL | `redis://host:6379/0` |
| `S3_BUCKET_NAME` | S3バケット名 | `quiz-app-assets-123456789012` |
| `CLOUDFRONT_DOMAIN` | CloudFront ドメイン | `dxxxxxxxxxx.cloudfront.net` |

### 3. ヘルスチェックエンドポイント (`app/routers/health.py`)

ALBのヘルスチェック用に `/api/health` エンドポイントを追加。

```python
@router.get("/health")
async def health_check():
    return {"status": "ok"}
```

### 4. Valkey WebSocket マネージャー (`app/ws/valkey_manager.py`)

複数 ECS タスク間で WebSocket メッセージをブロードキャストするため、
Valkey Pub/Sub を使った `ValkeyConnectionManager` を実装。

**主な機能:**
- Pub/Sub による全タスク間のメッセージ配信
- ローカルWebSocket接続管理
- delivered_at のValkey保存

**使用するチャンネル:**
- `event:{event_id}` - イベント内のブロードキャスト
- `delivered:{event_id}:{session_id}` - 配信時刻の記録

### 5. S3 画像アップロードサービス (`app/services/image_service.py`)

環境変数 `S3_BUCKET_NAME` の有無で自動的にS3/ローカルを切り替える。

```python
async def upload_image(file_data: bytes, filename: str, content_type: str) -> str:
    # S3_BUCKET_NAME が設定されていれば S3、なければローカル
    ...
```

**返却URL:**
- S3: `https://{CLOUDFRONT_DOMAIN}/images/{uuid}.jpg`
- ローカル: `/uploads/{uuid}.jpg`

### 6. Alembic マイグレーション設定

PostgreSQL マイグレーション用の Alembic 設定を追加。

**作成ファイル:**
- `alembic.ini` - Alembic設定
- `alembic/env.py` - 非同期対応の環境設定
- `alembic/script.py.mako` - マイグレーションテンプレート
- `alembic/README` - 実行手順

**マイグレーション実行:**
```bash
# マイグレーションファイル自動生成
alembic revision --autogenerate -m "initial schema"

# マイグレーション適用
alembic upgrade head
```

### 7. Dockerfile の更新

本番環境向けに以下を追加:

```dockerfile
# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

# マイグレーション自動実行 + workers=2
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## 動作モード

### ローカル開発モード（環境変数未設定）

| 項目 | 使用技術 |
|---|---|
| DB | SQLite (data/quiz.db) |
| WebSocket | インメモリ (manager.py) |
| 画像 | ローカル (uploads/) |

### AWS本番モード（環境変数設定）

| 項目 | 使用技術 |
|---|---|
| DB | PostgreSQL (RDS) |
| WebSocket | Valkey Pub/Sub (valkey_manager.py) |
| 画像 | S3 + CloudFront |

## 環境変数の設定例

### ローカル開発 (.env)

```bash
DATABASE_URL=sqlite+aiosqlite:///data/quiz.db
ADMIN_PASSWORD=secret
CORS_ORIGINS=http://localhost:5173
```

### AWS本番 (ECS タスク定義)

```bash
DATABASE_URL=postgresql+asyncpg://quizadmin:PASSWORD@quiz-app-db.xxx.ap-northeast-1.rds.amazonaws.com:5432/quizapp
REDIS_URL=redis://quiz-app-valkey.xxx.0001.apne1.cache.amazonaws.com:6379/0
S3_BUCKET_NAME=quiz-app-assets-123456789012
CLOUDFRONT_DOMAIN=dxxxxxxxxxx.cloudfront.net
CORS_ORIGINS=https://your-domain.com
ADMIN_PASSWORD=SecurePassword123
```

## データベース移行

SQLite → PostgreSQL への移行時の注意点:

| 項目 | SQLite | PostgreSQL | 対応 |
|---|---|---|---|
| ドライバ | aiosqlite | asyncpg | DATABASE_URL変更のみ |
| BOOLEAN型 | INTEGER (0/1) | BOOLEAN | SQLAlchemyが吸収 |
| 日時型 | TEXT | TIMESTAMP | Column型をDateTimeに統一済み |
| 自動採番 | ROWID | SERIAL | UUIDを使用（影響なし） |

## 次のステップ (MS4)

- [ ] Dockerイメージのビルド (`--platform linux/amd64`)
- [ ] ECR リポジトリの作成
- [ ] イメージのプッシュ

## 参考

- 詳細な手順: `docs/plan_phase_3.md`
- Alembic 実行方法: `backend/alembic/README`
