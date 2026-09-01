from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from preflight.api.events import event_bus

router = APIRouter(prefix="/api/v1/events", tags=["Real-Time Stream (Server-Sent Events)"])


@router.get(
    "/stream",
    summary="Real-Time SSE Event Stream",
    description="Subscribe to live real-time server-sent events for PO uploads, status changes, human decisions, and ERP synchronization.",
)
async def event_stream() -> StreamingResponse:
    return StreamingResponse(
        event_bus.event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/orders",
    summary="Orders Live Event Stream (Alias)",
    description="Stream live order-related state transitions.",
)
async def orders_event_stream() -> StreamingResponse:
    return await event_stream()
