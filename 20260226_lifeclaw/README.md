# 🦞 LifeClaw - パーソナルライフログシステム

LINEで雑にメモを送るだけで、AIが日報フォーマットに整形し、Notionに自動記録するライフログシステム。

## コンセプト

来たるAI時代に向けて、**自分のコンテキスト（思考・行動・学習の履歴）をデバイスに蓄積する**ことが重要になる。本プロジェクトは、日常の記録を最小限の労力で構造化し、パーソナルコンテキストエンジンを構築することを目的とする。

## アーキテクチャ

```
┌──────────┐     ┌──────────────┐     ┌─────────────────────────────────────┐
│          │     │              │     │  自宅Mac                            │
│  LINE    │────▶│  Tailscale   │────▶│  ┌─ Docker ─────────────────────┐  │
│ (スマホ) │     │  Funnel      │     │  │                              │  │
│          │     │              │     │  │  OpenClaw Gateway             │  │
└──────────┘     └──────────────┘     │  │  ├── LINE Webhook 受信       │  │
                                      │  │  ├── lifelog スキル（自作）   │  │
       ┌──────────────────────────────│  │  ├── Notion API 書き込み     │  │
       │  リマインド（cron job）      │  │  └── cron: 毎日リマインド    │  │
       │  「今日のログを書こう📝」    │  │                              │  │
       ▼                              │  └──────────────────────────────┘  │
┌──────────┐                          │                                    │
│  LINE    │                          │  Tailscale（Funnel: Webhookのみ）  │
│ (通知)   │                          └────────────────────────────────────┘
└──────────┘                                       │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Notion          │
                                          │  ライフログDB    │
                                          └─────────────────┘
```

## データフロー

```
1. LINEで雑にメモを送信（フォーマット自由）
2. LINE Messaging API → Tailscale Funnel → Docker内のOpenClaw Gateway
3. OpenClawのlifelogスキルがLLMでメモを日報フォーマットに整形
4. Notion APIで特定のデータベースに書き込み（同一日付なら追記）
5. 毎日決まった時間にLINEでリマインドを送信（OpenClaw cron job）
```

## 記録するコンテキスト

### 仕事
- どういった考えで、どのような作業をしているか
- いつ、どんなタスクを行っているか
- 就業時間

### プライベート
- どのようなことを考えたか
- LLM（大規模言語モデル）に何を聞いたか
- どのような勉強をしているか
- どのようなYouTubeやドキュメンタリーを見たか
- 睡眠（起床時刻・就寝時刻）

### 家族
- 子供の成長記録

## Notionデータベース設計

| プロパティ | 型 | 説明 | 例 |
|-----------|------|------|------|
| 日付 | Date | 記録日 | 2026-02-26 |
| 起床時刻 | Date (時刻含む) | 起きた時刻 | 2026-02-26 07:00 |
| 就寝時刻 | Date (時刻含む) | 寝た時刻 | 2026-02-26 23:30 |
| 就業時間 | Number (h) | その日の労働時間 | 8.5 |
| 仕事 | Rich Text | やったこと・考えたこと | APIの設計レビュー |
| インプット | Rich Text | 読んだ/見たもの | YouTube「○○」 |
| LLMログ | Rich Text | LLMに聞いたこと | OpenClawの構成相談 |
| 勉強 | Rich Text | 学習内容 | Rustのライフタイム |
| 子供の成長 | Rich Text | 子供の出来事・発達記録 | 初めて「パパ」と言った |
| メモ | Rich Text | その他自由記述 | 体調やや不良 |
| 元メッセージ | Rich Text | LINE送信の原文（整形前） | 今日は8.5h働いた… |

### 運用ルール
- 1日に複数回送信した場合は、同一日付のレコードに追記する
- LLMが入力から各プロパティに自動振り分けする
- 振り分け不明な内容は「メモ」に格納する
- 起床/就寝は「7時に起きた」「23時半に寝た」のような自然言語から解析する
- 就業時間は「8.5h働いた」「9時〜17時半」のような入力から数値に変換する

