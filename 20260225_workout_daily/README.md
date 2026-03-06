# Auto Diary - Phase 1: 健康日記自動生成

## プロジェクト概要

1日に1回、Garminのヘルスデータを取得し、LLM（Claude API）で自然文の日記を自動生成してNotionに投稿するPythonアプリケーション。

### ゴール

- ユーザーが何もしなくても、毎日Notionに「今日の健康日記」が自動で作成される
- Phase 1ではレポート調の自然文から始め、将来的に情緒ある日記へ進化させる

---

## 開発ワークフロー

本プロジェクトはドキュメント駆動で開発を進める。ドキュメントは「永続的ドキュメント」と「作業単位のドキュメント」の2層構造で管理する。

### 永続的ドキュメント（`docs/`）

アプリ全体の「何を作るか」と「どう作るか」を定義する恒久的なドキュメント群。基本設計や方針が変わらない限り更新されない。

| ファイル | 役割 |
|----------|------|
| `docs/product-requirements.md` | プロダクトの要求定義書。ユーザー課題、ゴール、スコープ |
| `docs/functional-design.md` | 機能設計書。各機能の振る舞い、入出力、画面/UIフロー |
| `docs/architecture.md` | 技術仕様書。システム構成、技術スタック、データフロー、API仕様 |
| `docs/repository-structure.md` | リポジトリ構造定義書。ディレクトリ構成とファイルの責務 |
| `docs/development-guidelines.md` | 開発ガイドライン。コーディング規約、命名規則、テスト方針、Git運用 |
| `docs/glossary.md` | ユビキタス言語定義。プロジェクト内で使う用語の意味を統一 |

### 作業単位のドキュメント（`.steering/`）

個別の開発タスクごとに作成する作業用ドキュメント。タスクの開始から完了までのライフサイクルを管理する。

```
.steering/[YYYYMMDD]-[開発タイトル]/
├── requirements.md   # 今回の作業の要求内容（何をしたいか、なぜやるか）
├── design.md         # 変更内容の設計（どう実現するか、影響範囲）
└── tasklist.md       # タスクリスト（チェックボックス形式、進捗管理）
```

**例**: `.steering/20260225-garmin-data-integration/`

### 開発の進め方

1. **作業開始時**: `.steering/`に作業ディレクトリを作成し、`requirements.md`で要求を定義する
2. **設計**: `design.md`に変更内容の設計を書く。必要に応じて永続的ドキュメントを参照する
3. **タスク分解**: `tasklist.md`にタスクをチェックボックス形式で列挙する
4. **実装**: タスクリストに沿って実装を進め、完了したらチェックを入れる
5. **完了時**: 永続的ドキュメントへの反映が必要な場合は`docs/`を更新する

---

## フェーズ計画

| Phase | 内容 | 状態 |
|-------|------|------|
| **Phase 1（現在）** | Garminデータ（睡眠・歩数・ストレス）+ Claude API → Notion投稿 | 着手中 |
| Phase 2 | 写真のExifデータ（位置・時刻）を加えて「行動日記」に拡張 | 未着手 |
| Phase 3 | デバイス使用時間を追加し「知的活動」も含めた完全版 | 未着手 |

---

## 技術スタック

- **言語**: Python 3.12+
- **Garminデータ取得**: `python-garminconnect`（非公式APIラッパー、105+エンドポイント）
- **LLM**: Claude API（最安モデル: `claude-haiku-4-5-20251001`）
- **日記投稿先**: Notion API（新規データベースを作成）
- **スケジューリング**: cron
- **認証情報管理**: `.env` ファイル（`python-dotenv`）

---

## アーキテクチャ

