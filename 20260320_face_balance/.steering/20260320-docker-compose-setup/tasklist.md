# タスクリスト: Docker Compose環境構築

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

---

## フェーズ1: docker-compose.yml 作成

- [x] `docker-compose.yml` を作成する
  - [x] 4サービス定義（backend / frontend / postgres / minio）
  - [x] depends_on で起動順序を設定
  - [x] 環境変数を設定
  - [x] pgdata・miniodata ボリュームを定義

## フェーズ2: バックエンド骨格作成

- [x] `backend/Dockerfile` を作成する
- [x] `backend/requirements.txt` を作成する
- [x] `backend/config.yml` を作成する
- [x] `backend/app/__init__.py` を作成する
- [x] `backend/app/main.py` を作成する（FastAPI初期化・CORS・/health）
- [x] `backend/app/config.py` を作成する（pydantic-settings）
- [x] `backend/app/db/__init__.py` を作成する
- [x] `backend/app/db/session.py` を作成する（AsyncSession）

## フェーズ3: Alembic 初期設定

- [x] `backend/alembic.ini` を作成する
- [x] `backend/alembic/env.py` を作成する（asyncpg対応）
- [x] `backend/alembic/script.py.mako` を作成する
- [x] `backend/alembic/versions/` ディレクトリを作成する

## フェーズ4: フロントエンド骨格作成

- [x] `frontend/Dockerfile` を作成する
- [x] `frontend/package.json` を作成する
- [x] `frontend/tsconfig.json` を作成する
- [x] `frontend/vite.config.ts` を作成する
- [x] `frontend/index.html` を作成する
- [x] `frontend/src/main.tsx` を作成する
- [x] `frontend/src/App.tsx` を作成する（最小表示）

## フェーズ5: 動作確認

- [x] `docker compose build` でビルドエラーがないことを確認する
- [x] `http://localhost:8000/health` レスポンスを確認する（`{"status":"ok","db":"ok"}`）
- [x] `http://localhost:3000` アクセスを確認する

## フェーズ6: ドキュメント更新

- [x] `README.md` にセットアップ手順を記載する
- [x] 実装後の振り返りを記録する

---

## 実装後の振り返り

### 実装完了日
2026-03-20

### 計画と実績の差分

**計画と異なった点**:
- ヘルスチェックに `curl` を使う予定だったが、`python:3.11-slim` に `curl` が含まれていないため、`python -c "urllib.request.urlopen(...)"` に変更
- `backend` ヘルスチェック追加により `frontend` の `depends_on` を `condition: service_healthy` に格上げできた（設計書より品質が上がった）
- 別プロジェクト（quiz-app-backend）がポート8000を使用していたため、起動前に停止が必要だった

**新たに必要になったタスク**:
- ヘルスチェック方式の変更（curl → Python urllib）

### 学んだこと

**技術的な学び**:
- `python:3.11-slim` は最小構成のため `curl` 等のユーティリティが含まれていない。ヘルスチェックは Python 標準ライブラリで代用するか、Dockerfile で `curl` を `apt-get install` する
- `alembic.ini` の `sqlalchemy.url` は `env.py` で `config.set_main_option()` により上書きできる。環境変数との二重管理を避けるためこのパターンが有効
- Docker Compose の `depends_on` は `condition: service_healthy` を使うと信頼性が上がる

### 次回への改善提案
- 次ステップ（DBスキーマ・マイグレーション）では `alembic/versions/` に初回マイグレーションファイルを追加する
- `backend` Dockerfile に `HEALTHCHECK` 命令を追加することも検討（docker-compose.yml 外での実行時にも有効）
