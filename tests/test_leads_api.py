from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import get_db_path
from preflight.store import AuditStore


class TestLeadsAPI(unittest.TestCase):
    def setUp(self):
        from preflight.api.routes.leads import _ip_requests
        _ip_requests.clear()
        self.client = TestClient(app)

    def test_submit_lead_success(self):
        payload = {
            "name": "Nguyễn Văn A",
            "company": "Công ty TNHH Phân Phối Việt",
            "phone": "0987654321",
            "email": "nguyenvana@phanphoiviet.vn",
            "erp": "MISA AMIS",
            "volume": "100-500 đơn/ngày",
            "note": "Cần tích hợp thử nghiệm trong tháng 10.",
        }
        res = self.client.post("/api/v1/leads", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("Đã nhận", data.get("message", ""))
        self.assertIn("lead", data)
        self.assertEqual(data["lead"]["name"], "Nguyễn Văn A")
        self.assertEqual(data["lead"]["company"], "Công ty TNHH Phân Phối Việt")

    def test_submit_lead_honeypot_silently_ignored(self):
        payload = {
            "name": "Spam Bot",
            "company": "Spam Corp",
            "phone": "0123456789",
            "email": "bot@spam.com",
            "website": "http://spam-link.com",  # Honeypot filled!
        }
        res = self.client.post("/api/v1/leads", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))

    def test_submit_lead_rate_limit(self):
        payload = {
            "name": "Thử Nghiệm Rate Limit",
            "company": "Test Company",
            "phone": "0912345678",
            "email": "test@example.com",
        }

        for i in range(5):
            res = self.client.post("/api/v1/leads", json=payload)
            self.assertEqual(res.status_code, 201)

        # 6th request from same IP should get 429
        res = self.client.post("/api/v1/leads", json=payload)
        self.assertEqual(res.status_code, 429)
        self.assertIn("RATE_LIMITED", res.text)


if __name__ == "__main__":
    unittest.main()
