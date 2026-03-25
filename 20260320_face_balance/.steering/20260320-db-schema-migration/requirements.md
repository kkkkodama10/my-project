# 要求内容

## 概要

FaceGraph の5テーブル（persons / images / features / person_features / comparisons）の SQLAlchemy ORM モデルと Alembic マイグレーションを実装する。`alembic upgrade head` でテーブルが作成されることを確認する。

## 背景

Docker Compose 環境は整備済み。次にバックエンドAPIの実装土台となるデータモデルを確定させる必要がある。ORM モデルは後続の人物管理API・解析パイプライン・比較APIの全てで使用される。

## 実装対象

### 1. SQLAlchemy ORM モデル（5ファイル）
- `backend/app/models/person.py` — persons テーブル
- `backend/app/models/image.py` — images テーブル（ImageStatus Enum含む）
- `backend/app/models/feature.py` — features テーブル
- `backend/app/models/person_feature.py` — person_features テーブル
- `backend/app/models/comparison.py` — comparisons テーブル（SimilarityMethod Enum含む）
- `backend/app/models/__init__.py` — Base・全モデルのエクスポート

### 2. Alembic マイグレーション
- `backend/alembic/versions/001_initial_schema.py` — 5テーブルを作成する初回マイグレーション
- `backend/alembic/env.py` の `target_metadata` を実際の Base.metadata に更新

## 受け入れ条件

- [ ] `docker compose exec backend alembic upgrade head` がエラーなく完了する
- [ ] PostgreSQL に5テーブルが作成される（psql で確認）
- [ ] `docker compose exec backend alembic downgrade base` でテーブルが全て削除される（ロールバック確認）
- [ ] `alembic current` でリビジョンが正しく表示される

## スコープ外

- MinIO バケット作成（ステップ3で実施）
- 人物管理APIの実装（ステップ4以降）
- seeder・テストデータの投入

## 参照ドキュメント

- `docs/functional-design.md` — テーブル定義・ER図
- `docs/architecture.md` — 技術スタック（SQLAlchemy 2.0 async）
