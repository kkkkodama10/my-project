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


## 4. 機能要件 (CRUD)・画面仕様

### 一覧画面（GET /）
- 全ペットを `created_at` 降順で表示。
- ページ下部に新規登録フォームを配置。
- UI要素:
  - 「新規登録」ボタン（画面上部または下部）
  - ペット一覧テーブル（各行に「詳細」「編集」「削除」ボタン）
- レイアウト例:
  - テーブル: 名前／種別／性別／登録日／操作（詳細・編集・削除）
  - 新規登録フォーム: ページ下部に配置

### 登録画面（POST /）
- フォーム項目: `name` (必須 50文字以内), `species` (必須 30文字以内), `sex` (select: male/female/unknown)
- UI要素:
  - 入力フォーム（name, species, sex）
  - 「登録」ボタン
- ラベル例:
  - 名前（必須）
  - 種別（必須）
  - 性別（必須: 男性/女性/不明）
- プレースホルダー例:
  - 名前: "例）ポチ"
  - 種別: "例）イヌ"
- 成功時: `/` にリダイレクト & Flash メッセージ

### 詳細画面（GET /pets/<id>）
- エンティティ詳細を表示。
- UI要素:
  - ペット情報表示
  - 「編集」「削除」「戻る」ボタン

### 編集画面（GET+POST /pets/<id>/edit）
- プリフィルされたフォーム。バリデーションは登録と同じ。
- UI要素:
  - プリフィル済みフォーム
  - 「更新」ボタン
  - 「戻る」ボタン

### 削除（POST /pets/<id>/delete）
- CSRF 保護 & 確認。成功後 `/` へ。
- UI要素:
  - 削除確認ダイアログまたは画面
  - 「削除」「キャンセル」ボタン

---

## 5. エラーハンドリング仕様

- バリデーションエラー時:
  - 各フォーム項目下に赤字でエラーメッセージを表示
  - 例: "名前は必須です（50文字以内）"
- DBやAPI通信エラー時:
  - 画面上部にアラート（赤色）でエラーメッセージを表示
  - 例: "登録に失敗しました。再度お試しください。"

---

## 6. API仕様・データ構造例

### エンドポイント一覧
- GET    /pets         : ペット一覧取得
- POST   /pets         : ペット新規登録
- GET    /pets/<id>    : ペット詳細取得
- PUT    /pets/<id>    : ペット情報更新
- DELETE /pets/<id>    : ペット削除

### リクエスト/レスポンス例

- 新規登録（POST /pets）
  - リクエスト:
    ```json
    {
      "name": "ポチ",
      "species": "イヌ",
      "sex": "male"
    }
    ```
  - レスポンス:
    ```json
    {
      "id": 1,
      "name": "ポチ",
      "species": "イヌ",
      "sex": "male",
      "created_at": "2025-07-12T12:34:56+09:00",
      "updated_at": "2025-07-12T12:34:56+09:00"
    }
    ```

- バリデーションエラー時:
  - レスポンス:
    ```json
    {
      "error": "nameは必須です"
    }
    ```

---

## 7. 画面遷移図（例）

```
[一覧] --新規登録--> [登録フォーム]
  |                     |
  |--詳細--> [詳細画面]  |
  |                     |
  |--編集--> [編集画面]  |
  |                     |
  |--削除--> [削除確認]  |
```

---

---


## 8. データモデル

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
