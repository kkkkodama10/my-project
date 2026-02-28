# リポジトリ構造定義書

## ディレクトリ構成

```
lifeclaw/
├── CLAUDE.md                          # AIアシスタント用プロジェクトメモリ
├── README.md                          # プロジェクト概要・セットアップ手順
├── docker-compose.yml                 # Docker Compose 定義
├── Dockerfile                         # OpenClaw Gateway コンテナ定義
├── .env.example                       # 環境変数テンプレート
├── docs/                              # 永続的ドキュメント
│   ├── product-requirements.md        #   プロダクト要求定義書
│   ├── functional-design.md           #   機能設計書
│   ├── architecture.md                #   技術仕様書
│   ├── repository-structure.md        #   リポジトリ構造定義書（本ファイル）
│   ├── development-guidelines.md      #   開発ガイドライン
│   └── glossary.md                    #   ユビキタス言語定義
├── skills/                            # OpenClaw カスタムスキル
│   └── lifelog/
│       └── SKILL.md                   #   lifelog スキル定義（プロンプト・ツール許可）
├── config/                            # 設定ファイルテンプレート
│   └── openclaw.json.example          #   OpenClaw 設定テンプレート
├── scripts/                           # ユーティリティスクリプト
│   └── setup.sh                       #   初期セットアップスクリプト
└── .steering/                         # 作業単位のドキュメント（Git管理対象外可）
    └── [YYYYMMDD]-[開発タイトル]/
        ├── requirements.md
        ├── design.md
        └── tasklist.md
```

## ファイル・ディレクトリの責務

### ルート

| ファイル | 責務 |
|---------|------|
| `CLAUDE.md` | AIアシスタントが最初に読むプロジェクトコンテキスト |
| `README.md` | プロジェクト概要、アーキテクチャ図、セットアップ手順 |
| `docker-compose.yml` | OpenClaw Gatewayコンテナの定義・読み取り専用ボリュームマウント・ポート設定 |
| `Dockerfile` | コンテナイメージのビルド定義（Node 22 + OpenClaw） |
| `.env.example` | 環境変数のテンプレート（`NOTION_TOKEN`, `LIFELOG_DATABASE_ID` 等） |

### `docs/` — 永続的ドキュメント

プロジェクト全体の設計・方針を定義する恒久的なドキュメント群。基本設計や方針が変わらない限り更新しない。

### `skills/lifelog/` — lifelogスキル

| ファイル | 責務 |
|---------|------|
| `SKILL.md` | OpenClawのスキル定義。LLMへの整形プロンプト、使用ツール（Notion API）の許可設定、入出力仕様を記述 |

### `config/` — 設定テンプレート

| ファイル | 責務 |
|---------|------|
| `openclaw.json.example` | OpenClawの設定テンプレート。ツール制限・スキル許可リスト・LINE連携・cron設定の雛形 |

### `scripts/` — ユーティリティ

| ファイル | 責務 |
|---------|------|
| `setup.sh` | 初期セットアップの自動化（ディレクトリ作成、設定ファイルコピー、Docker起動等） |

### `.steering/` — 作業単位のドキュメント

個別の開発タスクごとに作成する作業用ディレクトリ。開発ワークフローに従い `requirements.md` → `design.md` → `tasklist.md` の順で作成する。

## デプロイ先のファイル配置

リポジトリのファイルは自宅Mac上で以下のように配置される。

```
~/.openclaw/
├── openclaw.json          # ← config/openclaw.json.example をコピーして編集
├── .env                   # ← .env.example をコピーして編集
└── workspace/
    └── skills/
        └── lifelog/
            └── SKILL.md   # ← skills/lifelog/SKILL.md をコピーまたはシンボリックリンク
```

## .gitignore 方針

| 対象 | 理由 |
|------|------|
| `.env` | シークレット情報を含むため |
| `.steering/` | 作業中のドキュメントはリポジトリに含めなくてよい（任意） |
| `node_modules/` | 依存パッケージ |
