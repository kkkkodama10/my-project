"""テスト用フィクスチャ。

各テストは独立した in-memory SQLite を使用する。
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_session
from app.main import app
from app.routers.admin import _admin_sessions, _failed_attempts
from app.seed import seed_all


@pytest.fixture(autouse=True)
def _clear_admin_sessions():
    """テスト間で管理者セッションと失敗カウントをクリアする。"""
    _admin_sessions.clear()
    _failed_attempts.clear()
    yield
    _admin_sessions.clear()
    _failed_attempts.clear()


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    import app.models  # noqa: F401 — メタデータに全モデル登録

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine):
    """シード済みテストクライアント。demo イベント + 5問 + 管理者が存在する。"""
    sf = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # シード
    async with sf() as session:
        await seed_all(session)

    async def override_get_session():
        async with sf() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ── ヘルパー ───────────────────────────────────────────


async def join_and_register(
    client: AsyncClient,
    event_id: str = "demo",
    join_code: str = "123456",
    display_name: str = "tester",
) -> dict:
    """参加→登録してユーザ情報と Cookie 付きクライアント状態を返す。"""
    r = await client.post(
        f"/api/events/{event_id}/join",
        json={"join_code": join_code},
    )
    assert r.status_code == 200

    r2 = await client.post(
        f"/api/events/{event_id}/users/register",
        json={"display_name_base": display_name},
    )
    assert r2.status_code == 200
    return r2.json()


async def admin_login(client: AsyncClient, password: str = "secret") -> None:
    """管理者ログイン。"""
    r = await client.post("/api/admin/login", json={"password": password})
    assert r.status_code == 200
