# v1.0 拡張設計書

## 全体方針

v1.0の3機能は互いに独立しており、それぞれ個別に実装・テスト・リリース可能とする。実装順序は依存関係と難易度から以下とする：

1. **R2: 天気自動記録**（最も独立性が高く、外部依存が少ない）
2. **R3: Garmin連携**（Pythonサイドカーの追加）
3. **R1: Ollama対応**（既存のLLMパイプライン変更のため最後に実施）

---

## D1: ローカルLLM（Ollama）対応設計

### 概要

OpenClawのLLMプロバイダー設定をClaude APIからOllamaに変更する。OpenClawは `--model` オプションまたは設定ファイルでLLMプロバイダーを切り替えられる想定。

### 構成変更

```
ホストマシン
├── Ollama（ホスト直接 or Docker）
│   └── モデル: gemma3（軽量・日本語対応）
└── Docker: lifeclaw-gateway（OpenClaw）
    └── LLMプロバイダー → Ollama（http://host.docker.internal:11434）
```

### 設計詳細

#### Ollamaのセットアップ

- ホストマシンにOllamaをインストール（`brew install ollama`）
- 推奨モデル: `gemma3`（軽量かつ日本語の構造化出力に対応）
  - 代替候補: `llama3.1:8b`, `phi3`
- モデルのプル: `ollama pull gemma3`

#### OpenClawとの接続

- OpenClawの設定（`openclaw.json`）でLLMプロバイダーをOllamaに変更
- エンドポイント: `http://host.docker.internal:11434`（Docker内からホストのOllamaにアクセス）
- Docker Composeに `extra_hosts` を追加してホスト名解決を保証

#### docker-compose.yml の変更

```yaml
services:
  openclaw:
    # ... 既存設定 ...
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - OLLAMA_HOST=http://host.docker.internal:11434
```

#### openclaw.json の変更

```json
{
  "provider": "ollama",
  "model": "gemma3",
  "ollama": {
    "host": "http://host.docker.internal:11434"
  }
}
```

> **注意**: OpenClawのOllama対応の具体的な設定キーは実装時に公式ドキュメントを確認する。上記は想定構成。

#### フォールバック設計

- Ollama接続失敗時はClaude APIにフォールバックする設定を検討
- フォールバックの実現方法はOpenClawの機能に依存するため、実装時に調査

#### SKILL.md の変更

- 基本的に変更不要（プロンプト自体はLLMプロバイダーに依存しない）
- Ollamaモデルの出力品質が不十分な場合のみプロンプト調整

### 検証項目

- [ ] Ollamaで既存プロンプトが正しくJSON出力を返すか
- [ ] 応答速度が実用範囲か（目標: 10秒以内）
- [ ] Docker内からOllamaへの接続が安定しているか

---

## D2: 天気・気温の自動記録設計

### 概要

lifelogスキルの処理フローに天気取得ステップを組み込む。ユーザーがLINEで日記メモを送信したタイミングで、Open-Meteo APIから横浜市の天気情報を取得しNotionに記録する。Notionに当日分の天気データが既に存在する場合はAPI呼び出しをスキップする。

### API仕様

#### Open-Meteo API

- **エンドポイント**: `https://api.open-meteo.com/v1/forecast`
- **認証**: 不要（完全無料、APIキー不要）
- **レート制限**: 10,000リクエスト/日（十分すぎる）

#### リクエスト例

```
GET https://api.open-meteo.com/v1/forecast
  ?latitude=35.4437
  &longitude=139.6380
  &daily=weather_code,temperature_2m_max,temperature_2m_min
  &timezone=Asia/Tokyo
  &forecast_days=1
```

#### レスポンス例

```json
{
  "daily": {
    "time": ["2026-03-01"],
    "weather_code": [3],
    "temperature_2m_max": [15.2],
    "temperature_2m_min": [6.8]
  }
}
```

#### WMOウェザーコードの変換表（主要なもの）

| コード | 天気 |
|--------|------|
| 0 | 快晴 |
| 1 | 晴れ |
| 2 | 一部曇り |
| 3 | 曇り |
| 45, 48 | 霧 |
| 51, 53, 55 | 霧雨 |
| 61, 63, 65 | 雨 |
| 71, 73, 75 | 雪 |
| 80, 81, 82 | にわか雨 |
| 95 | 雷雨 |

