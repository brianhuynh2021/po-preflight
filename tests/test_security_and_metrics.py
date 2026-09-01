from __future__ import annotations

import os
import unittest

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.security.rate_limiter import global_rate_limiter
from preflight.security.rbac import Role, UserPrincipal, get_api_key_registry


class TestSecurityAndMetrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        global_rate_limiter.reset()

    def test_prometheus_metrics_endpoint(self):
        """Test GET /metrics returns OpenMetrics formatted Prometheus text."""
        res = self.client.get("/metrics")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/plain", res.headers.get("content-type", ""))
        body = res.text
        self.assertIn("po_preflight_uptime_seconds", body)
        self.assertIn("po_preflight_build_info", body)

    def test_k8s_liveness_and_readiness_probes(self):
        """Test GET /health/live and GET /health/ready."""
        res_live = self.client.get("/health/live")
        self.assertEqual(res_live.status_code, 200)
        self.assertEqual(res_live.json().get("status"), "alive")

        res_ready = self.client.get("/health/ready")
        self.assertEqual(res_ready.status_code, 200)
        self.assertEqual(res_ready.json().get("status"), "ready")
        self.assertIn("database", res_ready.json().get("checks", {}))

    def test_rbac_invalid_api_key_rejected(self):
        """Test invalid X-API-Key returns 401 Unauthorized."""
        res = self.client.post(
            "/api/v1/orders/1/decide",
            json={"decision": "approved", "actor": "tester"},
            headers={"X-API-Key": "invalid_bogus_key_12345"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("Invalid or expired API Key", res.json().get("detail", ""))

    def test_rbac_role_hierarchy_viewer_forbidden_to_approve(self):
        """Test VIEWER role is blocked from manager-level decision actions (403 Forbidden)."""
        # Viewer key
        headers = {"X-API-Key": "pf_live_view_6604"}
        res = self.client.post(
            "/api/v1/orders/1/decide",
            json={"decision": "approved", "actor": "viewer_user"},
            headers=headers,
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("requires at least 'MANAGER' role", res.json().get("detail", ""))

    def test_rate_limiter_triggers_429(self):
        """Test exceeding rate limit returns 429 Too Many Requests."""
        # Set a small path limit for testing
        global_rate_limiter.path_limits["/api/v1/orders"] = 3
        headers = {"X-API-Key": "test_client_key_rl"}

        # First 3 requests succeed
        for _ in range(3):
            res = self.client.get("/api/v1/orders", headers=headers)
            self.assertEqual(res.status_code, 200)

        # 4th request must be rate-limited (429)
        res_limit = self.client.get("/api/v1/orders", headers=headers)
        self.assertEqual(res_limit.status_code, 429)
        self.assertIn("Rate limit exceeded", res_limit.text)
        self.assertEqual(res_limit.headers.get("Retry-After"), "60")


if __name__ == "__main__":
    unittest.main()
