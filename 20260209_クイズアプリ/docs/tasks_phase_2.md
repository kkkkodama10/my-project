# Phase 2 タスクリスト

## 凡例

- **優先度**: P0（ブロッカー）> P1（高）> P2（中）> P3（低）
- **状態**: `[ ]` 未着手 / `[~]` 進行中 / `[x]` 完了
- **依存**: 先行タスクの番号

---

## マイルストーン 1: バックエンド基盤構築

> 目標: モジュール分割・DB 接続・テスト環境を整備し、Phase 1 の全 API を新構成で動作させる

### 1.1 プロジェクト構成・依存関係

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-001 | `requirements.txt` を更新（SQLAlchemy, Alembic, aiosqlite, bcrypt, httpx, pytest, pytest-asyncio 等） | P0 | [x] | - |
| T-002 | バックエンドのディレクトリ構成を作成（`models/`, `schemas/`, `routers/`, `services/`, `store/`, `ws/`, `tests/`） | P0 | [x] | - |
| T-003 | `config.py` を作成（環境変数読み込み: `DATABASE_URL`, `ADMIN_PASSWORD` 等） | P0 | [x] | T-002 |

### 1.2 DB セットアップ

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-004 | `database.py` を作成（SQLAlchemy async engine + session factory） | P0 | [x] | T-001 |
| T-005 | SQLAlchemy ORM モデルを定義（`events`, `questions`, `question_choices`, `event_users`, `event_sessions`, `answers`, `admins`, `admin_audit_logs`） | P0 | [x] | T-004 |
| T-006 | Alembic 初期設定 + 初回マイグレーション作成 | P1 | [ ] | T-005 |
| T-007 | startup 時に DB テーブル自動作成（開発用） + サンプル問題のシードスクリプト | P1 | [x] | T-005 |

### 1.3 ストア層

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-008 | `store/base.py` に抽象基底クラス（ABC）を定義 | P0 | [x] | T-002 |
| T-009 | `store/sqlite_store.py` にイベント関連の CRUD を実装 | P0 | [x] | T-005, T-008 |
| T-010 | `store/sqlite_store.py` に問題関連の CRUD を実装 | P0 | [x] | T-005, T-008 |
| T-011 | `store/sqlite_store.py` にユーザ・セッション関連の CRUD を実装 | P0 | [x] | T-005, T-008 |
| T-012 | `store/sqlite_store.py` に回答関連の CRUD を実装 | P0 | [x] | T-005, T-008 |
| T-013 | `store/sqlite_store.py` に管理操作ログの CRUD を実装 | P1 | [x] | T-005, T-008 |

### 1.4 Pydantic スキーマ

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-014 | `schemas/event.py` — イベント関連のリクエスト/レスポンススキーマ | P0 | [x] | T-002 |
| T-015 | `schemas/question.py` — 問題関連のスキーマ | P0 | [x] | T-002 |
| T-016 | `schemas/user.py` — ユーザ・セッション関連のスキーマ | P0 | [x] | T-002 |
| T-017 | `schemas/answer.py` — 回答関連のスキーマ | P0 | [x] | T-002 |
| T-018 | `schemas/admin.py` — 管理者認証・操作ログ関連のスキーマ | P0 | [x] | T-002 |

### 1.5 サービス層

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-019 | `services/event_service.py` — イベント進行ロジック（start, next, close, reveal, finish, abort） | P0 | [x] | T-009 |
| T-020 | `services/question_service.py` — 問題 CRUD・並び替え・有効/無効切替 | P0 | [x] | T-010 |
| T-021 | `services/answer_service.py` — 回答提出・締切判定・回答時間計測 | P0 | [x] | T-012 |
| T-022 | `services/ranking_service.py` — ランキング計算・CSV エクスポート | P1 | [x] | T-012 |

### 1.6 WebSocket 管理

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-023 | `ws/manager.py` — ConnectionManager クラス（接続登録・削除・ブロードキャスト） | P0 | [x] | T-002 |
| T-024 | `delivered_at` のセッション別記録をマネージャー内で管理 | P1 | [x] | T-023 |

### 1.7 ルーター層（Phase 1 API 移植）

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-025 | `routers/events.py` — ユーザ系 API を移植（join, register, me/state, answers, results） | P0 | [ ] | T-014~T-017, T-019, T-021 |
| T-026 | `routers/admin.py` — 管理者系 API を移植（login, start, next, close, reveal, finish, logs） | P0 | [ ] | T-018, T-019 |
| T-027 | `routers/ws.py` — WebSocket エンドポイントを移植 | P0 | [ ] | T-023 |
| T-028 | `main.py` を書き換え（ルーター登録、startup で DB 初期化、ミドルウェア設定） | P0 | [ ] | T-025~T-027 |

