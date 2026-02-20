"""WebSocket 接続管理・ブロードキャスト。

Phase 1 と同等のインメモリ管理。Phase 3 で Redis Pub/Sub 版に差し替え。
delivered_at_map もインメモリで保持する（問題ごとにリセット）。
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import WebSocket


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectionManager:
    def __init__(self) -> None:
        # event_id -> {session_id: WebSocket}
        self._connections: dict[str, dict[str, WebSocket]] = {}
        # event_id -> {session_id: iso_timestamp}
        self._delivered_at: dict[str, dict[str, str]] = {}

    # ── 接続管理 ───────────────────────────────────────

    async def connect(
        self,
        event_id: str,
        session_id: str,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()
        self._connections.setdefault(event_id, {})[session_id] = websocket

    def disconnect(self, event_id: str, session_id: str) -> None:
        conns = self._connections.get(event_id)
        if conns and session_id in conns:
            del conns[session_id]

    # ── ブロードキャスト ───────────────────────────────

    async def broadcast(self, event_id: str, payload: dict) -> None:
        """イベント内の全クライアントにメッセージ送信。"""
        conns = self._connections.get(event_id, {})
        for ws in list(conns.values()):
            try:
                await ws.send_json(payload)
            except Exception:
                pass

    async def broadcast_question(
        self,
        event_id: str,
        payload: dict,
    ) -> dict[str, str]:
        """問題配信用ブロードキャスト。

        送信成功した各セッションの delivered_at を記録して返す。
        """
        delivered_map: dict[str, str] = {}
        conns = self._connections.get(event_id, {})
        for sid, ws in list(conns.items()):
            try:
                await ws.send_json(payload)
                delivered_map[sid] = _now_iso()
            except Exception:
                pass
        self._delivered_at[event_id] = delivered_map
        return delivered_map

    # ── delivered_at 管理 ──────────────────────────────

    def get_delivered_at(self, event_id: str, session_id: str) -> str | None:
        return self._delivered_at.get(event_id, {}).get(session_id)

    def clear_delivered_at(self, event_id: str) -> None:
        self._delivered_at.pop(event_id, None)


# グローバルシングルトン
ws_manager = ConnectionManager()
