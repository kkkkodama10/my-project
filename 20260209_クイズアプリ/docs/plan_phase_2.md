# Phase 2 技術計画

## 0. 目的

Phase 1（プロトタイプ）の技術的負債を解消し、本番構成（Phase 3）へ移行可能な品質にする。
具体的には以下を達成する。

1. バックエンドのモジュール分割とストア層の抽象化
2. SQLite による永続化
3. Pydantic による型安全なリクエスト/レスポンス
4. pytest によるテスト基盤
5. React SPA によるフロントエンド刷新
6. 管理画面からの問題 CRUD・並び替え
7. ポーリングフォールバック・abort 状態の追加

---

## 1. 現状分析

### Phase 1 の構成

| 層 | 現状 | 課題 |
|---|---|---|
| バックエンド | `main.py` 1ファイル（595行） | ルーティング・ビジネスロジック・データアクセスが混在 |
| データ | Python 辞書（インメモリ） | 再起動で消失、テスト時の分離が困難 |
| 型定義 | なし（`request.json()` で生データ取得） | バリデーション不在、型安全性なし |
| フロントエンド | 素の HTML/JS/CSS（461行 + HTML） | 状態管理が手続き的、コンポーネント再利用不可 |
| テスト | なし | 品質保証なし |
| 依存 | FastAPI 0.95.2 / uvicorn 0.22.0 のみ | 最低限 |

---

## 2. ターゲットアーキテクチャ

```
Browser ──HTTP/WS──→ FastAPI (port 8000)  ← SQLite (data/quiz.db)
   │                     ↑
   └──HTTP──→ Vite dev server (port 5173)  ← React SPA
```

### 2.1 バックエンドディレクトリ構成

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app 生成、ミドルウェア、startup
│   ├── config.py                # 設定（環境変数、DB パス等）
│   ├── database.py              # SQLAlchemy エンジン・セッション管理
│   ├── models/                  # SQLAlchemy ORM モデル
│   │   ├── __init__.py
│   │   ├── event.py
│   │   ├── question.py
│   │   ├── user.py
│   │   ├── answer.py
│   │   └── admin.py
│   ├── schemas/                 # Pydantic スキーマ（リクエスト/レスポンス）
│   │   ├── __init__.py
│   │   ├── event.py
│   │   ├── question.py
│   │   ├── user.py
│   │   ├── answer.py
│   │   └── admin.py
│   ├── routers/                 # APIRouter 定義
│   │   ├── __init__.py
│   │   ├── events.py            # ユーザ系エンドポイント
│   │   ├── admin.py             # 管理者系エンドポイント
│   │   └── ws.py                # WebSocket
│   ├── services/                # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── event_service.py
│   │   ├── question_service.py
│   │   ├── answer_service.py
│   │   └── ranking_service.py
│   ├── store/                   # データアクセス層（抽象化）
│   │   ├── __init__.py
│   │   ├── base.py              # ABC（Phase 3 差し替え用）
│   │   └── sqlite_store.py      # SQLite 実装
│   └── ws/                      # WebSocket 管理
│       ├── __init__.py
│       └── manager.py           # 接続管理・ブロードキャスト
├── tests/
│   ├── conftest.py              # pytest fixture（テスト用 DB、テストクライアント）
│   ├── test_events.py
│   ├── test_questions.py
│   ├── test_answers.py
│   ├── test_admin.py
│   ├── test_ranking.py
│   └── test_ws.py
├── alembic/                     # DB マイグレーション（任意）
│   └── ...
├── data/                        # SQLite ファイル格納
│   └── .gitkeep
├── questions.sample.json
├── requirements.txt
└── Dockerfile
```

### 2.2 フロントエンドディレクトリ構成

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── main.jsx                 # エントリポイント
│   ├── App.jsx                  # ルートコンポーネント
│   ├── api/                     # API クライアント
│   │   └── client.js
│   ├── hooks/                   # カスタムフック
│   │   ├── useWebSocket.js
│   │   └── useEventState.js
│   ├── pages/                   # ページコンポーネント
│   │   ├── JoinPage.jsx
│   │   ├── QuizPage.jsx
│   │   ├── ResultsPage.jsx
│   │   ├── AdminLoginPage.jsx
│   │   └── AdminDashboard.jsx
│   ├── components/              # 共通 UI コンポーネント
│   │   ├── ChoiceButton.jsx
│   │   ├── Timer.jsx
│   │   ├── Leaderboard.jsx
│   │   ├── QuestionForm.jsx     # 問題 CRUD 用フォーム
│   │   └── QuestionList.jsx     # ドラッグ並び替え対応リスト
│   └── styles/
│       └── index.css
├── package.json
├── vite.config.js
└── Dockerfile
```

