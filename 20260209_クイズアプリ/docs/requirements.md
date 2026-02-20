# 仕様書: 同時接続型クイズアプリ

## 0. 本書の位置付け

本書は要件定義・API一覧・DB設計・状態遷移の各ドキュメントおよびプロトタイプ実装を踏まえ、3段階の開発フェーズそれぞれの仕様を定義する。

| フェーズ | 名称 | 目的 |
|---|---|---|
| Phase 1 | プロトタイプ（ローカル） | 最短で動くMVPをローカルで確認する |
| Phase 2 | ローカルアプリ（本格版） | プロトタイプの技術的負債を解消し、本番構成に移行可能な品質にする |
| Phase 3 | AWS構成（本番） | AWS上でマルチAZ・水平スケール可能な本番環境を構築する |

各セクションで Phase ごとの差分を明記する。記載がない項目は全 Phase 共通とする。

---

## 1. システム概要

- オールスター感謝祭のような同時接続型クイズアプリ
- ユーザはブラウザから参加し、4択問題にリアルタイムで回答する
- ランキングは正解数（降順）→ 正解した問題の回答時間合計（昇順）で順位付け

---

## 2. 利用者

| 種別 | 説明 |
|---|---|
| ユーザ | ブラウザから参加コードを入力して参加し、クイズに回答する |
| 管理者 | イベントの作成・進行・問題管理を行う |

---

## 3. 参加・ユーザ登録・セッション

### 3.1 参加フロー

1. ユーザはイベントURLにアクセスし、参加コード（6桁）を入力する
2. サーバはセッショントークン（HTTP Only Cookie）を発行する
3. ユーザは表示名ベース（例: `taro`）を入力して登録する
4. 表示名は `{ベース}-{ランダム4桁}` で生成される（例: `taro-4821`）
5. ランダム4桁は同一イベント内で一意とする（重複時は再生成）

**既存セッション検知（Phase 2）:**
- トップページ（`/`）アクセス時に `/me/state` でセッションを確認する
- 登録済みセッションが存在する場合は参加コード入力をスキップし、クイズページへ自動リダイレクトする
- セッションは存在するが未登録の場合はニックネーム登録ステップへスキップする

**遅延参加（クイズ終了後）の扱い（Phase 2）:**
- クイズが `finished` / `aborted` 状態のときに参加コードを入力すると、参加コード確認（join）までは許可するが表示名登録（register）を拒否する（HTTP 409）
- 代わりに「クイズは終了しました。次の開始をお待ち下さい。」を表示し、前回の結果テーブルを表示する
- 新規ログインはランキングに加わらない
- 管理者が次の Start を実行するとクイズ画面へ自動遷移する（3秒ポーリングで検知）

### 3.2 セッション管理

| 項目 | 仕様 |
|---|---|
| 識別方式 | HTTP Only Cookie（`session_id`） |
| 単位 | ブラウザ単位（シークレットモードは別セッション） |
| 複数タブ | 許可する。同一問題への回答は最初の1回のみ有効 |
| 途中参加 | 許可する。不参加問題は不正解扱い |
| 再接続 | セッション有効中は現在の問題画面に復帰可能 |
| ログアウト | QuizPage・ResultsPage・クイズ終了待ち画面にログアウトボタンを設置。Cookie を削除してトップページへ遷移 |
| ログアウト後の再参加 | 参加コードから再入力し、新規ユーザとして登録される |

### 3.3 データのライフサイクル

| Phase | 保持方式 |
|---|---|
| Phase 1 | インメモリ（プロセス再起動で消失） |
| Phase 2 | SQLite（ファイルベース永続化） |
| Phase 3 | RDS (PostgreSQL) + ElastiCache (Redis)。イベント終了後にユーザ・回答データを削除 |

---

## 4. 問題・回答データ

### 4.1 問題データ

| 項目 | 仕様 |
|---|---|
| 形式 | 問題文（最大300文字）+ 4択の選択肢（各最大120文字） |
| 画像 | 問題文および各選択肢に画像添付可能 |
| 正解 | 選択肢の1つ（`correct_choice_index`: 0-3） |
| 有効/無効 | `is_enabled` フラグで出題対象を制御 |

