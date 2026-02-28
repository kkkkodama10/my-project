# 設計: MVP基盤構築

## 変更内容の概要

以下の4つを新規作成し、MVPの一連のフローを動作可能にする。

1. **Docker環境** — OpenClaw Gatewayをコンテナで起動する構成
2. **lifelogスキル** — LINE受信→LLM整形→Notion書き込みの中核ロジック
3. **外部サービス連携** — LINE Bot・Notion DB・Tailscale Funnelの設定
4. **リマインド設定** — cronジョブによる毎日のLINE通知

## OpenClawの導入方針

- **インストール**: `npm install -g openclaw@latest`（Node ≥22 必須）
- **初期セットアップ**: `openclaw onboard --install-daemon`（対話式ウィザード）
- **実行方式**: Docker コンテナ内で `openclaw gateway` を起動（ホストPCの保護）
- **スキル配置先**: `~/.openclaw/workspace/skills/<skill>/SKILL.md`
- **設定ファイル**: `~/.openclaw/openclaw.json`
- **リポジトリ**: https://github.com/openclaw/openclaw

## 作成するファイル

| ファイル | 内容 |
|---------|------|
| `Dockerfile` | `node:22-slim` ベース。`openclaw@latest` をグローバルインストール。`node` ユーザー（uid 1000）で実行 |
| `docker-compose.yml` | ポート18789公開。設定ファイル・スキルを個別に読み取り専用（`:ro`）マウント。`node` ユーザー実行 |
| `.env.example` | 環境変数テンプレート（LINE認証情報、`NOTION_TOKEN`, `LIFELOG_DATABASE_ID`, `TAILSCALE_FUNNEL_URL`） |
| `config/openclaw.json.example` | OpenClaw設定テンプレート（ツール制限・スキル許可・LINE連携・cron） |
| `skills/lifelog/SKILL.md` | lifelogスキル定義。整形プロンプト、Notionツール許可、入出力JSON仕様 |
| `.gitignore` | `.env`, `node_modules/` 等の除外設定 |

## Docker構成の設計

### ボリュームマウント（読み取り専用）

```yaml
volumes:
  - ~/.openclaw/openclaw.json:/home/node/.openclaw/openclaw.json:ro
  - ~/.openclaw/.env:/home/node/.openclaw/.env:ro
  - ~/.openclaw/workspace/skills:/home/node/.openclaw/workspace/skills:ro
```

`~/.openclaw` を丸ごとマウントせず、必要なファイルのみを `:ro` で個別マウントする。コンテナからホストの設定ファイルを書き換えられないようにする。

## 外部サービスのセットアップ（手動作業）

以下はコード外の手動セットアップが必要。

| 作業 | 参照先 |
|------|--------|
| LINE Developers でMessaging APIチャネル作成 | `docs/architecture.md` LINE Webhook仕様 |
| Notionインテグレーション作成・DB作成 | `docs/product-requirements.md` Notionスキーマ |
| Tailscale Funnel の有効化 | `docs/architecture.md` ネットワーク構成 |

## lifelogスキルの設計

### 整形プロンプトの方針

- ユーザーの自然言語入力を受け取り、所定のJSONスキーマに変換する
- 時刻は自然言語→ISO 8601形式に変換（就寝時刻の前日判定含む）
- 振り分け不明な内容は `memo` に格納
- 該当なしのプロパティは `null`
- 詳細なJSON仕様は `functional-design.md` F2を参照

### Notion書き込みの方針

- 当日レコード検索 → 存在しなければ新規作成、存在すれば追記
- Rich Textプロパティは末尾追記、数値/時刻プロパティは上書き
- 詳細は `functional-design.md` F3を参照

## セキュリティ設計

| 対策 | 実現方法 |
|------|---------|
| ホストPC隔離 | Docker コンテナ内でOpenClaw実行 |
| 設定改ざん防止 | ボリュームを `:ro`（読み取り専用）でマウント |
| コマンド実行防止 | `openclaw.json` で `exec: false`, `browser: false` |
| 非rootユーザー | Dockerfile: `USER node`、docker-compose: `user: "1000:1000"` |
| スキル制限 | ホワイトリスト制。`notion`（バンドル）+ `lifelog`（カスタム）のみ |
| ポート制限 | 18789 のみ公開 |

## 影響範囲

- 新規ファイルの作成のみ。既存ドキュメントへの変更なし
- 外部サービス（LINE・Notion・Tailscale）のアカウント設定が前提条件
