"""MS2 2.4〜2.6 新機能テスト (T-054 + 画像アップロード + CSV)。"""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient

from tests.conftest import admin_login, join_and_register


# ── T-054: ポーリング API ──────────────────────────────


@pytest.mark.asyncio
async def test_polling_waiting_state(client: AsyncClient):
    """waiting 状態では question=None が返ること。"""
    r = await client.get("/api/events/demo/questions/current")
    assert r.status_code == 200
    data = r.json()
    assert data["event_state"] == "waiting"
    assert data["question"] is None


@pytest.mark.asyncio
async def test_polling_running_no_question(client: AsyncClient):
    """start 直後（問題未表示）では question=None が返ること。"""
    await admin_login(client)
    await client.post("/api/admin/events/demo/start")

    r = await client.get("/api/events/demo/questions/current")
    assert r.status_code == 200
    data = r.json()
    assert data["event_state"] == "running"
    assert data["question"] is None


@pytest.mark.asyncio
async def test_polling_with_active_question(client: AsyncClient):
    """Next 後は question と deadline_at が返ること。"""
    await admin_login(client)
    await client.post("/api/admin/events/demo/start")
    r = await client.post("/api/admin/events/demo/questions/next")
    qid = r.json()["question_id"]

    r = await client.get("/api/events/demo/questions/current")
    assert r.status_code == 200
    data = r.json()
    assert data["event_state"] == "running"
    assert data["question"] is not None
    assert data["question"]["question_id"] == qid
    assert data["deadline_at"] is not None
    # 正解インデックスは非表示
    assert data["question"]["correct_choice_index"] is None


@pytest.mark.asyncio
async def test_polling_after_reveal(client: AsyncClient):
    """Reveal 後は correct_choice_index が含まれること。"""
    await admin_login(client)
    await client.post("/api/admin/events/demo/start")
    r = await client.post("/api/admin/events/demo/questions/next")
    qid = r.json()["question_id"]
    await client.post(f"/api/admin/events/demo/questions/{qid}/close")
    await client.post(f"/api/admin/events/demo/questions/{qid}/reveal")

    r = await client.get("/api/events/demo/questions/current")
    data = r.json()
    assert data["question"]["correct_choice_index"] is not None


@pytest.mark.asyncio
async def test_polling_event_not_found(client: AsyncClient):
    r = await client.get("/api/events/nonexistent/questions/current")
    assert r.status_code == 404


# ── CSV エクスポート (T-051) ──────────────────────────


@pytest.mark.asyncio
async def test_csv_export_empty(client: AsyncClient):
    """参加者 0 人の場合もヘッダ行だけ返ること。"""
    await admin_login(client)
    await client.post("/api/admin/events/demo/start")
    await client.post("/api/admin/events/demo/finish")

    r = await client.get("/api/events/demo/results/csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    assert "results_demo.csv" in r.headers["content-disposition"]

    # BOM を除いた CSV テキスト
    text = r.content.decode("utf-8-sig")
    lines = [l for l in text.splitlines() if l]
    assert lines[0].startswith("順位")


@pytest.mark.asyncio
async def test_csv_export_with_data(client: AsyncClient):
    """回答データがある場合は本文行が存在すること。"""
    await admin_login(client)
    await join_and_register(client, display_name="csv_user")
    await client.post("/api/admin/events/demo/start")

    # 1問進めて回答
    r = await client.post("/api/admin/events/demo/questions/next")
    qid = r.json()["question_id"]
    await client.post(
        f"/api/events/demo/questions/{qid}/answers",
        json={"choice_index": 0},
    )
    await client.post("/api/admin/events/demo/finish")

    r = await client.get("/api/events/demo/results/csv")
    text = r.content.decode("utf-8-sig")
    lines = [l for l in text.splitlines() if l]
    # ヘッダ + 少なくとも 1 ユーザ分
    assert len(lines) >= 2


# ── 画像アップロード (T-048) ──────────────────────────


@pytest.mark.asyncio
async def test_upload_image(client: AsyncClient, tmp_path):
    """PNG 画像がアップロードでき URL が返ること。"""
    await admin_login(client)

    # 1x1 の最小 PNG バイト列
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("test.png", io.BytesIO(png_bytes), "image/png")}
    r = await client.post("/api/admin/assets/images", files=files)
    assert r.status_code == 200
    data = r.json()
    assert data["url"].startswith("/uploads/")
    assert data["url"].endswith(".png")


@pytest.mark.asyncio
async def test_upload_image_wrong_type(client: AsyncClient):
    """画像以外のファイルは 400 が返ること。"""
    await admin_login(client)
    files = {"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")}
    r = await client.post("/api/admin/assets/images", files=files)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_upload_image_requires_auth(client: AsyncClient):
    png_bytes = b"\x89PNG\r\n\x1a\n"
    files = {"file": ("test.png", io.BytesIO(png_bytes), "image/png")}
    r = await client.post("/api/admin/assets/images", files=files)
    assert r.status_code == 401