### 4.2 問題管理のフェーズ差分

| Phase | 管理方式 |
|---|---|
| Phase 1 | `questions.sample.json` ファイルから起動時に読み込み。5問固定 |
| Phase 2 | SQLite に永続化。管理画面から CRUD 操作が可能 |
| Phase 3 | RDS に永続化。管理画面から CRUD + 画像アップロード（S3）+ ドラッグ並び替え |

---

## 5. クイズ進行

### 5.1 イベント状態遷移

```
[waiting] ─(start)──→ [running] ─(finish)──→ [finished]
                          │
                          └──(abort)──→ [aborted]  ※Phase 2以降
```

| Phase | 差分 |
|---|---|
| Phase 1 | `waiting` / `running` / `finished` の3状態。abort なし |
| Phase 2 | `aborted` 状態を追加 |
| Phase 3 | 同上 |

### 5.2 問題進行状態遷移

```
[shown] ─(close)──→ [closed] ─(reveal)──→ [revealed] ─(next)──→ 次の問題の[shown]
```

| 状態 | 説明 |
|---|---|
| `shown` | 問題表示中。回答受付中（タイマー進行） |
| `closed` | 回答受付終了。正解表示待ち |
| `revealed` | 正解が公開済み。次の問題への切替待ち |

### 5.3 管理者の進行操作

管理者は以下のボタンでイベントを進行する。各フェーズで押下可能なボタンのみが有効化される。

| 操作 | 有効なフェーズ | 動作 |
|---|---|---|
| **Start Event** | `waiting` | イベント開始。`running` へ遷移 |
| **Next Question** | `started` / `revealed` | 次の問題を表示。全問完了時は `finished` へ遷移 |
| **Close Question** | `shown` | 回答受付を即時締め切る |
| **Reveal Answer** | `closed` | 正解を全クライアントに公開する |
| **Finish Event** | `running` 中いつでも | イベントを強制終了して結果画面へ遷移 |
| **Abort** | `running` 中いつでも | イベントを中止（`aborted` 状態）。参加者に警告バナーを表示 |
| **Reset** | `finished` / `aborted` | イベントを `waiting` 状態に戻す |

1問あたりの操作サイクル: **Next → (回答待ち) → Close → Reveal → Next**

### 5.4 オートモード（Phase 2）

管理ダッシュボードの `waiting` フェーズ時に **マニュアル / オート** を選択できる。

| モード | 動作 |
|---|---|
| マニュアル | 従来通り Next / Close / Reveal を手動で押す |
| オート | Start 後、各ステップを設定時間で自動進行する |

**オートモードの進行シーケンス:**

```
Start
  └→ シンキングタイム (秒) → Next Question
      └→ 回答時間（サーバーの time_limit_sec に連動）→ Close Question
          └→ 締め切り待機 (秒) → Reveal Answer
              └→ 解答表示 (秒) → Next Question → …（全問完了まで繰り返し）
```

**設定可能なタイミング（デフォルト値）:**

| 設定項目 | デフォルト | 意味 |
|---|---|---|
| シンキングタイム | 2秒 | Start → 最初の問題表示までの待機時間 |
| 回答時間 | サーバー設定連動 | イベントの `time_limit_sec` に自動同期 |
| 締め切り待機 | 3秒 | 回答締切後 → 正解公開までの待機 |
| 解答表示 | 2秒 | 正解公開後 → 次の問題までの表示時間 |

- オート中は Next / Close / Reveal ボタンが無効化（Abort / Reset は引き続き有効）
- 進行中のステップとカウントダウンを水色バナーで表示
- Abort / Reset でオートモードを即座に停止できる

### 5.4 配信方式

