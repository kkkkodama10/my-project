"""回答提出のテスト（二重提出・締切判定）。"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import admin_login, join_and_register


async def _start_and_next(client: AsyncClient) -> str:
    """イベント開始 + 最初の問題を表示して question_id を返す。"""
    await admin_login(client)
    await client.post("/api/admin/events/demo/start")
    r = await client.post("/api/admin/events/demo/questions/next")
    return r.json()["question_id"]


@pytest.mark.asyncio
async def test_submit_answer(client: AsyncClient):
    await join_and_register(client)
    qid = await _start_and_next(client)

    r = await client.post(
        f"/api/events/demo/questions/{qid}/answers",
        json={"choice_index": 2},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["result"] == "accepted"
    assert data["answer"]["choice_index"] == 2
    assert data["answer"]["response_time_sec_1dp"] is not None


@pytest.mark.asyncio
async def test_submit_answer_correct(client: AsyncClient):
    """q1 の正解は choice_index=2（東京）。"""
    await join_and_register(client)
    qid = await _start_and_next(client)
    assert qid == "q1"

    r = await client.post(
        f"/api/events/demo/questions/{qid}/answers",
        json={"choice_index": 2},
    )
    assert r.json()["answer"]["is_correct"] is True


@pytest.mark.asyncio
async def test_submit_answer_incorrect(client: AsyncClient):
    await join_and_register(client)
    qid = await _start_and_next(client)

    r = await client.post(
        f"/api/events/demo/questions/{qid}/answers",
        json={"choice_index": 0},
    )
    assert r.json()["answer"]["is_correct"] is False


@pytest.mark.asyncio
async def test_submit_double(client: AsyncClient):
    await join_and_register(client)
    qid = await _start_and_next(client)

    await client.post(
        f"/api/events/demo/questions/{qid}/answers",
        json={"choice_index": 0},
    )
    r = await client.post(
        f"/api/events/demo/questions/{qid}/answers",
        json={"choice_index": 1},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_submit_no_session(client: AsyncClient):
    qid = "q1"
    r = await client.post(
        f"/api/events/demo/questions/{qid}/answers",
        json={"choice_index": 0},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_state_after_answer(client: AsyncClient):
    """回答後に me/state で my_answer が返ること。"""
    await join_and_register(client)
    qid = await _start_and_next(client)

    await client.post(
        f"/api/events/demo/questions/{qid}/answers",
        json={"choice_index": 2},
    )
    r = await client.get("/api/events/demo/me/state")
    data = r.json()
    assert data["my_answer"] is not None
    assert data["my_answer"]["choice_index"] == 2
    # reveal 前なので is_correct は null
    assert data["my_answer"]["is_correct"] is None
