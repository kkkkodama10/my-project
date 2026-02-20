import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{DATA_DIR / 'quiz.db'}",
)

# ──────────────────────────────────────────────────
# Redis / Valkey (Phase 3: AWS)
# ──────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", None)
# 例: redis://quiz-app-valkey.xxxx.0001.apne1.cache.amazonaws.com:6379/0

# ──────────────────────────────────────────────────
# S3 / CloudFront (Phase 3: AWS)
# ──────────────────────────────────────────────────
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", None)
# 例: quiz-app-assets-123456789012

CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN", None)
# 例: dxxxxxxxxxx.cloudfront.net

# ローカル開発用のアップロードディレクトリ（S3未設定時に使用）
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────
# Admin & CORS
# ──────────────────────────────────────────────────
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret")

_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()]

# ──────────────────────────────────────────────────
# Misc
# ──────────────────────────────────────────────────
QUESTIONS_SAMPLE_PATH = BASE_DIR / "questions.sample.json"