| Phase | リアルタイム配信 | フォールバック |
|---|---|---|
| Phase 1 | WebSocket（FastAPI 組み込み、インメモリ接続管理） | なし |
| Phase 2 | WebSocket（同上） | 5秒ポーリング（`GET /events/{event_id}/me/state`） |
| Phase 3 | WebSocket（API Gateway WebSocket or ALB）+ Redis Pub/Sub | 5秒ポーリング |

---

## 6. 回答仕様

### 6.1 回答ルール

| 項目 | 仕様 |
|---|---|
| 選択 | 4択から1つを選択してボタン押下で即時確定 |
| 変更 | **確定後は変更不可** |
| 二重提出 | 2回目以降は HTTP 409 で拒否。UIは「回答済み」表示 |
| 未回答 | 不正解扱い。結果画面では「未回答」表示 |

### 6.2 締切判定

| 項目 | 仕様 |
|---|---|
| 基準時刻 | サーバ時刻のみ。クライアントのタイマーは表示用 |
| 制限時間 | 全問共通。管理画面で秒数を設定（Phase 1 では固定10秒） |
| 猶予 | 締切 + 2.0秒未満まで受理（`submitted_at < deadline + 2.0s`） |
| 超過時 | `accepted = false`, `reject_reason = "deadline_passed"` |

### 6.3 回答時間の計測

```
回答時間 = サーバが当該ユーザへ問題を配信した時刻 − サーバが回答を受理した時刻
```

- 小数点1桁（四捨五入）で保存
- `delivered_at` はWS送信時にユーザ別に記録。WS未接続時は受理時刻で代替

### 6.4 ユーザ側UI状態

| 管理者操作後 | ユーザ側の表示 |
|---|---|
| Next Question | 問題文・4択表示、タイマー開始 |
| 回答確定後 | ボタン全て disabled、「回答済み」表示 |
| Close Question | 「回答受付終了」（灰色テキスト） |
| Reveal Answer | 正解の選択肢を**緑**、不正解の自分の回答を**赤**でハイライト。「正解!」/「不正解...」表示 |
| Finish Event | 問題エリアを非表示、結果テーブルを表示 |

---

## 7. ランキング・結果

### 7.1 順位計算

| キー | 順序 | 説明 |
|---|---|---|
| 第1キー | 正解数 降順 | 母数は全問題数 |
| 第2キー | 正解した問題の回答時間合計 昇順 | 不正解・未回答は含めない |
| 同点 | 同着扱い | 例: 1位、1位、3位 |

### 7.2 結果表示項目

| 項目 | 説明 |
|---|---|
| 順位 | 同着対応 |
| 表示名 | `{ベース}-{4桁}` |
| 正解数 | 全問中の正解数 |
| 未回答数 | 回答レコードが存在しない問題数（不正解扱い）|
| 正答率 | `正解数 / 全問題数` |
| 回答時間合計 | 正解した問題の回答時間の合計（秒、小数1桁） |

### 7.3 フェーズ差分

| Phase | 差分 |
|---|---|
| Phase 1 | イベント終了時に結果画面に自動遷移。API で取得 |
| Phase 2 | 同上 + 結果の CSV エクスポート機能 |
| Phase 3 | 同上 + 結果の永続保存（イベント削除とは別に保持） |

---

## 8. 管理者機能

### 8.1 認証

| Phase | 方式 |
|---|---|
| Phase 1 | 環境変数の固定パスワード（`ADMIN_PASSWORD`）。Cookie セッション |
| Phase 2 | ID/パスワード認証（ハッシュ保存）。ログイン失敗ロック |
| Phase 3 | 同上 + HTTPS 必須。セッション有効期限管理 |

### 8.2 機能一覧

| 機能 | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|
| イベント進行（Start/Next/Close/Reveal/Finish） | o | o | o |
| イベント作成 | 起動時に固定1件 | 管理画面から作成 | 同左 |
| 参加コード変更 | - | o | o |
| 問題 CRUD | JSON ファイル編集 | 管理画面から CRUD | 同左 |
| 問題の有効/無効切替 | - | o | o |
| 問題の並び替え | - | o（ドラッグ&ドロップ） | o |
| 画像アップロード | - | ローカルファイルシステム | S3 |
| 操作ログ閲覧 | ファイルベース（admin_audit.log） | DB保存 + 管理画面表示 | 同左 |
| 途中終了（abort） | Finish で代替 | o | o |