## リマインド機能

OpenClawのcron jobを使い、毎日決まった時間にLINEでリマインドを送信する。

### 設定例
```bash
# 毎晩22:00にリマインドを送信
openclaw cron add \
  --name "lifelog-reminder" \
  --cron "0 22 * * *" \
  --tz "Asia/Tokyo" \
  --session isolated \
  --message "Output exactly: 📝 今日のログを書こう！仕事・インプット・睡眠・子供の成長、何でもOK。" \
  --deliver \
  --channel line \
  --to "<LINE_USER_ID>"
```

### リマインドのポイント
- LLM呼び出しなし（固定メッセージ出力のみ）でトークンコストを抑える
- isolatedセッションでメインの会話を汚さない
- 曜日ごとにメッセージを変えるなどの拡張も可能

## 技術スタック

| コンポーネント | 技術 | 用途 |
|--------------|------|------|
| メッセージ入力 | LINE Messaging API | ユーザーインターフェース |
| トンネル | Tailscale Funnel | Webhookの安全な外部公開 |
| コンテナ | Docker | ホストPCの隔離・保護 |
| AIエージェント | OpenClaw | メッセージ受信・整形・Notion書き込み |
| LLM | Claude API | メモの日報フォーマット整形 |
| データストア | Notion API | ライフログの蓄積・閲覧 |
| スケジューラ | OpenClaw Cron | 毎日のリマインド送信 |

## MVPコスト（目標: 無料）

| 項目 | コスト | 備考 |
|------|--------|------|
| LINE Messaging API | 無料 | フリープラン（月200通） |
| Tailscale | 無料 | Personalプラン（100デバイス） |
| Docker | 無料 | Docker Desktop（個人利用） |
| OpenClaw | 無料 | OSS |
| Notion | 無料 | フリープラン |
| 自宅Mac | 既存 | 常時起動（電気代のみ） |
| **LLM API** | **要検討** | **下記参照** |

### LLMコストの抑え方
MVPでは以下のアプローチでLLMコストを最小化する。

- **リマインドは固定メッセージ**: LLM呼び出し不要（トークンゼロ）
- **整形処理にはSonnet/Haikuを使用**: 日報整形は軽いタスクなのでOpus不要
- **ローカルLLM（Ollama）の検討**: 完全無料にしたい場合、整形程度ならローカルモデルでも十分対応可能
- **1日1〜3回の送信を想定**: 月間のAPI呼び出しは30〜90回程度に収まる

### LINE無料枠の運用
フリープランの月200通制限内で運用するための工夫:
- リマインド: 毎日1通 × 30日 = **30通/月**
- メモ整形の応答: 1日1〜2回 × 30日 = **30〜60通/月**
- 合計: **約60〜90通/月**（200通以内に十分収まる）

## セキュリティ設計（最小権限の原則）

本プロジェクトでは全レイヤーで最小権限を徹底する。

### Docker
- OpenClawをコンテナ内で実行し、ホストPCのファイルシステムから隔離
- マウントは `~/.openclaw`（設定）と `~/openclaw/workspace`（ワークスペース）のみ
- rootではなく `node` ユーザー（uid 1000）で実行

### Tailscale Funnel
- 公開するのはOpenClawのWebhookポート（18789）のみ
- ngrokと異なり、P2P通信で中間者リスクなし
- 固定URLが無料で利用可能

### OpenClaw Tools
- `exec`（シェル実行）: **無効**
- `browser`（ブラウザ操作）: **無効**
- `write`（ファイル書き出し）: 最小限のみ有効

### OpenClaw Skills
- バンドルスキルはホワイトリスト制（`skills.allowBundled`）
- 有効にするのは `notion` と自作の `lifelog` のみ
- サードパーティスキルは使用しない

### Notion API
- ライフログ用データベースのみインテグレーションに共有
- 権限: Read / Update / Insert のみ（**Deleteなし**）
- 他のNotionページには一切アクセス不可

