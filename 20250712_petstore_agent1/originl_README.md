# ペットカタログ設計指示書

> 本ドキュメントは **GitHub Copilot Agent** が開発を自動化するための設計指示書です。アーキテクチャ詳細は `/web/docs/architecture.md` を参照してください。

---

## 0. 前提環境

* 開発端末には **pyenv** & **virtualenv** がインストール済み。
* 空リポジトリが GitHub 上に作成済み（main ブランチ）。

---

## 1. プロジェクト目的

最小構成の CRUD Web アプリ **「ペットカタログ」** を開発し、登録済みのペットを Create / Read / Update / Delete できることを目指す。

---

## 2. 技術スタック

* **言語 / ランタイム**: Python 3.11（pyenv でインストール）
* **バックエンド**: Flask

  * Flask‑SQLAlchemy / Flask‑Migrate / Flask‑WTF
* **データベース**: PostgreSQL 15（Docker イメージ）
* **テンプレート**: Jinja2 (サーバーサイドレンダリングのみ)
* **スタイル**: Bootstrap 5 (CDN)
* **開発ツール**: `pip` + `pyproject.toml`（`poetry` または `pip‑tools` を選択）
  Lint: **ruff** / **black** / **mypy(strict)**
  テスト: **pytest** / **pytest‑flask**
* **構築環境**: docker, docker-compose 

---

## 3. 環境構築 & 追加要件

1. **Python 仮想環境**

   ```bash
   pyenv install 3.11.x
   pyenv virtualenv 3.11.x pet-catalog
   echo "pet-catalog" > .python-version
   ```
2. **依存ライブラリ**: Copilot Agent が `pyproject.toml` に記述し自動インストール。
3. **Postgres**: `docker-compose.yml` に `postgres:15` サービス (ボリューム: `./pgdata`).
4. **Git 運用**: プロジェクト実行前にブランチを作成。mainへのマージはしてはいけません。タスク完了ごとにコミット。主要マイルストーン後のコミットメッセージ例:

   * `feat: bootstrap project skeleton`
   * `feat: add pet model & migration`
   * `feat: implement CRUD routes`
   * `test: add CRUD flow tests`
   * `docs: add README`
   * `fix: lint & type errors`
5. **自律的エラーハンドリング**

   * `ruff`, `black --check`, `mypy`, `pytest` が失敗した場合、Agent が自動修正して再実行。
   * `docker compose up` で例外が発生した場合も同様にリトライ。

---

## 4. 機能要件 (CRUD)

* **一覧 (GET /)**
  全ペットを `created_at` 降順で表示。ページ下部に新規登録フォームを配置。
* **登録 (POST /)**

  * フォーム項目: `name` (必須 50文字以内), `species` (必須 30文字以内), `sex` (select: male/female/unknown)
  * 成功時: `/` にリダイレクト & Flash メッセージ
* **詳細 (GET /pets/<id>)**
  エンティティ詳細を表示。Edit / Delete / Back ボタン。
* **編集 (GET+POST /pets/<id>/edit)**
  プリフィルされたフォーム。バリデーションは登録と同じ。
* **削除 (POST /pets/<id>/delete)**
  CSRF 保護 & 確認。成功後 `/` へ。

---

## 5. データモデル

| カラム          | 型 / 制約                                                 | 説明               |
| ------------ | ------------------------------------------------------ | ---------------- |
| `id`         | SERIAL PK                                              | 自動採番             |
| `name`       | VARCHAR(50) NOT NULL                                   | 名前               |
| `species`    | VARCHAR(30) NOT NULL                                   | 種別               |
| `sex`        | ENUM(`male`,`female`,`unknown`) NOT NULL               | 性別               |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT now()                 | 登録日時 (immutable) |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT now() ON UPDATE now() | 更新日時             |

---

## 6. Copilot Agent タスク & コミットプラン

| #  | タスク                                       | 期待コミットメッセージ例                       |
| -- | ----------------------------------------- | ---------------------------------- |
| 0  | 開発用ブランチを作成 (`feature/initial-setup` など) | `chore: create development branch`            |
| 1  | Python venv 作成 & activate                 | `chore: create python virtualenv`  |
| 2  | 雛形 (ディレクトリ/空ファイル) 生成                      | `feat: bootstrap project skeleton` |
| 3  | `pyproject.toml` 記述 & 依存インストール            | `feat: add dependencies & tooling` |
| 4  | Postgres `docker-compose.yml` 作成          | `chore: add postgres service`      |
| 5  | モデル & マイグレーション                            | `feat: add pet model & migration`  |
| 6  | CRUD ルート & フォーム & テンプレート実装                | `feat: implement CRUD routes`      |
| 7  | テスト実装                                     | `test: add CRUD flow tests`        |
| 8  | Docker 動作確認 (`docker compose up --build`) | `chore: verify docker run`         |
| 9  | README & Makefile 追加                      | `docs: add README and Makefile`    |
| 10 | Lint / type / test グリーン化                  | `fix: lint & type errors`          |
|

---

## 9. 受け入れ基準

* `docker compose up` で **[http://localhost:5000](http://localhost:5000)** から CRUD 操作が可能。
* コミット履歴が要件ごとに分かれ、メッセージが意味を持つ。
* `ruff`, `black --check`, `mypy`, `pytest` すべて成功。
* README にセットアップ手順と運用方法が記載される。

---

> 本設計指示書に従い、自動化タスクを実行してください。

