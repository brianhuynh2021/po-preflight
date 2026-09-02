from __future__ import annotations

import os
import unittest
from unittest.mock import patch

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
        self.assertEqual(res.json().get("code"), "UNAUTHORIZED")

    def test_rbac_role_hierarchy_viewer_forbidden_to_approve(self):
        """Test VIEWER role is blocked from manager-level decision actions (403 Forbidden)."""
        # Viewer key
        headers = {"X-API-Key": "pf_dev_view_6604"}
        res = self.client.post(
            "/api/v1/orders/1/decide",
            json={"decision": "approved", "actor": "viewer_user"},
            headers=headers,
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json().get("code"), "FORBIDDEN")

    def test_auth_fail_closed_default_without_token_returns_401(self):
        """Test missing token returns 401 Unauthorized under default auth_required=true."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PREFLIGHT_AUTH_REQUIRED", None)
            res = self.client.post(
                "/api/v1/orders/1/decide",
                json={"decision": "approved", "actor": "anonymous_attacker"},
            )
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json().get("code"), "UNAUTHORIZED")

    def test_production_mode_rejects_open_auth_flag_returns_401(self):
        """Test setting PREFLIGHT_AUTH_REQUIRED=false in PRODUCTION still returns 401 Unauthorized."""
        with patch.dict(
            os.environ,
            {"PREFLIGHT_ENV": "production", "PREFLIGHT_AUTH_REQUIRED": "false"},
            clear=False,
        ):
            res = self.client.post(
                "/api/v1/orders/1/decide",
                json={"decision": "approved", "actor": "anonymous_user"},
            )
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json().get("code"), "UNAUTHORIZED")

    def test_production_mode_does_not_load_dev_keys(self):
        """Test dev keys (pf_dev_*) are NOT loaded into registry when PREFLIGHT_ENV=production."""
        with patch.dict(os.environ, {"PREFLIGHT_ENV": "production"}, clear=False):
            registry = get_api_key_registry()
            self.assertNotIn("pf_dev_adm_9901", registry)
            self.assertNotIn("pf_dev_mgr_8802", registry)
            self.assertNotIn("pf_dev_view_6604", registry)

    def test_production_mode_loads_explicit_env_keys(self):
        """Test explicit environment keys are loaded in production."""
        with patch.dict(
            os.environ,
            {
                "PREFLIGHT_ENV": "production",
                "PREFLIGHT_ADMIN_KEY": "prod_secret_admin_key_8899",
            },
            clear=False,
        ):
            registry = get_api_key_registry()
            self.assertIn("prod_secret_admin_key_8899", registry)
            self.assertEqual(registry["prod_secret_admin_key_8899"][1], Role.ADMIN)

    def test_rate_limiter_triggers_429(self):
        """Test exceeding rate limit returns 429 Too Many Requests."""
        global_rate_limiter.path_limits["/api/v1/orders"] = 3
        headers = {"X-API-Key": "test_client_key_rl"}

        # First 3 requests succeed
        for _ in range(3):
            res = self.client.get("/api/v1/orders", headers=headers)
            self.assertEqual(res.status_code, 200)

        # 4th request must be rate-limited (429)
        res_limit = self.client.get("/api/v1/orders", headers=headers)
        self.assertEqual(res_limit.status_code, 429)
        self.assertEqual(res_limit.json().get("code"), "RATE_LIMITED")
        self.assertEqual(res_limit.headers.get("Retry-After"), "60")

    def test_rate_limiter_cannot_be_bypassed_with_testclient_header(self):
        """Test header X-API-Key: testclient cannot bypass rate limiter."""
        global_rate_limiter.path_limits["/api/v1/orders"] = 2
        headers = {"X-API-Key": "testclient"}

        # First 2 requests succeed
        for _ in range(2):
            res = self.client.get("/api/v1/orders", headers=headers)
            self.assertEqual(res.status_code, 200)

        # 3rd request MUST be rate limited (429)
        res_limit = self.client.get("/api/v1/orders", headers=headers)
        self.assertEqual(res_limit.status_code, 429)

    def test_production_telegram_webhook_missing_secret_returns_503(self):
        """Test Telegram webhook in production without configured secret token returns 503."""
        with patch.dict(
            os.environ,
            {"PREFLIGHT_ENV": "production", "TELEGRAM_WEBHOOK_SECRET": "", "TELEGRAM_SECRET_TOKEN": ""},
            clear=False,
        ):
            res = self.client.post("/api/v1/bot/telegram/webhook", json={})
            self.assertEqual(res.status_code, 503)
            self.assertIn("Telegram webhook secret token is not configured", res.json().get("detail", ""))

    def test_production_zalo_webhook_missing_secret_returns_503(self):
        """Test Zalo webhook in production without configured secret key returns 503."""
        with patch.dict(
            os.environ,
            {"PREFLIGHT_ENV": "production", "ZALO_SECRET_KEY": ""},
            clear=False,
        ):
            res = self.client.post("/api/v1/bot/zalo/webhook", json={})
            self.assertEqual(res.status_code, 503)
            self.assertIn("Zalo webhook secret key is not configured", res.json().get("detail", ""))


if __name__ == "__main__":
    unittest.main()
