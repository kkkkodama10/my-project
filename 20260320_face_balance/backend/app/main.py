from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import check_db_connection
from app.routers import comparisons, images, persons

app = FastAPI(
    title="FaceGraph API",
    description="顔類似度定量分析 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(persons.router)
app.include_router(images.router)
app.include_router(comparisons.router)


@app.get("/health")
async def health_check():
    db_ok = await check_db_connection()
    return {
        "status": "ok",
        "db": "ok" if db_ok else "error",
    }
