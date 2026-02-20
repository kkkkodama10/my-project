"""WebSocket 接続の基本テスト。"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import app


def test_ws_connect():
    """WebSocket に接続して echo が返ること。"""
    with TestClient(app) as client:
        with client.websocket_connect("/api/ws?event_id=demo") as ws:
            ws.send_text("ping")
            data = ws.receive_text()
            assert data == "echo: ping"


def test_ws_no_event_id():
    """event_id なしで接続すると close される。"""
    with TestClient(app) as client:
        with pytest.raises(Exception):
            with client.websocket_connect("/api/ws") as ws:
                ws.receive_text()