---

## 9. API 一覧

### 9.1 ユーザ系

| メソッド | パス | 説明 | Phase |
|---|---|---|---|
| `POST` | `/events/{event_id}/join` | 参加コード確認 + セッション発行 | 1/2/3 |
| `POST` | `/events/{event_id}/users/register` | 表示名登録（finished/aborted 時は 409） | 1/2/3 |
| `POST` | `/events/{event_id}/logout` | セッション Cookie 削除（ログアウト） | 2/3 |
| `GET` | `/events/{event_id}/me/state` | 現在状態取得（初期表示・再接続） | 1/2/3 |
| `POST` | `/events/{event_id}/questions/{question_id}/answers` | 回答提出 | 1/2/3 |
| `GET` | `/events/{event_id}/results` | ランキング取得（未回答数を含む） | 1/2/3 |
| `GET` | `/events/{event_id}/questions/current` | ポーリングフォールバック | 2/3 |

### 9.2 管理者系

| メソッド | パス | 説明 | Phase |
|---|---|---|---|
| `POST` | `/admin/login` | 管理者ログイン | 1/2/3 |
| `GET` | `/admin/verify` | 管理者セッション確認（Cookie 検証） | 2/3 |
| `POST` | `/admin/events` | イベント作成 | 2/3 |
| `PUT` | `/admin/events/{event_id}/join-code` | 参加コード変更 | 2/3 |
| `POST` | `/admin/events/{event_id}/start` | イベント開始 | 1/2/3 |
| `POST` | `/admin/events/{event_id}/questions/next` | 次の問題を表示 | 1/2/3 |
| `POST` | `/admin/events/{event_id}/questions/{question_id}/close` | 回答締切 | 1/2/3 |
| `POST` | `/admin/events/{event_id}/questions/{question_id}/reveal` | 正解公開 | 1/2/3 |
| `POST` | `/admin/events/{event_id}/finish` | イベント終了 | 1/2/3 |
| `POST` | `/admin/events/{event_id}/abort` | 途中終了 | 2/3 |
| `POST` | `/admin/questions` | 問題作成 | 2/3 |
| `PUT` | `/admin/questions/{question_id}` | 問題更新 | 2/3 |
| `GET` | `/admin/questions` | 問題一覧 | 2/3 |
| `PUT` | `/admin/questions/{question_id}/enabled` | 有効/無効切替 | 2/3 |
| `PUT` | `/admin/questions/reorder` | 並び替え | 2/3 |
| `POST` | `/admin/assets/images` | 画像アップロード | 2/3 |
| `GET` | `/admin/logs` | 操作ログ取得 | 1/2/3 |

### 9.3 WebSocket

| パス | 方向 | イベント | 説明 |
|---|---|---|---|
| `GET /ws?event_id=...` | S→C | `event.state_changed` | イベント状態変更 |
| | S→C | `question.shown` | 問題表示（問題データ含む） |
| | S→C | `question.closed` | 回答締切 |
| | S→C | `question.revealed` | 正解公開（`correct_choice_index` 含む） |
| | S→C | `event.finished` | イベント終了 |

---

## 10. データ設計

### 10.1 Phase 1（インメモリ）

プロセス内のPython辞書で管理する。プロセス再起動でリセット。

| ストア | キー | 値 |
|---|---|---|
| `events` | `event_id` | イベント状態全体 |
| `questions` | `question_id` | 問題データ |
| `sessions` | `session_id` | `{event_id, user_id, created_at}` |
| `users` | `user_id` | `{event_id, display_name, session_id, ...}` |
| `answers` | `(event_id, question_id, user_id)` | 回答データ |
| `connections` | `event_id` | `{session_id: websocket}` |

### 10.2 Phase 2（SQLite）

DB設計.md のテーブル定義に準拠。ただし以下を簡略化:

