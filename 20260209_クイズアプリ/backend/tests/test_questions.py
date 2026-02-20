"""問題管理 CRUD API のテスト (T-043〜T-047)。"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import admin_login

_SAMPLE_CHOICES = [
    {"choice_index": 0, "text": "A"},
    {"choice_index": 1, "text": "B"},
    {"choice_index": 2, "text": "C"},
    {"choice_index": 3, "text": "D"},
]


@pytest.mark.asyncio
async def test_list_questions(client: AsyncClient):
    """T-043: 問題一覧が取得できること。"""
    await admin_login(client)
    r = await client.get("/api/admin/questions")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "question_id" in data[0]
    assert "choices" in data[0]


@pytest.mark.asyncio
async def test_list_questions_requires_auth(client: AsyncClient):
    r = await client.get("/api/admin/questions")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_question(client: AsyncClient):
    """T-044: 問題が作成できること。"""
    await admin_login(client)
    r = await client.post(
        "/api/admin/questions",
        json={
            "question_text": "2 + 2 は？",
            "choices": _SAMPLE_CHOICES,
            "correct_choice_index": 0,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["question_text"] == "2 + 2 は？"
    assert data["correct_choice_index"] == 0
    assert len(data["choices"]) == 4
    assert data["is_enabled"] is True


@pytest.mark.asyncio
async def test_create_question_requires_4_choices(client: AsyncClient):
    await admin_login(client)
    r = await client.post(
        "/api/admin/questions",
        json={
            "question_text": "問題",
            "choices": _SAMPLE_CHOICES[:3],  # 3 択 → NG
            "correct_choice_index": 0,
        },
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_update_question(client: AsyncClient):
    """T-045: 問題テキストを更新できること。"""
    await admin_login(client)

    # 一覧から最初の問題を取得
    r = await client.get("/api/admin/questions")
    qid = r.json()[0]["question_id"]

    r = await client.put(
        f"/api/admin/questions/{qid}",
        json={"question_text": "更新後の問題文"},
    )
    assert r.status_code == 200
    assert r.json()["question_text"] == "更新後の問題文"


@pytest.mark.asyncio
async def test_update_question_not_found(client: AsyncClient):
    await admin_login(client)
    r = await client.put(
        "/api/admin/questions/nonexistent",
        json={"question_text": "x"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_set_question_enabled(client: AsyncClient):
    """T-046: 問題の有効/無効を切り替えられること。"""
    await admin_login(client)

    r = await client.get("/api/admin/questions")
    qid = r.json()[0]["question_id"]

    # 無効化
    r = await client.put(f"/api/admin/questions/{qid}/enabled", json={"enabled": False})
    assert r.status_code == 200
    assert r.json()["is_enabled"] is False

    # 再有効化
    r = await client.put(f"/api/admin/questions/{qid}/enabled", json={"enabled": True})
    assert r.status_code == 200
    assert r.json()["is_enabled"] is True


@pytest.mark.asyncio
async def test_reorder_questions(client: AsyncClient):
    """T-047: 問題の並び替えができること。"""
    await admin_login(client)

    r = await client.get("/api/admin/questions")
    questions = r.json()
    original_ids = [q["question_id"] for q in questions]

    # 逆順に並び替え
    reversed_ids = list(reversed(original_ids))
    r = await client.put("/api/admin/questions/reorder", json={"ordered_ids": reversed_ids})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # 順序が変わっていること
    r = await client.get("/api/admin/questions")
    new_ids = [q["question_id"] for q in r.json()]
    assert new_ids == reversed_ids
