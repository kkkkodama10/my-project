# リポジトリ構造定義書

## ディレクトリ構成

```
auto-diary/
├── CLAUDE.md                  # Claude Code向けプロジェクトメモリ
├── README.md                  # プロジェクト概要（人間向け）
├── .env                       # 認証情報（Git管理外）
├── .env.example               # .envのテンプレート（Git管理対象）
├── .gitignore
├── requirements.txt           # Pythonパッケージ依存定義
│
├── docs/                      # 永続的ドキュメント
│   ├── product-requirements.md    # プロダクト要求定義書
│   ├── functional-design.md       # 機能設計書
│   ├── architecture.md            # 技術仕様書
│   ├── repository-structure.md    # このファイル
│   ├── development-guidelines.md  # 開発ガイドライン
│   └── glossary.md                # ユビキタス言語定義
│
├── .steering/                 # 作業単位のドキュメント（Git管理外）
│   └── YYYYMMDD-タイトル/
│       ├── requirements.md    # 作業の要求内容
│       ├── design.md          # 変更内容の設計
│       └── tasklist.md        # チェックボックス形式のタスクリスト
│
├── src/                       # アプリケーションコード
│   ├── __init__.py
│   ├── main.py                # エントリポイント・オーケストレーション
│   ├── config.py              # .env読み込みとバリデーション
│   ├── garmin_client.py       # Garmin Connectデータ取得
│   ├── diary_generator.py     # Claude APIで日記生成
│   └── notion_client.py       # Notion投稿（MVP後に実装）
│
├── prompts/
│   └── diary_prompt.txt       # 日記生成プロンプトテンプレート
│
├── logs/
│   └── .gitkeep               # ディレクトリをGit管理するためのプレースホルダ
│
└── tests/
    ├── test_garmin.py
    ├── test_generator.py
    └── test_notion.py
```

## 各ファイル・ディレクトリの責務

### ルート

| ファイル | 責務 |
|----------|------|
| `CLAUDE.md` | Claude Code用のプロジェクトメモリ。開発時の参照先 |
| `README.md` | 人間向けのプロジェクト概要。セットアップ手順を含む |
| `.env` | 認証情報と設定値。**Git管理外** |
| `.env.example` | `.env`のテンプレート。記入例を示す。Git管理対象 |
| `requirements.txt` | `pip install -r requirements.txt` で環境を再現する |

### docs/

アプリ全体の「何を作るか」「どう作るか」を定義する恒久的なドキュメント群。基本設計や方針が変わらない限り更新されない。

| ファイル | 責務 |
|----------|------|
| `product-requirements.md` | ユーザー課題・ゴール・スコープ・フェーズ計画 |
| `functional-design.md` | 各機能の振る舞い・入出力・エラーハンドリング |
| `architecture.md` | システム構成・技術スタック・データフロー・外部API仕様 |
| `repository-structure.md` | このファイル。ディレクトリ構成とファイルの責務 |
| `development-guidelines.md` | コーディング規約・命名規則・テスト方針・Git運用 |
| `glossary.md` | プロジェクト内で使う用語の定義 |

### .steering/

個別の開発タスクごとに作成する作業用ドキュメント。完了後は削除してよい。`.gitignore` で管理外にすることを推奨。

### src/

| ファイル | クラス/関数 | 責務 |
|----------|-------------|------|
| `main.py` | `main()` | 全体のオーケストレーション。他モジュールを呼び出す |
| `config.py` | `Config` | 環境変数の読み込みとバリデーション |
| `garmin_client.py` | `GarminClient` | Garmin Connectへの認証とデータ取得 |
| `diary_generator.py` | `DiaryGenerator` | Claude APIを使った日記テキスト生成 |
| `notion_client.py` | `NotionClient` | NotionデータベースへのページCREATE |

### prompts/

LLMへのプロンプトテンプレートを管理する。コードと分離することでプロンプトの調整をコード変更なしに行えるようにする。

### logs/

cronジョブの実行ログを格納する。`logs/diary.log` にリダイレクトして使用する。`.gitkeep` のみGit管理し、ログファイルは `.gitignore` で除外する。

### tests/

| ファイル | テスト対象 |
|----------|------------|
| `test_garmin.py` | `GarminClient` |
| `test_generator.py` | `DiaryGenerator` |
| `test_notion.py` | `NotionClient` |

## Git管理外ファイル（.gitignore対象）

| パターン | 理由 |
|----------|------|
| `.env` | 認証情報 |
| `.venv/` | 仮想環境（環境依存） |
| `logs/*.log` | 実行ログ |
| `__pycache__/` | Pythonキャッシュ |
| `.steering/` | 作業中ドキュメント（任意） |
| `~/.garminconnect` | Garminセッショントークン（リポジトリ外） |