### 1.8 テスト基盤

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-029 | `tests/conftest.py` — テスト用 DB（`sqlite:///:memory:`）、AsyncClient fixture | P0 | [ ] | T-004, T-005 |
| T-030 | `tests/test_events.py` — 参加・登録・状態取得の統合テスト | P1 | [ ] | T-025, T-029 |
| T-031 | `tests/test_answers.py` — 回答提出・二重提出拒否・締切判定のテスト | P1 | [ ] | T-025, T-029 |
| T-032 | `tests/test_admin.py` — 管理者ログイン・イベント進行操作のテスト | P1 | [ ] | T-026, T-029 |
| T-033 | `tests/test_ranking.py` — ランキング計算（同着・回答時間ソート）のテスト | P1 | [ ] | T-022, T-029 |
| T-034 | `tests/test_ws.py` — WebSocket 接続・イベント配信のテスト | P2 | [ ] | T-027, T-029 |

### 1.9 マイルストーン 1 完了確認

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-035 | Phase 1 と同等の手動検証（docker compose up → join → quiz → results） | P0 | [x] | T-028 |
| T-036 | 旧 `main.py`（Phase 1 モノリス）を削除またはアーカイブ | P1 | [x] | T-035 |

---

## マイルストーン 2: 新規バックエンド機能

> 目標: Phase 2 固有の機能（管理 CRUD、abort、ポーリング、CSV 等）を追加する

### 2.1 管理者認証の強化

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-037 | `admins` テーブルへの初期管理者シード（bcrypt ハッシュ） | P1 | [x] | T-007 |
| T-038 | `POST /admin/login` を ID/PW 認証（bcrypt 照合）に変更 | P1 | [x] | T-037 |
| T-039 | ログイン失敗カウント + 5回連続失敗で15分ロック | P2 | [x] | T-038 |

### 2.2 イベント管理

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-040 | `POST /admin/events` — イベント作成 API | P1 | [x] | T-026 |
| T-041 | `PUT /admin/events/{event_id}/join-code` — 参加コード変更 API | P2 | [x] | T-026 |
| T-042 | `POST /admin/events/{event_id}/abort` — 途中終了（aborted 状態）API | P2 | [x] | T-019 |

### 2.3 問題管理 CRUD

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-043 | `GET /admin/questions` — 問題一覧取得 API | P1 | [x] | T-020 |
| T-044 | `POST /admin/questions` — 問題作成 API（問題文 + 4選択肢） | P1 | [x] | T-020 |
| T-045 | `PUT /admin/questions/{question_id}` — 問題更新 API | P1 | [x] | T-020 |
| T-046 | `PUT /admin/questions/{question_id}/enabled` — 有効/無効切替 API | P2 | [x] | T-020 |
| T-047 | `PUT /admin/questions/reorder` — 並び替え API | P2 | [x] | T-020 |

### 2.4 画像アップロード

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-048 | `POST /admin/assets/images` — ローカルファイルシステムへの画像保存 API | P3 | [x] | T-026 |
| T-049 | 静的ファイル配信設定（`/uploads/` パスで画像を返す） | P3 | [x] | T-048 |

### 2.5 ポーリングフォールバック

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-050 | `GET /events/{event_id}/questions/current` — 現在の問題取得 API（ポーリング用） | P2 | [x] | T-025 |

### 2.6 結果エクスポート

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-051 | `GET /events/{event_id}/results/csv` — CSV ダウンロード API | P3 | [x] | T-022 |

### 2.7 新規機能のテスト

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-052 | 問題 CRUD API のテスト（作成・更新・削除・並び替え・有効/無効） | P1 | [x] | T-043~T-047, T-029 |
| T-053 | abort 状態遷移のテスト | P2 | [x] | T-042, T-029 |
| T-054 | ポーリング API のテスト | P2 | [x] | T-050, T-029 |

---

## マイルストーン 3: フロントエンド React 化

> 目標: 素の HTML/JS から React SPA に移行し、ユーザ画面と管理画面を分離する

### 3.1 プロジェクト初期化

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-055 | Vite + React プロジェクト初期化（`frontend/` 配下） | P1 | [x] | - |
| T-056 | `vite.config.js` — API プロキシ設定（`/api` → `localhost:8000`） | P1 | [x] | T-055 |
| T-057 | `api/client.js` — API クライアントモジュール（fetch ラッパー、credentials 設定） | P1 | [x] | T-055 |
| T-058 | `hooks/useWebSocket.js` — WebSocket 接続・再接続・イベントディスパッチ | P1 | [x] | T-055 |

### 3.2 ユーザ画面

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-059 | `JoinPage.jsx` — 参加コード入力画面 | P1 | [x] | T-057 |
| T-060 | `QuizPage.jsx` — 問題表示・選択肢ボタン・タイマー・回答状態 | P1 | [x] | T-057, T-058 |
| T-061 | `ResultsPage.jsx` — ランキング表示 | P1 | [x] | T-057 |
| T-062 | `components/ChoiceButton.jsx` — 選択肢ボタン（selected / correct / incorrect 状態） | P1 | [x] | T-055 |
| T-063 | `components/Timer.jsx` — カウントダウンタイマー | P1 | [x] | T-055 |
| T-064 | `components/Leaderboard.jsx` — ランキングテーブル | P1 | [x] | T-055 |

