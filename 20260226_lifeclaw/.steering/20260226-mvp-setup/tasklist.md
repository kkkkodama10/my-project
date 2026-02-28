# タスクリスト: MVP基盤構築

## 1. 外部サービスのセットアップ（手動）

- [x] LINE Developers でMessaging APIチャネルを作成する
- [x] チャネルアクセストークンとチャネルシークレットを取得する
- [x] Notionインテグレーションを作成する（権限: Read / Update / Insert、Deleteなし）
- [x] Notionにライフログ用データベースを作成する（スキーマは `product-requirements.md` 参照）
- [x] データベースにインテグレーションを接続する
- [x] Tailscale をインストールし、Funnelを有効化する

## 2. リポジトリのファイル作成

- [x] `.gitignore` を作成する
- [x] `.env.example` を作成する
- [x] `config/openclaw.json.example` を作成する
- [x] `Dockerfile` を作成する
- [x] `docker-compose.yml` を作成する
- [x] `skills/lifelog/SKILL.md` を作成する

## 3. ローカル環境の設定

- [x] `.env.example` をコピーして `.env` を作成し、実際のトークンを記入する
- [x] `config/openclaw.json.example` をコピーして `~/.openclaw/openclaw.json` に配置する
- [x] `skills/lifelog/SKILL.md` を `~/.openclaw/workspace/skills/lifelog/` に配置する（シンボリックリンク可）

## 4. 起動と動作確認

- [x] `docker compose up -d` でGatewayを起動する
- [x] `tailscale funnel 18789` でWebhookを公開する
- [x] LINE DevelopersのWebhook URLにTailscale FunnelのURLを設定する
- [x] LINEからテストメッセージを送信し、Notionに記録されることを確認する
- [x] 同一日付に2回目のメッセージを送信し、追記されることを確認する

## 5. リマインド設定

- [x] `openclaw cron add` でリマインドジョブを登録する（毎日18:00 JST、`--session main --system-event` 方式）
- [x] リマインドが届くことを確認する（17:19 JST にLINE受信確認）

## 6. セキュリティ確認

- [x] OpenClawの `exec` が無効であることを確認する（allowlist 0件）
- [x] Dockerコンテナがrootではなくnodeユーザーで実行されていることを確認する（uid=1000）
- [ ] `browser` の明示的無効化（現バージョンでは設定キー不明。ポート18791は外部非公開で運用中）
- [x] Notion APIの権限にDeleteが含まれていないことを確認する（Notion管理画面で手動確認）
