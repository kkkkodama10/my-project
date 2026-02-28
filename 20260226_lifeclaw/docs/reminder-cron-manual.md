# リマインド（Cron）設定マニュアル

LifeClaw のリマインド機能は OpenClaw の `cron` コマンドで管理する。
Docker コンテナ内で実行するため、コマンドは `docker exec lifeclaw-gateway openclaw cron ...` の形式で使う。

---

## 現在の設定

| 項目 | 値 |
|------|-----|
| 名前 | `lifelog-reminder` |
| ID | `e65bce0a-e598-42b4-8978-d61776b7ff77` |
| 時刻 | 毎日 **18:00 JST** |
| 送信先 | LINE（ユーザーID: `Ub1233b07b0e0755a830d2db42660831e`） |
| メッセージ | 「📝 今日のライフログを記録しよう！」 |
| 方式 | `--session main --system-event`（LLM経由でLINEプッシュ） |

---

## よく使うコマンド

### 現在のジョブ一覧を確認

```bash
docker exec lifeclaw-gateway openclaw cron list
```

### ジョブの詳細確認（JSON）

```bash
docker exec lifeclaw-gateway openclaw cron list --json
```

---

## リマインド時刻を変更する

### 手順

1. 現在のジョブIDを確認する

```bash
docker exec lifeclaw-gateway openclaw cron list
```

2. 既存ジョブを削除する

```bash
docker exec lifeclaw-gateway openclaw cron rm <ID>
```

3. 新しい時刻で再登録する（例: 21:00 に変更する場合）

```bash
docker exec lifeclaw-gateway openclaw cron add \
  --name "lifelog-reminder" \
  --description "毎日21時にLINEでライフログリマインドを送信" \
  --cron "0 21 * * *" \
  --tz "Asia/Tokyo" \
  --session main \
  --system-event "毎日のリマインド: LINEユーザー Ub1233b07b0e0755a830d2db42660831e に「📝 今日のライフログを記録しよう！」とLINEのプッシュメッセージを送ってください。それ以外は何もしないでください。"
```

**cron 式の読み方：** `分 時 日 月 曜日`

| cron 式 | 意味 |
|---------|------|
| `0 18 * * *` | 毎日 18:00 |
| `0 22 * * *` | 毎日 22:00 |
| `0 8,18 * * *` | 毎日 8:00 と 18:00 の2回 |
| `0 18 * * 1-5` | 平日（月〜金）18:00のみ |

---

## リマインドメッセージを変更する

既存ジョブを削除して `--system-event` の内容を変えて再登録する。

```bash
# 削除
docker exec lifeclaw-gateway openclaw cron rm <ID>

# 再登録（メッセージを変更）
docker exec lifeclaw-gateway openclaw cron add \
  --name "lifelog-reminder" \
  --cron "0 18 * * *" \
  --tz "Asia/Tokyo" \
  --session main \
  --system-event "毎日のリマインド: LINEユーザー Ub1233b07b0e0755a830d2db42660831e に「✏️ ログの時間だよ！今日どうだった？」とLINEのプッシュメッセージを送ってください。それ以外は何もしないでください。"
```

---

## ジョブを一時停止・再開する

```bash
# 停止
docker exec lifeclaw-gateway openclaw cron disable <ID>

# 再開
docker exec lifeclaw-gateway openclaw cron enable <ID>
```

---

## 今すぐテスト実行する

本番ジョブをそのまま即時実行してテストできる。

```bash
docker exec lifeclaw-gateway openclaw cron run <ID>
```

---

## N分後にテスト（使い捨て）

```bash
FUTURE=$(python3 -c "from datetime import datetime, timezone, timedelta; print((datetime.now(timezone.utc)+timedelta(minutes=3)).strftime('%Y-%m-%dT%H:%M:%SZ'))")

docker exec lifeclaw-gateway openclaw cron add \
  --name "test-reminder" \
  --at "$FUTURE" \
  --session main \
  --system-event "毎日のリマインド: LINEユーザー Ub1233b07b0e0755a830d2db42660831e に「📝 今日のライフログを記録しよう！」とLINEのプッシュメッセージを送ってください。それ以外は何もしないでください。" \
  --keep-after-run
```

実行確認後は削除する：
```bash
docker exec lifeclaw-gateway openclaw cron rm <テストジョブのID>
```

---

## 注意事項

- **Docker コンテナが停止するとcronも止まる。** Mac 再起動後は `docker compose up -d` でコンテナを起動すること。
- **Tailscale Funnel も再起動が必要。** Mac 再起動後は `tailscale funnel 18789` を再実行すること（または永続化設定を行うこと）。
- cron ジョブの設定は `~/.openclaw/cron/` に保存されるため、コンテナを再作成してもジョブは保持される。

---

## 技術メモ（なぜこの方式か）

`--session main --system-event` 方式を採用している理由：

| 方式 | 問題 |
|------|------|
| `--session isolated --announce` | isolated セッションは文脈がなく「No reply from agent」になる |
| `--session main --announce` | `--announce` は isolated 必須でエラー |
| `--session main --system-event` | ✅ メインエージェントがLINE push ツールで送信できる |
