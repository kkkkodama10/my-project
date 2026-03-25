# 要求内容

## 概要

FaceGraph MVPの基盤となる Docker Compose 環境を構築する。`docker compose up --build` の1コマンドで4コンテナ（frontend / backend / postgres / minio）が起動し、ブラウザからアクセスできる状態を作る。

## 背景

FaceGraph は Docker Compose で動作するローカルアプリケーション。後続の全機能実装（人物管理API・解析パイプライン・フロントエンド）はこの環境が土台となる。最初にインフラを確立することで、以降の実装を効率化する。

## 実装対象の機能

### 1. docker-compose.yml の構築
- 4コンテナ定義（backend / frontend / postgres / minio）
- コンテナ間のネットワーク・依存関係設定
- ボリューム定義（pgdata / miniodata）
- 環境変数設定

### 2. バックエンド Dockerfile・骨格実装
- Python 3.11 + FastAPI の Dockerfile
- ヘルスチェックエンドポイント（`GET /health`）
- requirements.txt（MVP全依存関係）
- config.py（環境変数読み込み）
- config.yml（解析手法設定）

### 3. フロントエンド Dockerfile・骨格実装
- Node.js 20 + React + Vite の Dockerfile
- 起動確認用の最小 App.tsx

### 4. Alembic マイグレーション初期設定
- alembic.ini・env.py の設定
- マイグレーション実行確認

## 受け入れ条件

### Docker Compose 起動
- [ ] `docker compose up --build` で4コンテナが全て起動する
- [ ] ブラウザで `http://localhost:3000` にアクセスできる
- [ ] ブラウザで `http://localhost:8000/docs` (Swagger UI) にアクセスできる
- [ ] ブラウザで `http://localhost:9001` (MinIO Console) にアクセスできる

### バックエンド
- [ ] `GET /health` が `{"status": "ok"}` を返す

## スコープ外

- DBテーブル定義・マイグレーション（ステップ2で実施）
- MinIOバケット作成（ステップ3で実施）
- 人物管理APIの実装（ステップ4以降）
- フロントエンドの画面実装（ステップ9で実施）

## 参照ドキュメント

- `docs/architecture.md` - docker-compose.yml 設計・依存ライブラリ一覧
- `docs/repository-structure.md` - ディレクトリ構造
