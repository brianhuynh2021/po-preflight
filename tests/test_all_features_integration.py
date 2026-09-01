import os
import unittest
from decimal import Decimal
from pathlib import Path
from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import get_audit_store, get_catalog
from preflight.currency import fx_engine
from preflight.rag.matcher import HybridSKUMatcher
from preflight.store import AuditStore


class TestAllFeaturesIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = "runtime/test_all_features.db"
        Path(self.db_path).unlink(missing_ok=True)
        self.store = AuditStore(self.db_path)
        self.catalog = get_catalog()
        app.dependency_overrides[get_audit_store] = lambda: self.store
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.store.close()
        Path(self.db_path).unlink(missing_ok=True)

    def test_issue_43_telegram_webhook_secret_verification(self):
        """Test Telegram webhook secret token header guard prevents spoofed webhooks."""
        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "super_secret_12345"

        # 1. Missing secret token -> 403 Forbidden
        res_fail = self.client.post("/api/v1/bot/telegram/webhook", json={"update_id": 1})
        self.assertEqual(res_fail.status_code, 403)
        self.assertIn("Invalid or missing Telegram webhook secret", res_fail.json()["detail"])

        # 2. Wrong secret token -> 403 Forbidden
        res_wrong = self.client.post(
            "/api/v1/bot/telegram/webhook",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"},
        )
        self.assertEqual(res_wrong.status_code, 403)

        # 3. Valid secret token -> 200 OK
        res_ok = self.client.post(
            "/api/v1/bot/telegram/webhook",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "super_secret_12345"},
        )
        self.assertEqual(res_ok.status_code, 200)

        # Cleanup
        del os.environ["TELEGRAM_WEBHOOK_SECRET"]

    def test_issue_44_sse_realtime_stream(self):
        """Test Server-Sent Events (SSE) EventBus pub/sub and generator."""
        import asyncio
        from preflight.api.events import EventBus

        bus = EventBus()
        q = bus.subscribe()
        bus.publish("order.created", {"po_number": "PO-TEST-99", "status": "ready"})

        self.assertEqual(q.qsize(), 1)
        item = q.get_nowait()
        self.assertEqual(item["event"], "order.created")
        self.assertEqual(item["data"]["po_number"], "PO-TEST-99")

        bus.unsubscribe(q)
        self.assertEqual(len(bus._subscribers), 0)

    def test_issue_45_sku_active_learning_alias_store(self):
        """Test active learning alias memory records and resolves customer nicknames."""
        matcher = HybridSKUMatcher(self.catalog, store=self.store)

        # 1. Learn alias for customer 'VinGroup'
        matcher.learn_alias(
            customer_id="VinGroup",
            raw_query="cục chuyển đổi type c nhiều cổng",
            target_sku="DOCK-USBC",
        )

        # 2. Lookup alias via store
        learned = self.store.get_customer_alias("VinGroup", "cục chuyển đổi type c nhiều cổng")
        self.assertEqual(learned, "DOCK-USBC")

        # 3. Resolve via matcher with customer context -> 100% Tier 1 Exact / Tier 0 Match
        result = matcher.resolve("cục chuyển đổi type c nhiều cổng", customer_id="VinGroup")
        self.assertEqual(result.matched_sku, "DOCK-USBC")
        self.assertEqual(result.confidence_score, 1.0)
        self.assertIn("Customer Active Learning", result.explanation)

        # 4. API endpoint to list aliases
        res_aliases = self.client.get("/api/v1/sku/aliases?customer_id=VinGroup")
        self.assertEqual(res_aliases.status_code, 200)
        aliases = res_aliases.json()
        self.assertTrue(any(a["target_sku"] == "DOCK-USBC" for a in aliases))

    def test_issue_46_dynamic_fx_engine(self):
        """Test dynamic currency exchange rate caching and fallback."""
        rate = fx_engine.get_rate("USD", "VND")
        self.assertGreater(rate, 20000.0)

        converted = fx_engine.convert(100.0, "USD", "VND")
        self.assertEqual(converted, 100.0 * rate)

        # Test API endpoint
        res = self.client.get("/api/v1/currency/rate?base=USD&target=VND")
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertEqual(payload["base"], "USD")
        self.assertEqual(payload["target"], "VND")
        self.assertGreater(payload["rate"], 20000.0)

        # Test cross-currency order evaluation in rules engine (PO in USD vs Catalog in VND)
        from preflight.models import Order, LineItem
        from preflight.rules import analyze_order
        usd_order = Order(
            po_number="PO-USD-CROSS-BORDER",
            customer="Global Retail Inc",
            items=(
                # 18.5M VND is approx $728 USD at 25.4k. If PO specifies $728, tolerance passes.
                LineItem(sku="LAPTOP-A14", quantity=1, unit_price=Decimal("728.35")),
            ),
            currency="USD",
        )
        analysis = analyze_order(usd_order, self.catalog, price_tolerance_percent=Decimal("5"))
        # Should be ready for approval without price mismatch error
        self.assertEqual(analysis.status, "ready_for_approval")
        self.assertEqual(len(analysis.findings), 0)


if __name__ == "__main__":
    unittest.main()