### 実装方式

#### 方式選定: lifelogスキル内での同期実行

天気取得はlifelogスキルの処理フローに組み込み、日記記録と同期して実行する。LLMは使わず、APIレスポンスを定型フォーマットに変換してNotionに書き込む。

#### 実装パターン

lifelogスキルの処理フロー（LLM整形 → Notion書き込み）の前段に天気取得ステップを追加する:

1. Notionの当日レコードを確認し、天気データが既に存在するかチェック
2. **未記録の場合のみ**: Open-Meteo APIを呼び出し（OpenClawのfetchツール or curlコマンド）
3. レスポンスからweather_code, max, minを抽出
4. weather_codeを日本語に変換
5. Notionの当日レコードに書き込み
6. **記録済みの場合**: スキップして次のステップ（LLM整形）へ進む

#### Notionプロパティ追加

| プロパティ名 | 型 | 内容 | 例 |
|-------------|------|------|------|
| 天気 | Rich Text | 天気概況 | 曇り |
| 最高気温 | Number | ℃ | 15.2 |
| 最低気温 | Number | ℃ | 6.8 |

#### トリガーとスキップ条件

- **トリガー**: ユーザーがLINEで日記メモを送信したとき（lifelogスキルの実行時）
- **スキップ条件**: Notionの当日レコードに天気プロパティ（天気・最高気温・最低気温のいずれか）が既に値を持っている場合
- 1日に複数回日記を送っても、天気APIは初回のみ呼び出される

#### エラーハンドリング

- API呼び出し失敗 → 1回リトライ
- リトライ失敗 → 天気記録のみスキップ、日記記録は通常通り続行
- Notion書き込み失敗 → 既存のF3エラーハンドリングに準拠

---

## D3: Garmin連携設計

### 概要

`20250225_workout_daily`プロジェクトの`python-garminconnect`ベースの実装パターンを流用し、Pythonサイドカーとしてlifeclawシステムに組み込む。ユーザーがLINEで日記メモを送信したタイミングでlifelogスキルからサイドカーを呼び出し、前日の健康データを取得してNotionに記録する。Notionに当日分の健康データが既に存在する場合はスキップする。

### アーキテクチャ

```
ホストマシン
├── Docker: lifeclaw-gateway（OpenClaw） ... 既存
└── Docker: lifeclaw-garmin（Python）     ... 新規
    ├── garmin_client.py（データ取得）
    ├── notion_writer.py（Notion書き込み）
    └── main.py（オーケストレーション）
```

#### サイドカー方式を選んだ理由

- `python-garminconnect`はPythonライブラリであり、Node.jsベースのOpenClawから直接呼べない
- 参考プロジェクトの実装をほぼそのまま流用できる
- OpenClawとは独立して動作するため障害が波及しない

### 取得データと Notionマッピング

| Garminデータ | Notionプロパティ | 型 | 既存/新規 |
|-------------|-----------------|------|----------|
| 睡眠合計時間 | 睡眠時間 | Number(h) | 新規 |
| 深い睡眠 | 深い睡眠 | Number(h) | 新規 |
| 浅い睡眠 | 浅い睡眠 | Number(h) | 新規 |
| REM睡眠 | REM睡眠 | Number(h) | 新規 |
| 歩数 | 歩数 | Number | 新規 |
| ストレス平均 | ストレス | Number | 新規 |
| Body Battery | Body Battery | Number | 新規 |
| HRV | HRV | Number | 新規 |

> **注意**: 既存の「起床時刻」「就寝時刻」はLINEメモからの手動入力として残す。Garminの睡眠データは詳細な内訳として別プロパティに記録する。

### Pythonサイドカーの構成

```
services/garmin/
├── Dockerfile
├── requirements.txt    # garminconnect, notion-client, python-dotenv
├── src/
│   ├── main.py            # エントリポイント（cron実行用）
│   ├── config.py          # 設定管理（.env読み込み）
│   ├── garmin_client.py   # Garmin APIラッパー（workout_dailyから移植）
│   └── notion_writer.py   # Notion書き込み（LifeClaw用に新規作成）
└── prompts/               # 不要（LLM未使用）
```

#### 参考プロジェクトからの流用

