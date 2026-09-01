from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncGenerator


class EventBus:
    """Lightweight in-memory asynchronous pub/sub broadcaster for real-time SSE streams."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(q)

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": time.time(),
        }
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                self._subscribers.discard(q)

    async def event_generator(self) -> AsyncGenerator[str, None]:
        q = self.subscribe()
        try:
            init_payload = {"event": "connected", "data": {"status": "live", "timestamp": time.time()}}
            yield f"data: {json.dumps(init_payload)}\n\n"

            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"event: {payload.get('event', 'message')}\ndata: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    ping = {"event": "ping", "data": {"time": time.time()}}
                    yield f": ping - {json.dumps(ping)}\n\n"
        finally:
            self.unsubscribe(q)


event_bus = EventBus()