### 3.3 管理画面

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-065 | `AdminLoginPage.jsx` — 管理者ログイン画面 | P1 | [x] | T-057 |
| T-066 | `AdminDashboard.jsx` — イベント進行操作パネル（Start/Next/Close/Reveal/Finish/Abort） | P1 | [x] | T-057, T-058 |
| T-067 | `components/QuestionForm.jsx` — 問題作成・編集フォーム | P1 | [x] | T-055 |
| T-068 | `components/QuestionList.jsx` — 問題一覧 + ドラッグ&ドロップ並び替え（@dnd-kit） | P2 | [x] | T-067 |
| T-069 | 問題の有効/無効トグル UI | P2 | [x] | T-068 |
| T-070 | イベント作成フォーム（タイトル・参加コード・制限時間・問題選択） | P2 | [ ] | T-066 |
| T-071 | 操作ログ表示パネル | P2 | [x] | T-066 |

### 3.4 共通・レイアウト

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-072 | React Router 設定（ユーザ系 / 管理系のルーティング） | P1 | [x] | T-055 |
| T-073 | `EventContext` / `AuthContext` — グローバル状態管理 | P1 | [x] | T-055 |
| T-074 | レスポンシブ対応（モバイルでクイズ参加を想定） | P2 | [x] | T-059~T-061 |
| T-075 | Phase 1 の CSS を移植・調整 | P2 | [x] | T-055 |

### 3.5 フロントエンド Dockerfile

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-076 | `frontend/Dockerfile` 作成（Vite dev server） | P1 | [x] | T-055 |
| T-077 | `docker-compose.yml` を Phase 2 構成に更新 | P1 | [x] | T-076 |

---

## マイルストーン 4: 結合テスト・品質保証

> 目標: 全体を通した動作確認と品質基準の達成

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-078 | E2E 手動テスト — ユーザフロー（参加→回答→結果） | P1 | [x] | T-060, T-061 |
| T-079 | E2E 手動テスト — 管理者フロー（ログイン→問題作成→イベント作成→進行→終了） | P1 | [x] | T-066, T-067 |
| T-080 | E2E 手動テスト — 複数ユーザ同時参加（2-3ブラウザ） | P1 | [ ] | T-078 |
| T-081 | WebSocket 再接続・ポーリングフォールバックの動作確認 | P2 | [x] | T-050, T-058 |
| T-082 | abort 状態の UI 動作確認 | P2 | [x] | T-042, T-066 |
| T-083 | CSV エクスポートの動作確認 | P3 | [x] | T-051 |
| T-084 | pytest カバレッジ計測 + サービス層 80% 以上を確認 | P2 | [x] | T-030~T-034, T-052~T-054 |

---

## マイルストーン 5: ドキュメント・クリーンアップ

| # | タスク | 優先度 | 状態 | 依存 |
|---|---|---|---|---|
| T-085 | `requirements.md` のセクション13を Phase 2 実装状況で更新 | P2 | [x] | T-078~T-080 |
| T-086 | Phase 1 のフロントエンド（素 HTML/JS/CSS）を削除またはアーカイブ | P2 | [x] | T-078 |
| T-087 | `.gitignore` 更新（`data/*.db`, `uploads/`, `node_modules/`, `.venv/` 等） | P1 | [x] | - |

---

## タスク数サマリー

| マイルストーン | タスク数 | P0 | P1 | P2 | P3 |
|---|---|---|---|---|---|
| MS1: バックエンド基盤 | 36 | 22 | 12 | 1 | 0 |
| MS2: 新規バックエンド機能 | 18 | 0 | 7 | 7 | 4 |
| MS3: フロントエンド React 化 | 23 | 0 | 16 | 6 | 0 |
| MS4: 結合テスト・品質保証 | 7 | 0 | 3 | 3 | 1 |
| MS5: ドキュメント・クリーンアップ | 3 | 0 | 1 | 2 | 0 |
| **合計** | **87** | **22** | **39** | **19** | **5** |

---

## 推奨実装順序

```
MS1 (T-001 ~ T-036)   バックエンド基盤
       ↓
MS2 (T-037 ~ T-054)   新規バックエンド機能
       ↓
MS3 (T-055 ~ T-077)   フロントエンド React 化
       ↓
MS4 (T-078 ~ T-084)   結合テスト
       ↓
MS5 (T-085 ~ T-087)   クリーンアップ
```

> **注**: MS3 の `T-055`（React 初期化）は MS1 と並行して着手可能。
> ただし API との結合（T-059 以降）は MS1 完了後が望ましい。