- `quiz_sets` テーブルはデフォルト1件のみ
- `images` テーブルはローカルファイルパスを保持
- `event_sessions` の `ip` / `user_agent` は任意

### 10.3 Phase 3（RDS + Redis）

DB設計.md のテーブル定義をそのまま適用:

- `admins`, `quiz_sets`, `questions`, `question_choices`, `images`
- `events`, `event_questions`, `event_sessions`, `event_users`
- `event_question_runs`, `answers`, `admin_audit_logs`

Redis の用途:
- WebSocket 接続情報の管理
- セッションストア
- `delivered_at` のユーザ別記録
- Pub/Sub によるマルチインスタンス間のイベント配信

---

## 11. アーキテクチャ

### 11.1 Phase 1: プロトタイプ（ローカル）

```
Browser ──HTTP/WS──→ FastAPI (port 8000)  ← インメモリストア
   │                     ↑
   └──HTTP──→ python -m http.server (port 5173)  ← 静的ファイル配信
```

- docker compose で backend + frontend を起動
- バックエンド: FastAPI + uvicorn、全ロジックを `main.py` に集約
- フロントエンド: 素の HTML/JS/CSS、`python -m http.server` で配信
- データ: インメモリ辞書（再起動でリセット）
- 問題: `questions.sample.json` から起動時ロード

### 11.2 Phase 2: ローカルアプリ（本格版）

```
Browser ──HTTP/WS──→ FastAPI (port 8000)  ← SQLite
   │                     ↑
   └──HTTP──→ Vite dev server (port 5173)  ← React/Vue SPA
```

**バックエンド改善:**
- `main.py` のモノリスをルーター/サービス/ストアに分離（開発手順_ローカル.md のディレクトリ構成に準拠）
- Pydantic スキーマによるリクエスト/レスポンス型定義
- SQLite + SQLAlchemy（or 軽量ORM）で永続化
- ストア層の抽象化（`base.py` → `sqlite_store.py`）で Phase 3 への差し替えを容易にする
- pytest によるユニットテスト・統合テスト
- ポーリングフォールバック（`GET /events/{event_id}/questions/current`）

**フロントエンド改善:**
- SPA フレームワーク導入（React or Vue）
- ユーザ画面と管理画面の分離
- 管理画面: 問題 CRUD、イベント作成、ドラッグ並び替え
- レスポンシブ対応

### 11.3 Phase 3: AWS構成（本番）

```
Browser ──HTTPS──→ CloudFront ──→ S3 (SPA)
   │
   └──HTTPS/WSS──→ ALB ──→ ECS Fargate (FastAPI x N)
                              ↕
                         RDS (PostgreSQL, Multi-AZ)
                              ↕
                         ElastiCache (Redis, Multi-AZ)
                              ↕
                         S3 (画像ストレージ)
```

**インフラ:**
- リージョン: 1リージョン、マルチAZ
- コンピュート: ECS Fargate（水平スケール）
- DB: RDS PostgreSQL（Multi-AZ）
- キャッシュ: ElastiCache Redis（セッション、WS Pub/Sub、delivered_at）
- CDN: CloudFront + S3（SPA + 画像配信）
- 通信: HTTPS/WSS 必須

**ストア層の差し替え:**
- `sqlite_store.py` → `rds_store.py`（SQLAlchemy のDB URLを切り替えるだけ）
- `memory_ws.py` → `redis_ws.py`（Redis Pub/Sub でマルチインスタンスブロードキャスト）

---

## 12. 非機能要件

| 項目 | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|
| 同時接続数 | 数人（検証用） | 〜10人（ローカル検証） | 初期100人、目標1,000人 |
| 回答応答時間 | - | - | p95 300ms以内 |
| 問題配信到達 | - | - | p95 1秒以内 |
| 可用性 | - | - | マルチAZ冗長、単一AZ障害時も継続 |
| 通信 | HTTP/WS | HTTP/WS | HTTPS/WSS 必須 |
| 認証 | 固定PW | ID/PW + ロック | 同左 + HTTPS |
| ログ | ファイルベース | SQLite | RDS + CloudWatch |
| データ精度 | 回答時間: 小数1桁 | 同左 | 同左（ms も保持） |