```
[cron: 毎日 0:00] → [main.py]
                        │
                        ├─ 1. Garmin Connect からデータ取得
                        │     ├─ get_sleep_data(date)
                        │     ├─ get_steps_data(date)
                        │     └─ get_stress_data(date)
                        │
                        ├─ 2. データ整形・欠損ハンドリング
                        │     └─ 取得できた分だけでレポート構成
                        │
                        ├─ 3. Claude API で自然文の日記を生成
                        │     └─ プロンプト + 整形済みデータ → 日本語の自然文レポート
                        │
                        └─ 4. Notion API でページ作成
                              ├─ タイトル: 日付（例: 2026-02-25）
                              ├─ 本文: LLM生成テキスト
                              └─ プロパティ: 歩数、睡眠時間、ストレス平均値（数値）
```

---

## ディレクトリ構成

```
auto-diary/
├── claude.md              # このファイル（プロジェクト仕様・開発ワークフロー）
├── .env                   # 認証情報（Git管理外）
├── .env.example           # .envのテンプレート
├── .gitignore
├── requirements.txt
├── docs/                  # 永続的ドキュメント
│   ├── product-requirements.md
│   ├── functional-design.md
│   ├── architecture.md
│   ├── repository-structure.md
│   ├── development-guidelines.md
│   └── glossary.md
├── .steering/             # 作業単位のドキュメント（Git管理外 or 任意）
│   └── YYYYMMDD-task-title/
│       ├── requirements.md
│       ├── design.md
│       └── tasklist.md
├── src/
│   ├── __init__.py
│   ├── main.py            # エントリポイント
│   ├── garmin_client.py   # Garminデータ取得
│   ├── diary_generator.py # Claude APIで日記生成
│   ├── notion_client.py   # Notion投稿
│   └── config.py          # 設定管理（.env読み込み）
├── prompts/
│   └── diary_prompt.txt   # 日記生成プロンプトテンプレート
├── logs/
│   └── .gitkeep
└── tests/
    ├── test_garmin.py
    ├── test_generator.py
    └── test_notion.py
```

---

## 環境変数（.env）

```env
# Garmin Connect
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password

# Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Notion
NOTION_API_KEY=secret_xxxxx
NOTION_DATABASE_ID=xxxxx

# アプリ設定
DIARY_GENERATION_TIME=00:00        # 生成時刻（cron側で制御、設定値として保持）
DIARY_TARGET_DATE=yesterday        # "yesterday" or "today"（デフォルト: yesterday）
DIARY_LANGUAGE=ja                  # 日記の言語
```

---

## 各モジュール仕様

### 1. `garmin_client.py`

**責務**: Garmin Connectからヘルスデータを取得する

```python
class GarminClient:
    def __init__(self, email: str, password: str):
        """ログインしてセッションを確立。トークンはローカルに保存して再利用。"""

    def get_daily_health_data(self, date: str) -> dict:
        """
        指定日のヘルスデータを取得して返す。
        取得に失敗した項目はNoneとして含める（エラーで全体を止めない）。

        Returns:
            {
                "date": "2026-02-25",
                "sleep": { ... } | None,
                "steps": { ... } | None,
                "stress": { ... } | None,
            }
        """
```

**注意点**:
- `python-garminconnect`は非公式ライブラリのため、Garmin側の仕様変更で壊れる可能性がある
- セッショントークンは`~/.garminconnect`等に保存して再利用し、毎回ログインしない
- MFAは現状無効の前提。有効化された場合は手動対応が必要
- 各データ取得は個別にtry-exceptし、一部失敗でも他のデータは返す

### 2. `diary_generator.py`

**責務**: ヘルスデータからClaude APIを使って自然文の日記を生成する

```python
class DiaryGenerator:
    def __init__(self, api_key: str):
        """Anthropic クライアント初期化"""

    def generate(self, health_data: dict) -> str:
        """
        ヘルスデータを受け取り、自然文の日記テキストを返す。
        データが欠損している場合は、ある分だけで文章を構成する。

        出力例:
        "今日は6時間半ほど眠り、深い睡眠は約1時間。
         8,400歩ほど歩き、ストレスレベルは比較的低く推移した。"
        """
```