### LINE
- 自分専用のBotアカウント
- 友だち登録は自分のみ

## セットアップ手順

### 1. 事前準備
- Docker Desktop をインストール
- Tailscale をインストール
- LINE Developers アカウントを作成
- Notion インテグレーションを作成

### 2. OpenClaw（Docker）
```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
./docker-setup.sh
```
オンボーディングで以下を設定:
- Gateway bind: `lan`
- LLMプロバイダー: Claude API（APIキーを設定）

### 3. LINE連携
1. LINE Developers で Messaging API チャネルを作成
2. チャネルアクセストークンとチャネルシークレットを取得
3. `~/.openclaw/openclaw.json` に追記:
```json
{
  "channels": {
    "line": {
      "token": "<チャネルアクセストークン>",
      "secret": "<チャネルシークレット>"
    }
  }
}
```

### 4. Tailscale Funnel
```bash
tailscale funnel 18789
```
表示されるURLをLINE DevelopersのWebhook URLに設定。

### 5. Notion連携
1. https://www.notion.so/my-integrations でインテグレーション作成
2. 権限: Read content / Update content / Insert content（Deleteは付けない）
3. Notionにライフログ用データベースを作成（上記スキーマ参照）
4. データベースにインテグレーションを接続（「…」→「Add connections」）
5. `~/.openclaw/.env` にトークンを追記:
```bash
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxx
LIFELOG_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 6. lifelogスキルの配置
```bash
mkdir -p ~/.openclaw/skills/lifelog
```
`~/.openclaw/skills/lifelog/SKILL.md` を作成（別途定義）。

### 7. 最小権限の設定
`~/.openclaw/openclaw.json`:
```json
{
  "tools": {
    "exec": false,
    "browser": false,
    "write": true
  },
  "skills": {
    "allowBundled": ["notion"]
  },
  "cron": {
    "enabled": true
  }
}
```

### 8. リマインド設定
```bash
openclaw cron add \
  --name "lifelog-reminder" \
  --cron "0 22 * * *" \
  --tz "Asia/Tokyo" \
  --session isolated \
  --message "Output exactly: 📝 今日のログを書こう！" \
  --deliver \
  --channel line \
  --to "<LINE_USER_ID>"
```

### 9. 起動・テスト
```bash
# Docker内のGateway再起動
docker compose restart openclaw-gateway
```
LINEからBotにテストメッセージを送信して動作確認。

## 入力例と処理結果

### LINEでの入力（雑でOK）
```
今日は9時半から18時まで仕事した（8.5h）。
API設計のレビューやった。
昼にRustのライフタイムの動画見た。
子供が初めてパパって言った！
7時起き、昨日は23時半に寝た。
```

### Notionへの書き込み結果

| プロパティ | 値 |
|-----------|------|
| 日付 | 2026-02-26 |
| 起床時刻 | 2026-02-26 07:00 |
| 就寝時刻 | 2026-02-25 23:30 |
| 就業時間 | 8.5 |
| 仕事 | API設計のレビュー |
| インプット | Rustのライフタイムの動画 |
| LLMログ | |
| 勉強 | Rustのライフタイム |
| 子供の成長 | 初めて「パパ」と言った |
| メモ | |
| 元メッセージ | （原文をそのまま保存） |

## 今後の拡張

- [ ] lifelogスキル（SKILL.md）の作成
- [ ] Notionデータベーステンプレートの作成
- [ ] 曜日別リマインドメッセージ（月曜は「今週の目標は？」等）
- [ ] 1日の終わりにサマリーを自動生成してLINEに返す
- [ ] 睡眠データの自動収集（Apple Health連携）
- [ ] YouTube視聴履歴の自動取り込み（Google Takeout）
- [ ] LLM会話ログの自動連携
- [ ] 週次・月次の振り返りレポート自動生成
- [ ] RAGによるコンテキスト検索（「先週何を考えていたか」）
- [ ] ローカルLLM（Ollama）対応で完全無料化

## ライセンス

Private - 個人利用
