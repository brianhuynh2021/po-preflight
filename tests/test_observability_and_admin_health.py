import json
import logging
import os
import unittest
from decimal import Decimal
from unittest.mock import patch

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.observability.context import (
    get_order_id,
    get_request_id,
    get_user_id,
    set_order_id,
    set_request_id,
    set_user_id,
)
from preflight.observability.logging import ColoredLogFormatter, JsonLogFormatter, configure_logging
from preflight.observability.metrics import PrometheusMetricsRegistry
from preflight.observability.tracing import is_otel_enabled, trace_span
from preflight.security.rbac import Role, UserPrincipal
from preflight.security.session import create_session_token
from preflight.store import AuditStore


class TestObservabilityAndAdminHealth(unittest.TestCase):
    def setUp(self):
        self.db_path = "runtime/test_observability.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.store = AuditStore(self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_context_vars(self):
        set_request_id("req-12345")
        set_user_id("admin_user")
        set_order_id("PO-9999")

        self.assertEqual(get_request_id(), "req-12345")
        self.assertEqual(get_user_id(), "admin_user")
        self.assertEqual(get_order_id(), "PO-9999")

    def test_json_log_formatter(self):
        formatter = JsonLogFormatter()
        set_request_id("req-abc")
        set_user_id("auditor_01")
        set_order_id("PO-8888")

        record = logging.LogRecord(
            name="preflight.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="Order %s verified",
            args=("PO-8888",),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["message"], "Order PO-8888 verified")
        self.assertEqual(data["request_id"], "req-abc")
        self.assertEqual(data["user_id"], "auditor_01")
        self.assertEqual(data["order_id"], "PO-8888")
        self.assertIn("timestamp", data)

    def test_colored_log_formatter(self):
        formatter = ColoredLogFormatter()
        set_request_id("req-xyz")
        set_user_id("dev_user")
        set_order_id("PO-1111")

        record = logging.LogRecord(
            name="preflight.test",
            level=logging.WARNING,
            pathname=__file__,
            lineno=20,
            msg="Price variance detected",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        self.assertIn("WARN", formatted)
        self.assertIn("Price variance detected", formatted)
        self.assertIn("req_id=req-xyz", formatted)

    def test_trace_span_fallback_no_op(self):
        with trace_span("test_span", {"test_attr": "value"}) as span:
            # Span is None when OpenTelemetry is not active, but shouldn't raise
            self.assertIsNone(span)

    def test_metrics_registry(self):
        registry = PrometheusMetricsRegistry()
        registry.record_http_request("GET", "/api/v1/orders", 200, 0.025)
        registry.record_order_processed("ready_for_approval", "LOW")
        registry.record_finding("PRICE_MISMATCH", "warning")
        registry.record_analysis_duration(0.012)
        registry.record_sku_resolution("exact")
        registry.record_erp_sync("SAP", True)
        registry.record_outbox_pending(3, 120.5)

        prom_text = registry.generate_prometheus_text()
        self.assertIn("po_preflight_uptime_seconds", prom_text)
        self.assertIn('po_preflight_http_requests_total{method="GET",path="/api/v1/orders",status="200"} 1', prom_text)
        self.assertIn('po_preflight_orders_processed_total{status="ready_for_approval",risk_level="LOW"} 1', prom_text)
        self.assertIn('po_preflight_findings_total{code="PRICE_MISMATCH",severity="warning"} 1', prom_text)
        self.assertIn("po_preflight_analysis_duration_seconds", prom_text)
        self.assertIn('po_preflight_sku_resolutions_total{tier="exact"} 1', prom_text)
        self.assertIn('po_preflight_erp_sync_total{adapter="SAP",status="success"} 1', prom_text)
        self.assertIn("po_preflight_outbox_pending_count 3", prom_text)
        self.assertIn("po_preflight_outbox_pending_max_age_seconds 120.50", prom_text)

    def test_store_request_errors(self):
        self.store.record_request_error(
            request_id="req-err-01",
            endpoint="POST /api/v1/orders/upload",
            status_code=500,
            error_message="Database lock timeout",
            traceback_str="Traceback (most recent call last)...",
        )

        errors = self.store.get_recent_request_errors(limit=10)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["request_id"], "req-err-01")
        self.assertEqual(errors[0]["status_code"], 500)
        self.assertEqual(errors[0]["error_message"], "Database lock timeout")

    def test_admin_health_api_endpoint(self):
        # Generate admin JWT
        admin_token = create_session_token(UserPrincipal(username="admin_test", role=Role.ADMIN, api_key_id="session"))

        res = self.client.get(
            "/api/v1/admin/health",
            cookies={"pf_session": admin_token},
            headers={"X-Request-ID": "req-admin-health-001"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn(data["status"], ["healthy", "degraded", "unhealthy"])
        self.assertIn("database", data)
        self.assertIn("latency_ms", data["database"])
        self.assertIn("outbox", data)
        self.assertIn("inventory", data)
        self.assertIn("recent_errors", data)
        self.assertEqual(res.headers.get("X-Request-ID"), "req-admin-health-001")


if __name__ == "__main__":
    unittest.main()
