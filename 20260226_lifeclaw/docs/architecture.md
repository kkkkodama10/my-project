# 技術仕様書

## システム構成図

```
┌──────────┐     ┌──────────────┐     ┌─────────────────────────────────────┐
│          │     │              │     │  自宅Mac                            │
│  LINE    │────▶│  Tailscale   │────▶│  ┌─ Docker ─────────────────────┐  │
│ (スマホ) │     │  Funnel      │     │  │                              │  │
│          │     │  :443        │     │  │  OpenClaw Gateway (:18789)   │  │
└──────────┘     └──────────────┘     │  │  ├── LINE Webhook 受信       │  │
                                      │  │  ├── lifelog スキル           │  │
       ┌──────────────────────────────│  │  ├── Notion API 書き込み     │  │
       │  リマインド（cron 22:00 JST）│  │  └── cron: リマインド送信    │  │
       ▼                              │  │                              │  │
┌──────────┐                          │  └──────────────────────────────┘  │
│  LINE    │                          │                                    │
│ (通知)   │                          │  Tailscale Funnel: port 18789のみ  │
└──────────┘                          └────────────────────────────────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Notion API      │
                                          │  ライフログDB    │
                                          └─────────────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Claude API      │
                                          │  (Sonnet/Haiku)  │
                                          └─────────────────┘
```

## 技術スタック

| レイヤー | 技術 | 役割 |
|---------|------|------|
| ユーザーIF | LINE Messaging API | メッセージ送受信 |
| ネットワーク | Tailscale Funnel | Webhookの安全な外部公開（P2P、固定URL） |
| コンテナ | Docker / Docker Compose | ホストPCからの隔離・実行環境 |
| AIエージェント | OpenClaw Gateway | Webhook受信、スキル実行、cron管理 |
| LLM | Claude API（Sonnet/Haiku） | メモの日報フォーマット整形 |
| データストア | Notion API | ライフログの蓄積・閲覧 |
| スケジューラ | OpenClaw Cron | 毎日のリマインド送信 |

### OpenClaw

- **リポジトリ**: https://github.com/openclaw/openclaw
- **インストール**: `npm install -g openclaw@latest`（Node ≥22 必須）
- **初期セットアップ**: `openclaw onboard --install-daemon`（対話式ウィザード）
- **Gateway起動**: `openclaw gateway`（WebSocket制御プレーン、port 18789）
- **スキル配置先**: `~/.openclaw/workspace/skills/<skill>/SKILL.md`
- **設定ファイル**: `~/.openclaw/openclaw.json`

## データフロー

### メッセージ受信〜記録フロー

```
LINE App
  │ HTTPS POST (Webhook)
  ▼
Tailscale Funnel (:443)
  │ プロキシ
  ▼
OpenClaw Gateway (:18789)
  │ 署名検証 → テキスト抽出
  ▼
lifelog スキル
  │ プロンプト + テキスト
  ▼
Claude API (Sonnet/Haiku)
  │ 整形済みJSON返却
  ▼
lifelog スキル
  │ 日付でレコード検索 → 新規作成 or 追記
  ▼
Notion API
  │ 書き込み完了
  ▼
LINE Messaging API
  │ 「記録しました」返信
  ▼
LINE App
```

### リマインドフロー

```
OpenClaw Cron (22:00 JST)
  │ 固定メッセージ（LLM呼び出しなし）
  ▼
LINE Messaging API
  │ Push Message
  ▼
LINE App（「📝 今日のログを書こう！」）
```

## API仕様

### LINE Webhook（受信）

- **エンドポイント**: `https://<tailscale-hostname>/webhook/line`
- **メソッド**: POST
- **認証**: チャネルシークレットによる署名検証（`X-Line-Signature` ヘッダー）
- **ペイロード**: LINE Messaging API の Webhook Event Object

### Notion API（送信）

- **ベースURL**: `https://api.notion.com/v1`
- **認証**: Bearer トークン（`NOTION_TOKEN`）
- **使用エンドポイント**:

| 操作 | エンドポイント | メソッド | 用途 |
|------|--------------|----------|------|
| レコード検索 | `/databases/{db_id}/query` | POST | 対象日付のページを検索 |
| ページ作成 | `/pages` | POST | 新規ライフログレコード作成 |
| ページ更新 | `/pages/{page_id}` | PATCH | 既存レコードへの追記 |

### Claude API（送信）

- **用途**: F2（ログ整形）でのみ使用
- **モデル**: `claude-sonnet-4-6` または `claude-haiku-4-5`（コスト優先）
- **入力**: ユーザーのテキストメッセージ + 整形指示プロンプト
- **出力**: 構造化JSON（`functional-design.md` F2の出力仕様参照）

## 設定ファイル構成

### `~/.openclaw/openclaw.json`

```json
{
  "gateway": {
    "bind": "lan"
  },
  "channels": {
    "line": {
      "token": "<チャネルアクセストークン>",
      "secret": "<チャネルシークレット>"
    }
  },
  "tools": {
    "exec": false,
    "browser": false,
    "write": true
  },
  "skills": {
    "allowBundled": ["notion"],
    "allowCustom": ["lifelog"]
  },
  "cron": {
    "enabled": true
  }
}
```

設定の詳細は `config/openclaw.json.example` を参照。

### `~/.openclaw/.env`

```
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxx
LIFELOG_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## セキュリティ設計

### 最小権限の原則

| レイヤー | 制限内容 |
|---------|---------|
| Docker | コンテナ内実行。`openclaw.json`・`.env`・`workspace/skills` を個別に読み取り専用（`:ro`）マウント。`node` ユーザー（uid 1000）で実行 |
| Tailscale Funnel | port 18789 のみ公開。P2P通信で中間者リスクなし |
| OpenClaw Tools | `exec`: 無効、`browser`: 無効、`write`: 最小限のみ有効 |
| OpenClaw Skills | ホワイトリスト制。`notion` と自作 `lifelog` のみ有効 |
| Notion API | ライフログDBのみ共有。権限: Read / Update / Insert（Delete なし） |
| LINE Bot | 自分専用。友だち登録は自分のみ |

### 通信経路

```
LINE → Tailscale Funnel (HTTPS/TLS) → Docker内 OpenClaw Gateway
OpenClaw → Claude API (HTTPS/TLS)
OpenClaw → Notion API (HTTPS/TLS)
```

全通信はHTTPS/TLSで暗号化される。Tailscale FunnelはP2P接続のため、第三者の中継サーバーを経由しない。

## コスト設計

| 項目 | コスト | 備考 |
|------|--------|------|
| LINE Messaging API | 無料 | フリープラン（月200通、想定60〜90通/月） |
| Tailscale | 無料 | Personalプラン |
| Docker | 無料 | Docker Desktop（個人利用） |
| OpenClaw | 無料 | OSS |
| Notion | 無料 | フリープラン |
| 自宅Mac | 既存 | 常時起動（電気代のみ） |
| Claude API | 従量課金 | Sonnet/Haiku使用で最小化（月30〜90回呼び出し） |

LLMコスト削減策:
- リマインドは固定メッセージ（LLM呼び出しゼロ）
- 整形処理にはSonnet/Haikuを使用（Opus不要）
- 将来的にローカルLLM（Ollama）で完全無料化も検討
