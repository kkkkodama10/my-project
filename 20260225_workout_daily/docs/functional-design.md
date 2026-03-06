# 機能設計書

## 1. 全体フロー

```
[CLI実行] → [設定読み込み] → [対象日付決定] → [Garminデータ取得] → [日記生成] → [Notion投稿(*)] → [ログ出力]

(*) MVP後に追加
```

## 2. F1: Garminデータ取得

### 入力

- 対象日付（YYYY-MM-DD形式）
- Garmin認証情報（email / password）

### 処理

1. セッショントークンをローカル（`~/.garminconnect`）から読み込み、再利用を試みる
2. トークンが無効またはなければ、email/passwordでログインし、トークンを保存する
3. 以下のデータを個別に取得する（各取得は独立した try-except）

| データ | 取得内容 |
|--------|----------|
| 睡眠 | 合計睡眠時間、深い睡眠、浅い睡眠、REM睡眠（秒→時間に変換） |
| 歩数 | 合計歩数 |
| ストレス | 日平均ストレスレベル |

### 出力

```python
{
    "date": "2026-02-25",
    "sleep": {
        "total_hours": 6.5,
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

### エラーハンドリング

- 個別データ取得失敗 → その項目を `None` にし、他は継続
- 全項目が `None` → 日記生成をスキップ、ログに記録して終了

## 3. F2: 日記生成

### 入力

- F1の出力（ヘルスデータdict）

### 処理

1. ヘルスデータから `None` でない項目だけを抽出
2. プロンプトテンプレート（`prompts/diary_prompt.txt`）にデータを埋め込む
3. Claude API を呼び出す

**API パラメータ**:

| パラメータ | 値 |
|------------|-----|
| model | claude-haiku-4-5-20251001 |
| temperature | 0.3 |
| max_tokens | 500 |

**プロンプト設計方針**:

- やわらかい自然文で出力する指示
- 数値は「約〇〇」「〇〇ほど」のように丸める
- 欠損データには一切触れない
- 日本語で2〜5文の短文

### 出力

```
"6時間半ほど眠り、深い睡眠は約1時間だった。8,400歩ほど歩き、ストレスレベルは比較的低く推移した。"
```

### エラーハンドリング

- API呼び出し失敗 → 1回リトライ
- リトライも失敗 → ログに記録して終了

## 4. F3: Notion投稿（MVP後）

### 入力

- 対象日付（YYYY-MM-DD）
- 日記テキスト（F2の出力）
- メタデータ: `{ steps: int|None, sleep_hours: float|None, stress_avg: int|None }`

### 処理

Notionデータベースにページを作成する。

**ページ構成**:

| プロパティ | 型 | 値 |
|------------|----|----|
| タイトル | Title | 日付（例: `2026-02-25`） |
| 本文 | Content (blocks) | 日記テキスト |
| 歩数 | Number | 合計歩数（取得できた場合） |
| 睡眠時間 | Number | 合計睡眠時間（時間、小数） |
| ストレス平均 | Number | 日平均ストレスレベル |
| 生成日時 | Date | ページ作成日時 |

### 出力

- 作成されたページのURL

### エラーハンドリング

- API失敗 → 1回リトライ
- リトライも失敗 → ローカルに `logs/YYYY-MM-DD.md` として保存（フォールバック）

## 5. 設定管理

### 環境変数（.env）

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|------------|------|
| GARMIN_EMAIL | o | - | Garmin Connectメールアドレス |
| GARMIN_PASSWORD | o | - | Garmin Connectパスワード |
| ANTHROPIC_API_KEY | o | - | Claude API キー |
| NOTION_API_KEY | o(*) | - | Notion API キー |
| NOTION_DATABASE_ID | o(*) | - | Notion データベースID |
| DIARY_TARGET_DATE | - | yesterday | "yesterday" or "today" |
| DIARY_LANGUAGE | - | ja | 日記の言語 |

(*) MVP時点では未使用。Notion投稿追加時に必須になる。

### バリデーション

- 必須環境変数が未設定の場合、起動時にエラーメッセージを出して終了する

## 6. 対象日付の決定ロジック

1. `DIARY_TARGET_DATE` を読み取る
2. `"yesterday"` → 実行日の前日（デフォルト）
3. `"today"` → 実行日当日
4. YYYY-MM-DD形式の文字列 → その日付をそのまま使用
