# FaceGraph

顔類似度定量分析アプリケーション。子供が両親のどちらに似ているかを、顔パーツの幾何学的特徴量に基づいて定量的にスコア化する。

## セットアップ

### 前提条件

- Docker Desktop（最新版）

### 起動

```bash
docker compose up --build
```

初回はイメージのビルド・ダウンロードに数分かかります。

### アクセス先

| サービス | URL | 説明 |
|---------|-----|------|
| フロントエンド | http://localhost:3000 | React UI |
| バックエンド API | http://localhost:8000/docs | Swagger UI |
| MinIO コンソール | http://localhost:9001 | ストレージ管理（minioadmin / minioadmin） |

### DBマイグレーション（初回・スキーマ変更時）

```bash
docker compose exec backend alembic upgrade head
```

### 停止

```bash
# コンテナのみ停止（データ保持）
docker compose down

# コンテナ＋データ削除（リセット）
docker compose down -v
```

## 開発

詳細は `docs/` を参照してください。

| ドキュメント | 内容 |
|---|---|
| `docs/product-requirements.md` | プロダクト要求定義書 |
| `docs/functional-design.md` | 機能設計書 |
| `docs/architecture.md` | アーキテクチャ設計書 |
| `docs/repository-structure.md` | リポジトリ構造定義書 |
| `docs/development-guidelines.md` | 開発ガイドライン |
| `docs/glossary.md` | 用語集 |