---

## 3. 技術選定

| カテゴリ | 技術 | 理由 |
|---|---|---|
| バックエンド FW | FastAPI（継続） | Phase 1 から変更なし |
| ORM | SQLAlchemy 2.0 | FastAPI との統合実績、Phase 3 の RDS 移行が DB URL 変更のみ |
| マイグレーション | Alembic | SQLAlchemy 標準のマイグレーションツール |
| バリデーション | Pydantic v2 | FastAPI 標準、高速 |
| テスト | pytest + httpx (AsyncClient) | FastAPI 公式推奨の非同期テスト手法 |
| フロントエンド FW | React 18 | エコシステムの成熟度、情報量 |
| ビルドツール | Vite | 高速 HMR、React テンプレート標準 |
| 状態管理 | React hooks (useState/useContext) | 規模的に十分、追加ライブラリ不要 |
| UI ライブラリ | なし（CSS 手書き） | Phase 1 の CSS を継承、過度な依存を避ける |
| D&D | @dnd-kit/core | 軽量なドラッグ&ドロップ（問題並び替え用） |

---

## 4. DB 設計（SQLite）

### 4.1 テーブル一覧

```sql
-- 管理者
CREATE TABLE admins (
    id          TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

-- 問題
CREATE TABLE questions (
    id                  TEXT PRIMARY KEY,
    question_text       TEXT NOT NULL,
    question_image_path TEXT,
    correct_choice_index INTEGER NOT NULL CHECK(correct_choice_index BETWEEN 0 AND 3),
    is_enabled          INTEGER NOT NULL DEFAULT 1,
    sort_order          INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

-- 選択肢
CREATE TABLE question_choices (
    id            TEXT PRIMARY KEY,
    question_id   TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    choice_index  INTEGER NOT NULL CHECK(choice_index BETWEEN 0 AND 3),
    text          TEXT NOT NULL,
    image_path    TEXT,
    UNIQUE(question_id, choice_index)
);

-- イベント
CREATE TABLE events (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    join_code       TEXT NOT NULL,
    time_limit_sec  INTEGER NOT NULL DEFAULT 10,
    state           TEXT NOT NULL DEFAULT 'waiting' CHECK(state IN ('waiting','running','finished','aborted')),
    current_question_id TEXT REFERENCES questions(id),
    current_index   INTEGER NOT NULL DEFAULT -1,
    current_shown_at TEXT,
    current_deadline_at TEXT,
    revealed        INTEGER NOT NULL DEFAULT 0,
    started_at      TEXT,
    finished_at     TEXT,
    created_at      TEXT NOT NULL
);

-- イベント ↔ 問題 の紐付け（出題順序）
CREATE TABLE event_questions (
    event_id    TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL REFERENCES questions(id),
    sort_order  INTEGER NOT NULL,
    PRIMARY KEY (event_id, question_id)
);

-- セッション
CREATE TABLE event_sessions (
    id          TEXT PRIMARY KEY,
    event_id    TEXT NOT NULL REFERENCES events(id),
    user_id     TEXT REFERENCES event_users(id),
    created_at  TEXT NOT NULL
);

-- ユーザ
CREATE TABLE event_users (
    id              TEXT PRIMARY KEY,
    event_id        TEXT NOT NULL REFERENCES events(id),
    session_id      TEXT,
    display_name    TEXT NOT NULL,
    display_suffix  TEXT NOT NULL,
    joined_at       TEXT NOT NULL,
    UNIQUE(event_id, display_suffix)
);

-- 回答
CREATE TABLE answers (
    id                      TEXT PRIMARY KEY,
    event_id                TEXT NOT NULL REFERENCES events(id),
    question_id             TEXT NOT NULL REFERENCES questions(id),
    user_id                 TEXT NOT NULL REFERENCES event_users(id),
    choice_index            INTEGER NOT NULL,
    delivered_at            TEXT NOT NULL,
    submitted_at            TEXT NOT NULL,
    accepted                INTEGER NOT NULL DEFAULT 1,
    reject_reason           TEXT,
    is_correct              INTEGER,
    response_time_sec_1dp   REAL,
    UNIQUE(event_id, question_id, user_id)
);

-- 管理操作ログ
CREATE TABLE admin_audit_logs (
    id          TEXT PRIMARY KEY,
    admin_id    TEXT,
    action      TEXT NOT NULL,
    event_id    TEXT,
    payload     TEXT,
    created_at  TEXT NOT NULL
);
```

