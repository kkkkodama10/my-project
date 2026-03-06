# 技術仕様書（アーキテクチャ）

## 1. システム構成

```
┌─────────────────────────────────────────────────┐
│ ローカルマシン (macOS)                            │
│                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │  Config   │───▶│  main.py │───▶│   Log    │   │
│  │  (.env)   │    └────┬─────┘    │  (stdout │   │
│  └──────────┘         │          │  + file) │   │
│                       │          └──────────┘   │
│            ┌──────────┼──────────┐              │
│            ▼          ▼          ▼              │
│     ┌───────────┐ ┌────────┐ ┌────────┐        │
│     │  Garmin   │ │ Diary  │ │ Notion │        │
│     │  Client   │ │ Gen.   │ │ Client │        │
│     └─────┬─────┘ └───┬────┘ └───┬────┘        │
└───────────┼────────────┼─────────┼──────────────┘
            ▼            ▼         ▼
     ┌────────────┐ ┌─────────┐ ┌───────┐
     │   Garmin   │ │ Claude  │ │ Notion│
     │  Connect   │ │   API   │ │  API  │
     │  (非公式)   │ │         │ │       │
     └────────────┘ └─────────┘ └───────┘
```

## 2. 技術スタック

| レイヤー | 技術 | バージョン/備考 |
|----------|------|----------------|
| 言語 | Python | 3.12+ |
| Garminデータ取得 | python-garminconnect | >=0.2.38（非公式APIラッパー） |
| LLM | Claude API (anthropic) | モデル: claude-haiku-4-5-20251001 |
| 日記投稿先 | Notion API (notion-client) | MVP後に追加 |
| 設定管理 | python-dotenv | .envファイル読み込み |
| スケジューリング | cron | OS標準、MVP後に設定 |

## 3. モジュール構成と依存関係

```
main.py
  ├── config.py          (依存なし)
  ├── garmin_client.py   (← python-garminconnect)
  ├── diary_generator.py (← anthropic)
  └── notion_client.py   (← notion-client)  ※MVP後
```

各モジュールは `main.py` からのみ呼び出される。モジュール間の直接依存はない。

### モジュール責務

| モジュール | クラス | 責務 |
|------------|--------|------|
| config.py | Config | .envの読み込みとバリデーション |
| garmin_client.py | GarminClient | Garmin Connectからヘルスデータ取得 |
| diary_generator.py | DiaryGenerator | Claude APIで自然文の日記生成 |
| notion_client.py | NotionClient | Notionデータベースへのページ作成 |
| main.py | - (関数) | オーケストレーション |

## 4. データフロー

```
GarminClient.get_daily_health_data(date)
    │
    ▼
health_data: dict          ←── 内部データ形式（§4.1）
    │
    ▼
DiaryGenerator.generate(health_data)
    │
    ▼
diary_text: str
    │
    ▼
NotionClient.create_diary_page(date, diary_text, metadata)  ※MVP後
    │
    ▼
page_url: str
```

### 4.1 内部データ形式（health_data）

```python
{
    "date": "2026-02-25",
    "sleep": {
        "total_hours": 6.5,      # 秒から時間に変換済み
        "deep_hours": 1.0,
        "light_hours": 3.5,
        "rem_hours": 2.0
    } | None,
    "steps": {
        "total": 8432
    } | None,
    "stress": {
        "average": 32
    } | None
}
```

- Garmin APIのレスポンスをこの形式に正規化する責務は `GarminClient` にある
- `None` は取得失敗を意味する

## 5. 外部API連携

### 5.1 Garmin Connect（python-garminconnect経由）

- **認証**: email/password → セッショントークン
- **トークン保存先**: `~/.garminconnect`（ライブラリのデフォルト）
- **再認証**: トークン期限切れ時に自動で再ログイン
- **MFA**: 現状は無効前提。有効化時は手動対応
- **リスク**: 非公式APIのため、Garmin側変更で破損する可能性がある

### 5.2 Claude API

- **認証**: APIキー（`ANTHROPIC_API_KEY`）
- **エンドポイント**: Messages API
- **モデル**: claude-haiku-4-5-20251001（コスト・速度優先）
- **パラメータ**: temperature=0.3 / max_tokens=500

### 5.3 Notion API（MVP後）

- **認証**: Internal Integration トークン（`NOTION_API_KEY`）
- **操作**: ページ作成のみ（読み取り・更新・削除は不要）
- **対象DB**: `NOTION_DATABASE_ID` で指定

## 6. エラーハンドリング方針

| 障害箇所 | 挙動 |
|----------|------|
| Garmin: 個別データ取得失敗 | その項目を `None` にし、他は継続 |
| Garmin: 全データ取得失敗 | 日記生成をスキップ、ログ記録して終了 |
| Claude API失敗 | 1回リトライ → 失敗ならログ記録して終了 |
| Notion API失敗 | 1回リトライ → 失敗ならローカルにMarkdown保存 |

## 7. ログ

- **出力先**: 標準出力（cron実行時は `logs/diary.log` にリダイレクト）
- **ログレベル**: Python標準の `logging` モジュールを使用
- **記録内容**: 実行開始/終了、取得成功したデータ項目、生成テキスト文字数、エラー詳細

## 8. セキュリティ

- 認証情報は `.env` に格納し、`.gitignore` で管理外にする
- Garminパスワードは平文保存（個人利用のため許容）
- APIキーのローテーションはユーザーの手動運用
