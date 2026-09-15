from datetime import datetime
import os
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.security.rbac import Role, UserPrincipal, get_current_user
from test_banking import case_data


class BankingHTTPTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.payload = case_data()
        self.payload["limit_as_of"] = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
        self.payload["invoices"][0]["issued_on"] = self.payload["limit_as_of"]
        self.payload["contract_valid_until"] = "2099-12-31"

    def tearDown(self):
        app.dependency_overrides.pop(get_current_user, None)
        self.client.close()

    def authenticate(self):
        app.dependency_overrides[get_current_user] = lambda: UserPrincipal("reviewer", Role.VIEWER, "test")

    def test_requires_authentication(self):
        with patch.dict(os.environ, {"PREFLIGHT_AUTH_REQUIRED": "true"}):
            response = self.client.post("/api/v1/banking/analyze", json=self.payload)
        self.assertEqual(response.status_code, 401)

    def test_viewer_can_precheck_without_approval_or_persistence(self):
        self.authenticate()
        response = self.client.post("/api/v1/banking/analyze", json=self.payload)
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["status"], "Ready")
        self.assertEqual(result["available_limit"], "80000000")
        self.assertEqual(result["evaluated_on"], self.payload["limit_as_of"])
        self.assertNotIn("decision_id", result)

    def test_validation_returns_field_errors(self):
        self.authenticate()
        self.payload["requested_amount"] = "NaN"
        response = self.client.post("/api/v1/banking/analyze", json=self.payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("requested_amount", [error["field"] for error in response.json()["errors"]])

    def test_client_cannot_supply_status_or_policy(self):
        self.authenticate()
        self.payload["status"] = "Approved"
        response = self.client.post("/api/v1/banking/analyze", json=self.payload)
        self.assertEqual(response.status_code, 422)

    def test_banking_has_no_approval_endpoint(self):
        self.authenticate()
        response = self.client.post("/api/v1/banking/approve", json=self.payload)
        self.assertEqual(response.status_code, 404)
