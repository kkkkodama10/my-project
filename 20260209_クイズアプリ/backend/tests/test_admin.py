"""管理者系 API のテスト（ログイン・イベント進行）。"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import admin_login, join_and_register


@pytest.mark.asyncio
async def test_admin_login(client: AsyncClient):
    r = await client.post("/api/admin/login", json={"password": "secret"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_admin_login_wrong_password(client: AsyncClient):
    r = await client.post("/api/admin/login", json={"password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_start(client: AsyncClient):
    await admin_login(client)
    r = await client.post("/api/admin/events/demo/start")
    assert r.status_code == 200
    assert r.json()["state"] == "running"


@pytest.mark.asyncio
async def test_admin_start_requires_auth(client: AsyncClient):
    r = await client.post("/api/admin/events/demo/start")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_full_flow(client: AsyncClient):
    """Start → Next → Close → Reveal → Next(5問) → Finish の完全フロー。"""
    await admin_login(client)

    # Start
    r = await client.post("/api/admin/events/demo/start")
    assert r.json()["state"] == "running"

    for i in range(5):
        # Next
        r = await client.post("/api/admin/events/demo/questions/next")
        data = r.json()
        if data.get("state") == "finished":
            break
        qid = data["question_id"]
        assert qid is not None

        # Close
        r = await client.post(f"/api/admin/events/demo/questions/{qid}/close")
        assert r.json()["status"] == "ok"

        # Reveal
        r = await client.post(f"/api/admin/events/demo/questions/{qid}/reveal")
        assert r.json()["status"] == "ok"
        assert "correct_choice_index" in r.json()

    # 5問完了後の Next で finished
    r = await client.post("/api/admin/events/demo/questions/next")
    assert r.json()["state"] == "finished"


@pytest.mark.asyncio
async def test_admin_finish_early(client: AsyncClient):
    await admin_login(client)
    await client.post("/api/admin/events/demo/start")
    r = await client.post("/api/admin/events/demo/finish")
    assert r.json()["state"] == "finished"


@pytest.mark.asyncio
async def test_admin_logs(client: AsyncClient):
    await admin_login(client)
    await client.post("/api/admin/events/demo/start")

    r = await client.get("/api/admin/logs?limit=10")
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) >= 1
    assert logs[0]["action"] == "start"


# ── T-039: ログイン失敗ロック ─────────────────────────


@pytest.mark.asyncio
async def test_login_lockout(client: AsyncClient):
    """5回連続失敗で 429 が返ること。"""
    for _ in range(5):
        r = await client.post("/api/admin/login", json={"password": "wrong"})
        assert r.status_code == 401

    r = await client.post("/api/admin/login", json={"password": "wrong"})
    assert r.status_code == 429


@pytest.mark.asyncio
async def test_login_lockout_clears_on_success(client: AsyncClient):
    """4回失敗後に正しいパスワードで成功すると失敗カウントがリセットされること。"""
    for _ in range(4):
        await client.post("/api/admin/login", json={"password": "wrong"})

    r = await client.post("/api/admin/login", json={"password": "secret"})
    assert r.status_code == 200

    # リセット後は再びログイン失敗できる（ロックされない）
    r = await client.post("/api/admin/login", json={"password": "wrong"})
    assert r.status_code == 401


# ── T-040: イベント作成 ────────────────────────────────


@pytest.mark.asyncio
async def test_create_event(client: AsyncClient):
    await admin_login(client)
    r = await client.post(
        "/api/admin/events",
        json={"title": "New Event", "join_code": "abc123", "time_limit_sec": 20},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "New Event"
    assert data["state"] == "waiting"
    assert "event_id" in data


@pytest.mark.asyncio
async def test_create_event_requires_auth(client: AsyncClient):
    r = await client.post(
        "/api/admin/events",
        json={"title": "New Event"},
    )
    assert r.status_code == 401


# ── T-041: 参加コード変更 ──────────────────────────────


@pytest.mark.asyncio
async def test_update_join_code(client: AsyncClient):
    await admin_login(client)
    r = await client.put(
        "/api/admin/events/demo/join-code",
        json={"join_code": "newcode"},
    )
    assert r.status_code == 200
    assert r.json()["state"] == "waiting"

    # 旧コードで join できないこと
    r2 = await client.post("/api/events/demo/join", json={"join_code": "123456"})
    assert r2.status_code == 403

    # 新コードで join できること
    r3 = await client.post("/api/events/demo/join", json={"join_code": "newcode"})
    assert r3.status_code == 200


# ── T-042: abort ───────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_abort(client: AsyncClient):
    await admin_login(client)
    await client.post("/api/admin/events/demo/start")
    r = await client.post("/api/admin/events/demo/abort")
    assert r.status_code == 200
    assert r.json()["state"] == "aborted"
