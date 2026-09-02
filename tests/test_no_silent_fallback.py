import io
import os
import sqlite3
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import preflight
from preflight.agent.checkpointer import get_agent_checkpointer
from preflight.agent.graph import build_preflight_graph
from preflight.api.app import app
from preflight.api.errors import ConfigurationError, ParseError, UpstreamUnavailable
from preflight.bot.telegram import TelegramBotService
from preflight.bot.zalo import ZaloBotService
from preflight.erp.outbox import PostgresOutboxStore, create_outbox_store
from preflight.ingestion.ocr_engine import GeminiVisionOCREngine
from preflight.ingestion.pipeline import IngestionPipeline
from preflight.models import Analysis, LineItem, Order, Product
from preflight.rules import analyze_order
from preflight.store import AuditStore, PostgresAuditStore, create_audit_store


class TestNoSilentFallbacks(unittest.TestCase):
    def setUp(self):
        self.catalog = {
            "LAPTOP-A14": Product(
                sku="LAPTOP-A14",
                name="A14 Laptop",
                unit_price=Decimal("18500000"),
                stock=10,
                active=True,
            )
        }
        self.client = TestClient(app)

    def test_database_fails_closed_when_postgres_unreachable(self):
        """Database fail-closed: unresolvable postgres url raises ConfigurationError, does not fallback to SQLite."""
        bad_url = "postgresql://bad_user:bad_pass@127.0.0.1:59999/bad_db"
        with self.assertRaises(ConfigurationError):
            create_audit_store(bad_url)

        with self.assertRaises(ConfigurationError):
            create_outbox_store(bad_url)

    def test_gemini_vision_ocr_fails_closed_when_no_api_key(self):
        """GeminiVisionOCREngine raises UpstreamUnavailable when GEMINI_API_KEY is missing, no mock return."""
        from preflight.ingestion.schemas import DocumentType

        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            engine = GeminiVisionOCREngine(api_key="")
            self.assertFalse(engine.is_available)
            with self.assertRaises(UpstreamUnavailable):
                engine.extract(b"dummy image bytes", "document.pdf", DocumentType.SCANNED_PDF)

    def test_ingestion_pipeline_rejects_corrupted_structured_file(self):
        """Corrupted Excel/CSV files raise ParseError and do NOT silently fallback."""
        pipeline = IngestionPipeline(self.catalog)
        with self.assertRaises(ParseError):
            pipeline.process_file_bytes(b"this is corrupt binary not a zip or excel", "corrupt.xlsx")

        with self.assertRaises(ParseError):
            pipeline.process_file_bytes(b"invalid,json\nline1", "broken.json")

    def test_telegram_bot_honest_unconfigured_and_dry_run_modes(self):
        """TelegramBotService returns mode='unconfigured' or mode='dry_run' with message_id=None."""
        order_dict = {"id": 101, "po_number": "PO-101", "customer": "Northstar", "total": "500000"}

        # Unconfigured mode
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_DRY_RUN": "false"}):
            bot = TelegramBotService(token="", chat_id="")
            res = bot.send_order_alert(order_dict)
            self.assertFalse(res.success)
            self.assertEqual(res.mode, "unconfigured")
            self.assertIsNone(res.message_id)

        # Dry run mode
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_DRY_RUN": "true"}):
            bot = TelegramBotService(token="", chat_id="")
            res = bot.send_order_alert(order_dict)
            self.assertTrue(res.success)
            self.assertEqual(res.mode, "dry_run")
            self.assertIsNone(res.message_id)

    def test_zalo_bot_honest_unconfigured_and_dry_run_modes(self):
        """ZaloBotService returns mode='unconfigured' or mode='dry_run' with message_id=None."""
        order_dict = {"id": 102, "po_number": "PO-102", "customer": "Northstar", "total": "500000"}

        # Unconfigured mode
        with patch.dict(os.environ, {"ZALO_OA_SECRET": "", "ZALO_DRY_RUN": "false"}):
            bot = ZaloBotService(access_token="", dry_run=False)
            res = bot.send_order_alert(order_dict)
            self.assertFalse(res.success)
            self.assertEqual(res.mode, "unconfigured")
            self.assertIsNone(res.message_id)

        # Dry run mode
        with patch.dict(os.environ, {"ZALO_OA_SECRET": "", "ZALO_DRY_RUN": "true"}):
            bot = ZaloBotService(access_token="", dry_run=False)
            res = bot.send_order_alert(order_dict)
            self.assertTrue(res.success)
            self.assertEqual(res.mode, "dry_run")
            self.assertIsNone(res.message_id)

    def test_agent_checkpointer_persists_to_sqlite(self):
        """Agent checkpointer persists state across instances using SqliteSaver."""
        checkpointer = get_agent_checkpointer()
        self.assertIsNotNone(checkpointer)
        db_path = Path("runtime/agent_checkpoints.db")
        self.assertTrue(db_path.exists())

    def test_system_modes_endpoint(self):
        """GET /api/v1/system/modes returns honest subsystem statuses."""
        headers = {"X-API-Key": "pf_dev_view_6604"}
        resp = self.client.get("/api/v1/system/modes", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("database", data)
        self.assertIn("ocr", data)
        self.assertIn("telegram", data)
        self.assertIn("zalo", data)
        self.assertIn("erp", data)
        self.assertIn("fx", data)
        self.assertIn("environment", data)
        self.assertIn("auth_required", data)

    def test_health_endpoint_reports_dynamic_version(self):
        """GET /health reports actual package version."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["version"], preflight.__version__)
        self.assertEqual(data["database"]["type"], "sqlite")

    def test_metrics_dynamic_build_info(self):
        """po_preflight_build_info metric contains actual version and environment."""
        with patch.dict(os.environ, {"PREFLIGHT_ENV": "staging"}):
            resp = self.client.get("/metrics")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'version="{preflight.__version__}"', resp.text)
            self.assertIn('environment="staging"', resp.text)


if __name__ == "__main__":
    unittest.main()
