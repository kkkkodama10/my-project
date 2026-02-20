"""Phase 3: ヘルスチェックエンドポイント（ALB用）。"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """ALB ヘルスチェック用エンドポイント。

    Returns:
        dict: ステータス情報
    """
    return {"status": "ok"}