---

## 13. Phase 2（ローカルアプリ本格版）実装状況

### 13.1 実装済み

#### バックエンド基盤（MS1）

| 機能 | 状態 |
|---|---|
| FastAPI モジュール分割（routers / services / store / ws） | 実装済み |
| SQLAlchemy + aiosqlite による SQLite 永続化 | 実装済み |
| Pydantic v2 スキーマ定義（全エンドポイント） | 実装済み |
| 依存性注入（Depends）によるサービス・ストア管理 | 実装済み |
| pytest + pytest-asyncio による統合テスト基盤 | 実装済み |
| in-memory SQLite + シードデータを使ったテスト分離 | 実装済み |

#### バックエンド新機能（MS2）

| 機能 | 状態 |
|---|---|
| 管理者ログイン失敗ロック（5回失敗で15分ロック） | 実装済み |
| イベント作成 API（POST /api/admin/events） | 実装済み |
| 参加コード変更 API（PUT /api/admin/events/{id}/join-code） | 実装済み |
| 途中終了 Abort（state: aborted + WS 通知） | 実装済み |
| 問題 CRUD（作成・取得・更新・削除） | 実装済み |
| 問題の有効/無効切替 + ドラッグ並び替え（DnD） | 実装済み |
| 画像アップロード（PNG/JPEG → /uploads/） | 実装済み |
| 結果 CSV エクスポート | 実装済み |
| ポーリング API（GET /api/events/{id}/questions/current） | 実装済み |
| 管理操作ログ（SQLite + GET /api/admin/logs） | 実装済み |

#### フロントエンド React 化（MS3）

| 機能 | 状態 |
|---|---|
| Vite + React 18 SPA 構成 | 実装済み |
| React Router v6 によるルーティング | 実装済み |
| AuthContext（管理者ログイン状態管理） | 実装済み |
| EventContext（イベント状態・問題・回答の統合管理） | 実装済み |
| useWebSocket カスタムフック（1.5秒自動再接続） | 実装済み |
| WS 切断時のポーリングフォールバック（3秒間隔） | 実装済み |
| WS 切断インジケータ表示 | 実装済み |
| 参加ページ（JoinPage）・クイズページ（QuizPage） | 実装済み |
| 結果ページ（ResultsPage）+ ランキング表示 | 実装済み |
| 管理ダッシュボード（フェーズ同期 + ログ表示） | 実装済み |
| 問題管理ページ（AdminQuestionsPage）CRUD + DnD | 実装済み |
| Abort 状態の UI 表示（黄色警告バナー） | 実装済み |
| CSV ダウンロードボタン（finished / aborted 時） | 実装済み |
| nginx リバースプロキシ + SPA フォールバック | 実装済み |
| Docker マルチステージビルド（Node → nginx） | 実装済み |
| Docker Compose による全体起動 | 実装済み |

#### 追加改善機能

| 機能 | 状態 | 対象ファイル |
|---|---|---|
| **オートモード** — Start 後に全問を設定時間で自動進行（シンキングタイム・締め切り待機・解答表示を設定可能） | 実装済み | AdminDashboard.jsx |
| オートモードのカウントダウンバナー表示 | 実装済み | AdminDashboard.jsx |
| オートモードの回答時間をサーバー `deadline_at` に自動同期 | 実装済み | AdminDashboard.jsx |
| **ランキングに未回答数を表示** | 実装済み | Leaderboard.jsx / ranking_service.py / schemas/event.py |
| 未回答数を CSV エクスポートに追加 | 実装済み | ranking_service.py |
| **遅延参加ブロック** — finished/aborted 時の register を 409 で拒否 | 実装済み | routers/events.py |
| クイズ終了後ログイン時に「クイズは終了しました」メッセージ + 結果表示 | 実装済み | JoinPage.jsx |
| 終了待ち中に新クイズ開始を検知してクイズ画面へ自動遷移（3秒ポーリング） | 実装済み | JoinPage.jsx |
| **セッション永続化** — トップページ再訪時に既存セッションを検知してクイズページへリダイレクト | 実装済み | JoinPage.jsx |
| **管理者セッション永続化** — リロード後も再ログイン不要（`/admin/verify` による Cookie 検証） | 実装済み | AuthContext.jsx / admin.py |
| **参加者ログアウトボタン** — QuizPage・ResultsPage・クイズ終了待ち画面に設置。Cookie 削除 + トップページ遷移 | 実装済み | QuizPage.jsx / ResultsPage.jsx / JoinPage.jsx / routers/events.py |
| ログアウト後の再参加で新規ユーザーとして登録 | 実装済み | （上記の設計による） |

