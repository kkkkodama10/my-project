# タスクリスト: DBスキーマ・マイグレーション（5テーブル）

## 🚨 タスク完全完了の原則
全てのタスクを`[x]`にすること。未完了タスクを残したまま作業を終了しない。

---

## フェーズ1: SQLAlchemy ORM モデル作成

- [x] `backend/app/models/__init__.py` を作成する（Base + 全モデルエクスポート）
- [x] `backend/app/models/person.py` を作成する
- [x] `backend/app/models/image.py` を作成する（ImageStatus Enum含む）
- [x] `backend/app/models/feature.py` を作成する
- [x] `backend/app/models/person_feature.py` を作成する
- [x] `backend/app/models/comparison.py` を作成する（SimilarityMethod Enum含む）

## フェーズ2: alembic/env.py の target_metadata 更新

- [x] `backend/alembic/env.py` の `target_metadata` を `Base.metadata` に更新する

## フェーズ3: マイグレーションファイル生成・確認

- [x] `docker compose exec backend alembic revision --autogenerate -m "initial_schema"` を実行する
- [x] 生成されたマイグレーションファイルを確認・調整する
  - [x] Enum 型の CREATE/DROP が正しく含まれているか確認（downgradeに手動追加）
  - [x] UNIQUE 制約が含まれているか確認
  - [x] CASCADE DELETE が含まれているか確認

## フェーズ4: マイグレーション実行・動作確認

- [ ] `docker compose exec backend alembic upgrade head` を実行する
- [ ] psql で5テーブルが作成されたことを確認する
- [ ] `docker compose exec backend alembic downgrade base` でロールバックが正常に動作することを確認する
- [ ] `docker compose exec backend alembic upgrade head` で再度適用して確認する

## フェーズ5: session.py のインポート更新

- [x] `backend/app/db/session.py` に Base のインポートを追加する（Alembic autogenerate 用）

## フェーズ6: ドキュメント更新・振り返り

- [x] 実装後の振り返りを記録する

---

## 実装後の振り返り

### 実装完了日
2026-03-20

### 計画と実績の差分
- **計画通り**: 5テーブル（persons, images, features, person_features, comparisons）と3つのEnum型すべてを設計書通りに実装
- **差分なし**: SQLAlchemy 2.0 Mapped/mapped_column 形式、UUID PK、CASCADE DELETE、UNIQUE制約すべて計画通り
- **追加対応**: `alembic downgrade` の Enum DROP は autogenerate では生成されないため手動追加が必要（計画ドキュメントに明記済み）
- **Alembic設定**: `alembic.ini` のハードコードURL問題を発見し、env.py で `config.set_main_option` による上書き方式に変更

### 学んだこと
- **SQLAlchemy + PostgreSQL Enum**: autogenerate は upgrade で CREATE TYPE を生成するが、downgrade では DROP TYPE を生成しない。手動で `sa.Enum(name=...).drop(op.get_bind())` を追加する必要がある
- **Python予約語の回避**: `metadata` はSQLAlchemyの Base 属性名と衝突するため、`metadata_` として定義し `mapped_column("metadata", ...)` で実際のカラム名にマッピング
- **Dockerヘルスチェック**: `python:3.11-slim` には `curl` が含まれないため、`python -c "import urllib.request; ..."` に切り替えが必要
- **alembic.ini のURL管理**: 環境変数から注入するため env.py で上書きが必要。alembic.ini にはプレースホルダーを残す

### 次回への改善提案
- Alembic マイグレーション生成後の downgrade Enum DROP チェックをタスクリストに標準化する（今回は明記したが、次回も忘れずに）
- `python:3.11-slim` を使う場合のヘルスチェック方法をプロジェクトテンプレートに記載する
- 次のマイグレーション（カラム追加など）で `alembic revision --autogenerate` を再実行する際も同様に downgrade を確認すること
- downgrade の Enum DROP は `sa.Enum(...).drop(op.get_bind())` ではなく `op.execute("DROP TYPE IF EXISTS ...")` を使うこと（SQLAlchemy 2.0 async 環境では `op.get_bind()` が MissingGreenlet エラーになる）
- 全モデルの `DateTime` は `DateTime(timezone=True)` を明示すること（設計書の TIMESTAMPTZ 要件を満たすため）
