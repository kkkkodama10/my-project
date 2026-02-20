"""ランキング計算のテスト。"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import admin_login, join_and_register


@pytest.mark.asyncio
async def test_ranking_empty(client: AsyncClient):
    """回答者なしでもランキング取得できる。"""
    r = await client.get("/api/events/demo/results")
    assert r.status_code == 200
    data = r.json()
    assert data["leaderboard"] == []
    assert data["event_summary"]["total_questions"] == 5


@pytest.mark.asyncio
async def test_ranking_single_user(client: AsyncClient):
    """1ユーザが1問正解した場合のランキング。"""
    await join_and_register(client)
    await admin_login(client)
    await client.post("/api/admin/events/demo/start")
    r = await client.post("/api/admin/events/demo/questions/next")
    qid = r.json()["question_id"]

    # q1 正解 (choice_index=2)
    await client.post(
        f"/api/events/demo/questions/{qid}/answers",
        json={"choice_index": 2},
    )

    r = await client.get("/api/events/demo/results")
    data = r.json()
    assert len(data["leaderboard"]) == 1
    entry = data["leaderboard"][0]
    assert entry["rank"] == 1
    assert entry["correct_count"] == 1
    assert entry["correct_time_sum_sec_1dp"] >= 0


@pytest.mark.asyncio
async def test_ranking_order(client: AsyncClient):
    """正解数の多いユーザが上位。"""
    # ユーザ 1: 参加登録
    await join_and_register(client, display_name="user1")

    await admin_login(client)
    await client.post("/api/admin/events/demo/start")

    # 問1
    r = await client.post("/api/admin/events/demo/questions/next")
    qid = r.json()["question_id"]

    # ユーザ 1 が正解
    await client.post(
        f"/api/events/demo/questions/{qid}/answers",
        json={"choice_index": 2},
    )

    r = await client.get("/api/events/demo/results")
    lb = r.json()["leaderboard"]
    assert len(lb) == 1
    assert lb[0]["correct_count"] == 1
