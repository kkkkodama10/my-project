# 設計書

## アーキテクチャ概要

Docker Compose で4コンテナを管理するローカル環境。

```
ブラウザ
  :3000 → frontend (React + Vite)
  :8000 → backend (FastAPI)
           ├── postgres :5432
           └── minio :9000
  :9001 → minio console
```

## コンポーネント設計

### 1. docker-compose.yml

**責務**: 4コンテナの定義・起動順序・環境変数・ボリューム管理

**実装の要点**:
- depends_on: postgres・minio → backend → frontend の順
- VITE_API_BASE_URL=http://localhost:8000 を frontend に渡す
- pgdata・miniodata ボリュームでデータ永続化

### 2. backend/Dockerfile

**責務**: Python 3.11 slim + uvicorn での FastAPI 起動

**実装の要点**:
- opencv-python-headless を使用（GUI不要環境）
- requirements.txt を先にコピーしてキャッシュ最適化
- 開発時は --reload で自動リロード

### 3. backend/app/main.py

**責務**: FastAPI 初期化・CORS・/health エンドポイント

**実装の要点**:
- CORS: allow_origins=["http://localhost:3000"]
- /health で {"status": "ok"} を返す

### 4. frontend/Dockerfile

**責務**: Node.js 20 alpine + Vite 開発サーバー

**実装の要点**:
- `npm run dev -- --host 0.0.0.0` でポート3000公開

## ディレクトリ構造

```
facegraph/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config.yml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       └── db/
│           ├── __init__.py
│           └── session.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       └── App.tsx
└── README.md
```

## 実装の順序

1. docker-compose.yml
2. backend/ 骨格（Dockerfile・requirements.txt・config.yml・app/）
3. Alembic 初期設定
4. frontend/ 骨格（Dockerfile・package.json・最小 React アプリ）
5. 動作確認

## 依存ライブラリ（backend/requirements.txt）

```
fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.30
alembic==1.13.1
asyncpg==0.29.0
pydantic==2.7.1
pydantic-settings==2.3.0
mediapipe==0.10.14
opencv-python-headless==4.9.0.80
numpy==1.26.4
scipy==1.13.0
boto3==1.34.131
python-multipart==0.0.9
pillow==10.3.0
PyYAML==6.0.1
```