| ファイル | 流用元 | 変更点 |
|---------|--------|--------|
| garmin_client.py | workout_daily/src/garmin_client.py | ほぼそのまま流用 |
| config.py | workout_daily/src/config.py | Notion設定を追加、Claude設定を除去 |
| main.py | workout_daily/src/main.py | diary_generatorの代わりにnotion_writerを呼ぶ |
| notion_writer.py | 新規作成 | LifeClawのNotionスキーマに合わせた書き込み |

#### notion_writer.py の設計

- 既存のlifelog SKILL.mdと同じロジックを踏襲:
  1. 当日の日付でNotionデータベースを検索
  2. レコードが存在する → 健康データプロパティを更新
  3. レコードが存在しない → 新規作成（健康データのみ）
- Numberプロパティは上書き（Garminデータは1日1回の確定値のため）

### Docker Compose への追加

```yaml
services:
  # ... 既存の openclaw サービス ...

  garmin:
    build: ./services/garmin
    container_name: lifeclaw-garmin
    env_file:
      - .env
    volumes:
      - garmin-session:/home/appuser/.garminconnect
    user: "1000:1000"
    restart: "no"  # cronで起動するため常駐しない

volumes:
  garmin-session:  # Garminのセッショントークンを永続化
```

### 実行方式

lifelogスキルの処理フローからHTTP経由またはDockerコマンド経由で呼び出す。

#### トリガーとスキップ条件

- **トリガー**: lifelogスキル実行時にサイドカーを呼び出す（OpenClawのexecツール or HTTP API）
- **スキップ条件**: Notionの当日レコードに健康データプロパティ（睡眠時間・歩数等のいずれか）が既に値を持っている場合
- 1日に複数回日記を送っても、Garmin APIは初回のみ呼び出される

#### 呼び出し方式の選択肢

1. **HTTP API方式**: GarminサイドカーにFlask/FastAPIの軽量エンドポイントを追加し、lifelogスキルからfetch
2. **exec方式**: OpenClawからdocker compose runを実行（execツールが必要）
3. **常駐HTTP方式**: サイドカーを常駐させ、ヘルスチェック付きHTTP APIを公開

→ 実装時に方式を確定する（OpenClawから外部コマンド/HTTPを呼べるか調査が必要）

### 認証・セキュリティ

- Garmin認証情報は`.env`ファイルで管理
- セッショントークンはDockerボリューム（`garmin-session`）に永続化
- MFA未対応（Garminアカウント側でMFAを無効にする必要あり）

### エラーハンドリング

- `workout_daily`と同じパターン: 個別データ取得のtry-except分離
- 全データ失敗時のみスキップ、部分成功は記録する
- Notion書き込み失敗 → ログに記録（リトライ1回）

---

## Notionデータベース変更まとめ

### 新規追加プロパティ

| プロパティ名 | 型 | ソース | 備考 |
|-------------|------|--------|------|
| 天気 | Rich Text | Open-Meteo | R2 |
| 最高気温 | Number | Open-Meteo | ℃単位 |
| 最低気温 | Number | Open-Meteo | ℃単位 |
| 睡眠時間 | Number | Garmin | h単位（小数1桁） |
| 深い睡眠 | Number | Garmin | h単位 |
| 浅い睡眠 | Number | Garmin | h単位 |
| REM睡眠 | Number | Garmin | h単位 |
| 歩数 | Number | Garmin | 整数 |
| ストレス | Number | Garmin | 0-100 |
| Body Battery | Number | Garmin | 0-100 |
| HRV | Number | Garmin | ms単位 |

### 既存プロパティへの影響

- 変更なし。既存のMVPプロパティはすべてそのまま維持する。

---

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| OpenClawのOllama対応状況が不明 | R1が実装不可 | 実装前に公式ドキュメント/ソースを確認。非対応なら環境変数でのAPI切り替えを検討 |
| Ollamaモデルの日本語JSON出力品質 | 整形精度低下 | 複数モデルで検証、プロンプト調整、最悪Claude APIに戻す |
| python-garminconnectのAPI変更 | R3が動作不能 | ライブラリのバージョン固定、定期的な動作確認 |
| Garmin MFA強制化 | R3のログイン不可 | ライブラリのMFA対応状況を追跡 |
| Open-Meteo APIの仕様変更 | R2の取得失敗 | レスポンス構造の検証を入れる |