### 4.2 Phase 3 への移行パス

- SQLAlchemy の DB URL を `sqlite:///data/quiz.db` → `postgresql://...` に変更
- Alembic マイグレーションはそのまま適用可能
- `CHECK` 制約、`TEXT` 型等は PostgreSQL でも互換

---

## 5. API 変更点（Phase 1 → Phase 2）

### 5.1 新規 API

| メソッド | パス | 説明 |
|---|---|---|
| `POST` | `/admin/events` | イベント作成 |
| `PUT` | `/admin/events/{event_id}/join-code` | 参加コード変更 |
| `POST` | `/admin/events/{event_id}/abort` | 途中終了（aborted 状態） |
| `POST` | `/admin/questions` | 問題作成 |
| `PUT` | `/admin/questions/{question_id}` | 問題更新 |
| `GET` | `/admin/questions` | 問題一覧取得 |
| `PUT` | `/admin/questions/{question_id}/enabled` | 有効/無効切替 |
| `PUT` | `/admin/questions/reorder` | 問題の並び替え |
| `POST` | `/admin/assets/images` | 画像アップロード（ローカル） |
| `GET` | `/events/{event_id}/questions/current` | ポーリングフォールバック |
| `GET` | `/events/{event_id}/results/csv` | CSV エクスポート |

### 5.2 既存 API の変更

| API | 変更内容 |
|---|---|
| `POST /admin/login` | ID/パスワード認証（ハッシュ照合）に変更。失敗ロック追加 |
| 全管理者 API | Pydantic スキーマによるリクエストバリデーション追加 |
| WebSocket | ポーリングフォールバック（5秒間隔）を並行サポート |

---

## 6. ストア層の抽象化設計

### 6.1 抽象基底クラス（ABC）

```python
# store/base.py
from abc import ABC, abstractmethod

class BaseEventStore(ABC):
    @abstractmethod
    async def get_event(self, event_id: str) -> dict | None: ...
    @abstractmethod
    async def create_event(self, event: dict) -> dict: ...
    @abstractmethod
    async def update_event(self, event_id: str, updates: dict) -> dict: ...
    # ... 他メソッド

class BaseQuestionStore(ABC):
    @abstractmethod
    async def list_questions(self, enabled_only: bool = False) -> list[dict]: ...
    @abstractmethod
    async def create_question(self, question: dict) -> dict: ...
    @abstractmethod
    async def update_question(self, question_id: str, updates: dict) -> dict: ...
    @abstractmethod
    async def reorder_questions(self, ordered_ids: list[str]) -> None: ...
    # ...
```

### 6.2 Phase 3 での差し替え

- `sqlite_store.py` → `rds_store.py`（DB URL 変更 + 非同期ドライバ）
- `ws/manager.py` → `ws/redis_manager.py`（Redis Pub/Sub 追加）
- DI（FastAPI の `Depends`）で切り替え

---

## 7. フロントエンド設計方針