#### 品質保証（MS4）

| 機能 | 状態 |
|---|---|
| pytest テスト 106件（全通過） | 実装済み |
| サービス層カバレッジ 96%（目標 ≥80% 達成） | 実装済み |
| 全体カバレッジ 90% | 実装済み |

### 13.2 Phase 3 で対応する予定の項目

| 項目 | 優先度 |
|---|---|
| AWS 移行（ECS / Aurora / ElastiCache / S3） | 高 |
| マルチイベント対応（複数イベントの同時管理） | 高 |
| WebSocket の水平スケール（Redis Pub/Sub） | 高 |
| Alembic によるマイグレーション管理 | 中 |
| CDN による静的ファイル配信 | 中 |
| 認証強化（JWT / OAuth2） | 中 |
| 負荷テスト（同時接続 1000人規模） | 低 |

---

## 14. 検証手順（Phase 2）

### 14.1 起動

```bash
docker compose up --build -d
```

ブラウザで `http://localhost:5173` を開く。

### 14.2 ユーザフロー

1. トップページ（`/`）で Join code `123456` を入力 → **Join**
2. 表示名を入力 → **Register** → クイズページ（`/quiz/demo`）へ遷移
3. 管理者が問題を進めると自動更新（WS）

### 14.3 管理者フロー

1. `http://localhost:5173/admin` を開く
2. パスワード `secret` → **Login**（リロード後は再ログイン不要）
3. **マニュアル進行:**
   - **Start** → **Next Question** → ユーザ回答待ち → **Close Question** → **Reveal Answer** → **Next Question** を繰り返す
   - 全問終了後または **Finish** で結果確定
4. **オート進行:**
   - 「オート」を選択 → シンキングタイム・締め切り待機・解答表示の秒数を設定
   - **Start** → 全問が自動進行。カウントダウンバナーで状況を確認
   - Abort / Reset でいつでも停止可能
5. **結果 CSV ダウンロード** ボタンで成績を取得

### 14.4 確認ポイント

- 回答後にボタンが全て disabled になること
- Close で「回答受付終了」が表示されること
- Reveal で正解が緑、不正解が赤でハイライトされること
- 5問完了後の Next（または Finish）で結果画面に自動遷移すること
- ランキングに「未回答」列が表示されること
- ランキングが正解数降順 → 回答時間合計昇順でソートされていること
- Abort 時にユーザ画面に黄色警告バナーが表示されること
- WS 切断時に「ポーリングで更新中」インジケータが表示されること
- ページリロード後も管理ダッシュボードのフェーズが正しく復元されること
- クイズ終了後に参加コードを入力すると「クイズは終了しました」と結果が表示されること
- ログアウト後に再参加すると新規ユーザーとして登録されること
- 既存セッション有効時にトップページへアクセスするとクイズページへリダイレクトされること

### 14.5 問題管理

1. `http://localhost:5173/admin/questions` を開く
2. 問題の作成・編集・削除・並び替え・有効/無効切替が可能
3. 問題画像は PNG/JPEG をアップロード（`/uploads/` に保存）

### 14.6 自動テスト

```bash
cd backend
python -m pytest --cov=app/services -q
# → 106 passed, サービス層カバレッジ 96%
```
