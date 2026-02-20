"""Phase 2: FastAPI アプリケーションエントリポイント。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS, UPLOADS_DIR, REDIS_URL
from app.database import async_session_factory, init_db
from app.routers import admin, events, health, ws
from app.seed import seed_all

logger = logging.getLogger(__name__)
# 起動時に確認できるようにWARNINGレベルで必ず出力する
logging.getLogger("app.main").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # ── startup ──
    logging.warning("=" * 80)
    logging.warning("[VERSION CHECK] Application starting up")
    logging.warning(f"[VERSION CHECK] REDIS_URL is set: {bool(REDIS_URL)}")
    if REDIS_URL:
        logging.warning(f"[VERSION CHECK] REDIS_URL: {REDIS_URL[:50]}...")
    logging.warning("[VERSION CHECK] This is revision 7 with Valkey logging")
    logging.warning("=" * 80)

    await init_db()
    async with async_session_factory() as session:
        await seed_all(session)
    yield
    # ── shutdown ──


app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録（/api プレフィックス）
app.include_router(health.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(ws.router, prefix="/api")

# 静的ファイル（アップロード画像）
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/")
async def root():
    return {"message": "Quiz app backend (Phase 2)", "health": "/health"}


@app.get("/health")
async def health():
    return {"status": "ok"}
