"""ユーザ系 API のテスト（参加・登録・状態取得）。"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import join_and_register


@pytest.mark.asyncio
async def test_join_event(client: AsyncClient):
    r = await client.post("/api/events/demo/join", json={"join_code": "123456"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["event"]["event_id"] == "demo"
    assert data["event"]["state"] == "waiting"


@pytest.mark.asyncio
async def test_join_wrong_code(client: AsyncClient):
    r = await client.post("/api/events/demo/join", json={"join_code": "000000"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_join_not_found(client: AsyncClient):
    r = await client.post("/api/events/nonexistent/join", json={"join_code": "123456"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    await client.post("/api/events/demo/join", json={"join_code": "123456"})
    r = await client.post(
        "/api/events/demo/users/register",
        json={"display_name_base": "alice"},
    )
    assert r.status_code == 200
    user = r.json()["user"]
    assert user["display_name"].startswith("alice-")
    assert len(user["display_name"].split("-")[-1]) == 4


@pytest.mark.asyncio
async def test_register_no_session(client: AsyncClient):
    r = await client.post(
        "/api/events/demo/users/register",
        json={"display_name_base": "bob"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_state(client: AsyncClient):
    await join_and_register(client)
    r = await client.get("/api/events/demo/me/state")
    assert r.status_code == 200
    data = r.json()
    assert data["event"]["state"] == "waiting"
    assert data["me"] is not None
    assert data["me"]["display_name"].startswith("tester-")


@pytest.mark.asyncio
async def test_me_state_no_session(client: AsyncClient):
    r = await client.get("/api/events/demo/me/state")
    assert r.status_code == 401