### 7.1 ルーティング

| パス | コンポーネント | 説明 |
|---|---|---|
| `/` | `JoinPage` | 参加コード入力 |
| `/quiz` | `QuizPage` | 問題表示・回答 |
| `/results` | `ResultsPage` | ランキング表示 |
| `/admin` | `AdminLoginPage` | 管理者ログイン |
| `/admin/dashboard` | `AdminDashboard` | 進行操作 + 問題管理 |

### 7.2 状態管理

- `EventContext`: イベント状態（state, currentQuestion, myAnswer 等）
- `AuthContext`: セッション・管理者認証状態
- WebSocket は `useWebSocket` フックで管理、再接続ロジック内包

### 7.3 ユーザ画面と管理画面の分離

- ユーザ画面: `/`, `/quiz`, `/results`
- 管理画面: `/admin`, `/admin/dashboard`
- 同一 SPA 内でルーティング分離（React Router）

---

## 8. テスト戦略

### 8.1 テスト構成

| 種別 | 対象 | ツール |
|---|---|---|
| ユニットテスト | サービス層のビジネスロジック | pytest |
| 統合テスト | API エンドポイント（E2E） | pytest + httpx AsyncClient |
| WebSocket テスト | WS 接続・イベント配信 | pytest + httpx WebSocket |

### 8.2 テスト用 DB

- テスト実行時は `sqlite:///:memory:` を使用
- `conftest.py` で各テスト関数ごとにクリーンな DB を提供

### 8.3 カバレッジ目標

- サービス層: 80% 以上
- API 統合テスト: 主要フロー（参加→回答→結果）の E2E を網羅

---

## 9. 管理者認証の強化

| 項目 | Phase 1 | Phase 2 |
|---|---|---|
| 認証方式 | 環境変数の固定PW | ID/パスワード（DB 管理） |
| パスワード保存 | 平文比較 | bcrypt ハッシュ |
| ログイン失敗ロック | なし | 5回連続失敗で15分ロック |
| セッション管理 | インメモリ辞書 | DB（`admin_sessions` テーブルまたは signed cookie） |

---

## 10. Docker Compose（Phase 2）

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    image: quiz-app-backend:local
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/quiz.db
      - ADMIN_PASSWORD=secret  # 初期管理者作成用（初回起動のみ）
    volumes:
      - ./backend/data:/app/data          # DB 永続化
      - ./backend/uploads:/app/uploads    # 画像アップロード先
    restart: unless-stopped

  frontend:
    build: ./frontend
    image: quiz-app-frontend:local
    ports:
      - "5173:5173"
    restart: unless-stopped
```

---

## 11. 開発の進め方

### 11.1 ブランチ戦略

- `main`: 安定版（Phase 1 完了済み）
- `feature/phase2-backend-restructure`: バックエンド分割 + SQLite
- `feature/phase2-frontend-react`: フロントエンド React 化
- `feature/phase2-admin-crud`: 管理画面 CRUD
- PR ベースでレビュー → `main` にマージ

### 11.2 実装順序の原則

1. **バックエンド基盤から着手**（ストア層・DB・テスト環境）
2. **既存 API の移植**（Phase 1 の動作を壊さない）
3. **新規 API の追加**（CRUD、abort 等）
4. **フロントエンドの段階的移行**（API が安定した後）
5. **結合テスト・手動検証**

---

## 12. リスクと対策

| リスク | 影響 | 対策 |
|---|---|---|
| バックエンド分割で既存動作が壊れる | Phase 1 の動作担保が失われる | 統合テストを先に書き、リファクタ後に通ることを確認 |
| SQLAlchemy の非同期対応の複雑さ | 実装コスト増 | `aiosqlite` + SQLAlchemy async session を使用 |
| フロントエンド刷新の工数 | Phase 1 の HTML/JS を捨てるコスト | ページ単位で段階移行。API 互換を維持 |
| WebSocket とポーリングの並行サポート | 二重ロジック | サービス層でイベント発火 → WS/ポーリングは配信層が吸収 |
