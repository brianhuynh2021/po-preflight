from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.api.events import EventBus
from preflight.erp.adapters.sap import MockSAPAdapter
from preflight.erp.outbox import ERPEventStatus, ERPSyncPayload, OutboxStore
from preflight.erp.worker import OutboxSyncWorker
from preflight.jobs.definitions import (
    analyze_order,
    email_poll,
    inventory_sync,
    notify,
    outbox_dispatch,
    run_ocr,
)
from preflight.jobs.queue import enqueue_job, get_queue_mode, sync_enqueue_job
from preflight.models import Analysis, LineItem, Order, Product
from preflight.security.rate_limiter import SlidingWindowRateLimiter
from preflight.security.rbac import Role, UserPrincipal
from preflight.security.session import create_session_token
from preflight.store import AuditStore


# 1x1 Transparent PNG bytes
MINIMAL_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class TestC2JobsAndRedis(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_c2.db"
        self.store = AuditStore(self.db_path)
        from preflight.api.deps import get_audit_store, get_store
        app.dependency_overrides[get_audit_store] = lambda: self.store
        app.dependency_overrides[get_store] = lambda: self.store
        self.admin_token = create_session_token(
            UserPrincipal(username="admin_c2", role=Role.ADMIN, api_key_id="session")
        )
        self.client = TestClient(app, cookies={"pf_session": self.admin_token})

    def tearDown(self):
        app.dependency_overrides.clear()
        self.store.close()
        self.temp_dir.cleanup()

    def test_criterion_a_upload_png_returns_202_and_worker_ocr_analyzes(self):
        """Criterion a: upload PNG -> 202 Accepted, then worker run_ocr -> status analyzed, SSE receives 'order.analyzed'."""
        # 1. Upload PNG
        res = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("invoice_photo.png", MINIMAL_PNG_BYTES, "image/png")},
        )
        self.assertEqual(res.status_code, 202)
        data = res.json()
        self.assertEqual(data["status"], "received")
        self.assertIn("order_id", data)
        self.assertIn("sse_channel", data)
        order_id = data["order_id"]

        # Verify in DB: order is recorded with status 'received'
        db_order = self.store.get_order(str(order_id))
        self.assertIsNotNone(db_order)
        self.assertEqual(db_order["status"], "received")

        # 2. Simulate worker executing run_ocr
        # Mock OCR pipeline to return a parsed domain order
        mock_order = Order(
            po_number="PO-OCR-8822",
            customer="Northstar Retail",
            items=[LineItem(sku="LAPTOP-A14", quantity=1, unit_price=Decimal("18500000"))],
            currency="VND",
        )
        mock_pipeline = MagicMock()
        mock_pipeline.process_file_bytes.return_value = (MagicMock(), mock_order)

        # Capture SSE events
        received_events = []
        from preflight.api.events import event_bus
        orig_publish = event_bus.publish

        def mock_pub(evt_type, evt_data):
            received_events.append((evt_type, evt_data))
            orig_publish(evt_type, evt_data)

        with patch("preflight.jobs.definitions.IntelligentIngestionPipeline", return_value=mock_pipeline), \
             patch.object(event_bus, "publish", side_effect=mock_pub):

            # Run worker OCR job
            ctx = {"store": self.store, "catalog": {"LAPTOP-A14": Product(sku="LAPTOP-A14", name="Laptop", unit_price=Decimal("18500000"), stock=10)}}
            temp_file = Path(self.temp_dir.name) / "test.png"
            temp_file.write_bytes(MINIMAL_PNG_BYTES)

            job_res = asyncio.run(run_ocr(ctx, order_id=order_id, file_path=str(temp_file), filename="invoice_photo.png"))

            # 3. Assert status is now analyzed (ready_for_approval)
            self.assertEqual(job_res["status"], "ready_for_approval")
            self.assertEqual(job_res["po_number"], "PO-OCR-8822")

            # Verify updated in DB
            updated_order = self.store.get_order(str(order_id))
            self.assertEqual(updated_order["status"], "ready_for_approval")
            self.assertEqual(updated_order["po_number"], "PO-OCR-8822")

            # Verify SSE received 'order.analyzed'
            analyzed_events = [e for e in received_events if e[0] == "order.analyzed"]
            self.assertTrue(len(analyzed_events) > 0)
            self.assertEqual(analyzed_events[0][1]["order_id"], order_id)
            self.assertEqual(analyzed_events[0][1]["status"], "ready_for_approval")

    def test_deterministic_upload_sync_returns_201(self):
        """Deterministic uploads (JSON/CSV/Excel) continue synchronous fast-path returning 201."""
        payload = {
            "po_number": "PO-SYNC-001",
            "customer": "Northstar Retail",
            "currency": "VND",
            "total": 18500000,
            "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000}],
        }
        res = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order.json", json.dumps(payload).encode("utf-8"), "application/json")},
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["po_number"], "PO-SYNC-001")
        self.assertIn("ready", data["status"])

    def test_criterion_b_multi_process_event_bus_redis_pubsub(self):
        """Criterion b: SSE from Process A receives event published from Process B via Redis channel."""
        mock_redis_server = {}

        class FakeSyncRedis:
            def __init__(self, *args, **kwargs):
                pass
            def ping(self):
                return True
            def publish(self, channel, message):
                mock_redis_server.setdefault(channel, []).append(message)
                return 1

        # Process A EventBus & Process B EventBus
        bus_a = EventBus(redis_url="redis://localhost:6379/0")
        bus_a._sync_redis = FakeSyncRedis()
        bus_a._is_redis_active = True

        bus_b = EventBus(redis_url="redis://localhost:6379/0")
        bus_b._sync_redis = FakeSyncRedis()
        bus_b._is_redis_active = True

        # Process B subscribes to SSE
        q_b = bus_b.subscribe()

        # Process A publishes event
        bus_a.publish("order.created", {"po_number": "PO-REDIS-99", "status": "Ready"})

        # Verify published to Redis channel
        self.assertIn("preflight:events", mock_redis_server)
        raw_msg = mock_redis_server["preflight:events"][-1]
        data = json.loads(raw_msg)
        self.assertEqual(data["event"], "order.created")
        self.assertEqual(data["data"]["po_number"], "PO-REDIS-99")

        # Simulate Redis pubsub dispatching into Process B
        bus_b._dispatch_local(data)

        # Process B queue receives the message
        received = q_b.get_nowait()
        self.assertEqual(received["event"], "order.created")
        self.assertEqual(received["data"]["po_number"], "PO-REDIS-99")

        # Single process fallback check
        bus_standalone = EventBus(redis_url="")
        self.assertEqual(bus_standalone.mode, "single_process")

    def test_criterion_c_outbox_worker_crash_recovers_stale_leases(self):
        """Criterion c: worker dies mid-dispatch -> event returns to PENDING after lease timeout, without duplicate send."""
        outbox_db = Path(self.temp_dir.name) / "outbox_test.db"
        outbox_store = OutboxStore(outbox_db)

        # 1. Enqueue an ERP event
        payload = outbox_store.enqueue_order(
            po_number="PO-CRASH-01",
            customer="Vingroup Retail",
            total_amount=Decimal("50000000"),
            currency="VND",
            items=[{"sku": "LAPTOP-A14", "quantity": 2, "unit_price": "25000000"}],
            idempotency_key="idemp-crash-01",
        )

        # 2. Worker 1 fetches pending -> transitions status to PROCESSING
        claimed = outbox_store.fetch_pending(limit=1)
        self.assertEqual(len(claimed), 1)
        self.assertEqual(claimed[0].event_id, payload.event_id)

        # Verify in DB: status is PROCESSING
        stats = outbox_store.get_stats()
        self.assertEqual(stats.processing_count, 1)
        self.assertEqual(stats.pending_count, 0)

        # 3. Simulate Worker 1 crashing mid-flight (never calling mark_sent or mark_failed)
        # Advance time by manually setting updated_at to 120 seconds ago
        stale_time = time.time() - 120.0
        with outbox_store.conn:
            outbox_store.conn.execute(
                "UPDATE erp_outbox SET updated_at = ? WHERE event_id = ?",
                (stale_time, payload.event_id),
            )

        # 4. Worker 2 runs outbox_dispatch with 60s lease timeout
        worker2 = OutboxSyncWorker(outbox_store=outbox_store, adapter=MockSAPAdapter())
        responses = worker2.process_batch(limit=10, lease_seconds=60.0)

        # 5. Verify Worker 2 recovered the stale lease and dispatched successfully
        self.assertEqual(len(responses), 1)
        self.assertTrue(responses[0].success)
        self.assertEqual(responses[0].idempotency_key, "idemp-crash-01")

        # Verify DB: status is now SENT, no duplicates, no missing events
        stats_final = outbox_store.get_stats()
        self.assertEqual(stats_final.sent_count, 1)
        self.assertEqual(stats_final.processing_count, 0)
        self.assertEqual(stats_final.pending_count, 0)

    def test_redis_backed_rate_limiter_and_in_memory_fallback(self):
        """Rate limiter uses sliding window with Redis or fallback in-memory."""
        limiter = SlidingWindowRateLimiter(default_limit=3, window_seconds=60)
        self.assertEqual(limiter.mode, "in_memory")

        # 3 requests allowed
        self.assertTrue(limiter.is_allowed("client-1")[0])
        self.assertTrue(limiter.is_allowed("client-1")[0])
        self.assertTrue(limiter.is_allowed("client-1")[0])

        # 4th request blocked
        allowed, rem = limiter.is_allowed("client-1")
        self.assertFalse(allowed)
        self.assertEqual(rem, 0)

        # Another client still allowed
        self.assertTrue(limiter.is_allowed("client-2")[0])

    def test_dead_letter_records_error_to_request_errors(self):
        """Dead-letter job logs failure to request_errors table on final retry."""
        ctx = {"store": self.store, "job_id": "job-failing-99", "job_try": 3, "max_retries": 3}

        # Run analyze_order on non-existent order
        with self.assertRaises(ValueError):
            asyncio.run(analyze_order(ctx, order_id=999999))

        errors = self.store.get_recent_request_errors(limit=5)
        self.assertTrue(len(errors) > 0)
        dl_err = errors[0]
        self.assertIn("job:job-failing-99", dl_err["request_id"])
        self.assertIn("Dead-letter", dl_err["error_message"])

    def test_system_modes_endpoint_reports_c2_modes(self):
        """GET /api/v1/system/modes returns sse, queue, and rate_limiter."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/0"}):
            res = self.client.get("/api/v1/system/modes")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["sse"], "redis_pubsub")
            self.assertEqual(data["queue"], "arq_redis")
            self.assertEqual(data["rate_limiter"], "redis")

        with patch.dict(os.environ, {"REDIS_URL": ""}):
            res = self.client.get("/api/v1/system/modes")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["sse"], "single_process")
            self.assertEqual(data["queue"], "in_memory")
            self.assertEqual(data["rate_limiter"], "in_memory")


if __name__ == "__main__":
    unittest.main()
