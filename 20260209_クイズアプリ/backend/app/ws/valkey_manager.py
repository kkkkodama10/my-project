"""Phase 3: Valkey Pub/Sub を使った WebSocket マネージャー。

複数 ECS タスク間でイベントをブロードキャストするために、
Valkey (Redis) の Pub/Sub 機能を使用します。
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis
from fastapi import WebSocket


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ValkeyConnectionManager:
    """Valkey Pub/Sub ベースの WebSocket 接続マネージャー。"""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        # ローカルのWebSocket接続: event_id -> {session_id: WebSocket}
        self._connections: dict[str, dict[str, WebSocket]] = {}
        # delivered_at はValkey に保存: delivered:{event_id}:{session_id}
        self._subscriber_task: asyncio.Task | None = None

    async def _get_redis(self) -> aioredis.Redis:
        """Redis接続を取得（遅延初期化）。"""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def start_subscriber(self) -> None:
        """Pub/Sub購読タスクを開始。

        アプリケーション起動時に1回だけ呼び出す。
        """
        if self._subscriber_task is not None:
            return  # すでに起動済み

        redis = await self._get_redis()
        self._pubsub = redis.pubsub()
        self._subscriber_task = asyncio.create_task(self._subscribe_loop())

    async def stop_subscriber(self) -> None:
        """Pub/Sub購読タスクを停止。

        アプリケーション終了時に呼び出す。
        """
        if self._subscriber_task is not None:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass
            self._subscriber_task = None

        if self._pubsub is not None:
            await self._pubsub.close()
            self._pubsub = None

        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    async def _subscribe_loop(self) -> None:
        """Pub/Subメッセージを受信してローカルのWebSocketに送信。"""
        if self._pubsub is None:
            return

        # 全イベントチャンネルを購読（パターンマッチ）
        await self._pubsub.psubscribe("event:*")

        try:
            async for message in self._pubsub.listen():
                if message["type"] != "pmessage":
                    continue

                channel = message["channel"]  # e.g., "event:evt_123"
                data_str = message["data"]

                # チャンネル名からevent_idを抽出
                if not channel.startswith("event:"):
                    continue
                event_id = channel[6:]  # "event:"を除去

                # メッセージをデシリアライズ
                try:
                    payload = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                # ローカル接続にブロードキャスト
                await self._local_broadcast(event_id, payload)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[ValkeyManager] Subscribe loop error: {e}")

    async def _local_broadcast(self, event_id: str, payload: dict) -> None:
        """ローカルのWebSocket接続に送信。"""
        conns = self._connections.get(event_id, {})
        for ws in list(conns.values()):
            try:
                await ws.send_json(payload)
            except Exception:
                pass

    # ── 接続管理 ───────────────────────────────────────

    async def connect(
        self,
        event_id: str,
        session_id: str,
        websocket: WebSocket,
    ) -> None:
        """WebSocket接続を受け入れてローカルに保存。"""
        await websocket.accept()
        self._connections.setdefault(event_id, {})[session_id] = websocket

    def disconnect(self, event_id: str, session_id: str) -> None:
        """WebSocket接続を切断。"""
        conns = self._connections.get(event_id)
        if conns and session_id in conns:
            del conns[session_id]

    # ── ブロードキャスト ───────────────────────────────

    async def broadcast(self, event_id: str, payload: dict) -> None:
        """イベント内の全クライアントにメッセージ送信（全ECSタスク経由）。

        Valkey Pub/Subを使って全タスクに配信。
        """
        redis = await self._get_redis()
        channel = f"event:{event_id}"
        message = json.dumps(payload)
        await redis.publish(channel, message)

    async def broadcast_question(
        self,
        event_id: str,
        payload: dict,
    ) -> dict[str, str]:
        """問題配信用ブロードキャスト。

        Pub/Subで配信し、ローカル接続のdelivered_atを記録してValkeyに保存。
        """
        redis = await self._get_redis()
        channel = f"event:{event_id}"
        message = json.dumps(payload)
        await redis.publish(channel, message)

        # ローカル接続のdelivered_atを記録
        delivered_map: dict[str, str] = {}
        conns = self._connections.get(event_id, {})
        now = _now_iso()
        for sid in conns.keys():
            delivered_map[sid] = now
            # Valkeyに保存: delivered:{event_id}:{session_id}
            key = f"delivered:{event_id}:{sid}"
            await redis.set(key, now, ex=3600)  # 1時間で自動削除

        return delivered_map

    # ── delivered_at 管理 ──────────────────────────────

    async def get_delivered_at(self, event_id: str, session_id: str) -> str | None:
        """Valkeyからdelivered_atを取得。"""
        redis = await self._get_redis()
        key = f"delivered:{event_id}:{session_id}"
        value = await redis.get(key)
        return value

    async def clear_delivered_at(self, event_id: str) -> None:
        """イベントのdelivered_atを全削除。"""
        redis = await self._get_redis()
        # パターンマッチで削除
        pattern = f"delivered:{event_id}:*"
        async for key in redis.scan_iter(match=pattern):
            await redis.delete(key)


# グローバルインスタンス（main.pyで初期化）
valkey_manager: ValkeyConnectionManager | None = None


def get_valkey_manager(redis_url: str) -> ValkeyConnectionManager:
    """Valkeyマネージャーのシングルトンインスタンスを取得。"""
    global valkey_manager
    if valkey_manager is None:
        valkey_manager = ValkeyConnectionManager(redis_url)
    return valkey_manager