**プロンプト設計方針**:
- 日本語で出力
- Phase 1ではレポート調の自然文（事実ベース、簡潔）
- 数値は「約〇〇」「〇〇ほど」のように丸めて自然に表現
- 欠損データについては触れない（あるものだけで構成）
- LLMモデル: `claude-haiku-4-5-20251001`（最安・最速）
- temperature: 0.3（一貫性重視、多少のバリエーションは許容）
- max_tokens: 500（Phase 1では短文レポート）

### 3. `notion_client.py`

**責務**: 生成された日記をNotionデータベースに投稿する

```python
class NotionClient:
    def __init__(self, api_key: str, database_id: str):
        """Notion クライアント初期化"""

    def create_diary_page(self, date: str, content: str, metadata: dict) -> str:
        """
        Notionデータベースに日記ページを作成する。

        Args:
            date: "2026-02-25"
            content: LLM生成テキスト
            metadata: {"steps": 8432, "sleep_hours": 6.5, "stress_avg": 32}

        Returns:
            作成されたページのURL
        """
```

**Notionデータベース構成**:
- **タイトル（Title）**: 日付（例: `2026-02-25`）
- **本文（Content）**: LLM生成の自然文日記
- **歩数（Number）**: その日の合計歩数
- **睡眠時間（Number）**: 合計睡眠時間（時間単位、小数）
- **ストレス平均（Number）**: ストレスレベルの日平均値
- **生成日時（Date）**: ページ作成日時（自動記録用）

### 4. `config.py`

**責務**: `.env`から設定値を読み込み、バリデーションする

```python
class Config:
    """
    必須環境変数が未設定の場合は起動時にエラーを出す。
    DIARY_TARGET_DATE のデフォルトは "yesterday"。
    """
```

### 5. `main.py`

**責務**: 全体のオーケストレーション

```python
def main():
    """
    1. Config読み込み
    2. 対象日付を決定（デフォルト: 昨日）
    3. GarminClientでデータ取得
    4. DiaryGeneratorで日記生成
    5. NotionClientでページ作成
    6. ログ出力（成功/失敗、取得できたデータ項目、生成テキスト文字数）
    """
```

**エラーハンドリング方針**:
- Garminデータ取得失敗（全項目）: ログに記録、日記は生成しない
- Garminデータ部分欠損: 取得できた分で日記を生成
- Claude API失敗: リトライ1回、それでも失敗ならログに記録して終了
- Notion API失敗: リトライ1回、失敗ならローカルにMarkdownとして保存（フォールバック）

---

## cronジョブ設定

```bash
# 毎日0:00に実行（デフォルト）
0 0 * * * cd /path/to/auto-diary && /path/to/venv/bin/python src/main.py >> logs/diary.log 2>&1
```

**注意**: 睡眠データは翌朝のデバイス同期まで完全にならない場合がある。Phase 1では0:00実行のまま、欠損を許容する。必要に応じて実行時刻を朝に変更可能。

---

## 依存パッケージ（requirements.txt）

```
python-garminconnect>=0.2.38
anthropic
notion-client
python-dotenv
```

---

## セットアップ手順

1. リポジトリをクローン
2. Python仮想環境を作成: `python -m venv .venv && source .venv/bin/activate`
3. 依存パッケージをインストール: `pip install -r requirements.txt`
4. `.env.example`をコピーして`.env`を作成、認証情報を記入
5. Notionで新規データベースを作成し、Internal Integrationを接続
6. `python src/main.py`で手動実行テスト
7. crontabに登録

---

## 今後の拡張（Phase 2以降）

- **Phase 2**: 写真のExifデータ（GPS座標・撮影時刻）を取り込み、「どこで何をしたか」を日記に追加
- **Phase 3**: macOS/iOSのスクリーンタイムデータを取り込み、アプリ使用時間から「知的活動」を推定
- **共通拡張**: 日記のトーンを「レポート調」から「情緒的」に切り替える設定、週次・月次のサマリー自動生成、過去日記の振り返り機能