from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import MagicMock, patch

import openpyxl
from fastapi.testclient import TestClient

from preflight.api.app import app
from preflight.intake.email import (
    EmailAttachment,
    EmailIntakeConfig,
    EmailIntakeService,
    EmailMessageItem,
)
from preflight.models import CustomerMaster
from preflight.store import AuditStore


def create_sample_po_xlsx_bytes(po_number: str = "PO-2026-9999", sku: str = "LAPTOP-A14", qty: int = 2) -> bytes:
    """Helper creating valid PO Excel spreadsheet bytes."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DonHang"
    ws["A1"] = "ĐƠN HÀNG"
    ws["A2"] = "Mã PO:"
    ws["B2"] = po_number
    ws["A3"] = "Khách Hàng:"
    ws["B3"] = "Northstar Retail"
    ws["A4"] = "Tiền Tệ:"
    ws["B4"] = "VND"
    
    ws.append([])
    ws.append(["STT", "Mã SKU", "Tên Hàng", "Số Lượng", "ĐVT", "Đơn Giá", "Thành Tiền"])
    ws.append([1, sku, "Laptop A14 High Performance", qty, "PCS", 18500000, 18500000 * qty])
    
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class MockSMTPClient:
    def __init__(self):
        self.sent_messages = []

    def send_email(self, to_email: str, subject: str, body: str, attachment_path: str | Path | None = None) -> bool:
        self.sent_messages.append({
            "to": to_email,
            "subject": subject,
            "body": body,
            "attachment": str(attachment_path) if attachment_path else None,
        })
        return True


class MockIMAPClient:
    def __init__(self, messages: list[EmailMessageItem] | None = None):
        self.messages = messages or []

    def fetch_messages(self) -> list[EmailMessageItem]:
        return list(self.messages)


class TestEmailIntake(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_email_preflight.db"
        self.catalog_path = Path("examples/catalog.csv")
        self.store = AuditStore(self.db_path)
        self.smtp_client = MockSMTPClient()
        self.service = EmailIntakeService(
            store=self.store,
            smtp_client=self.smtp_client,
        )

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_single_mail_two_xlsx_attachments_creates_two_orders_and_confirms(self):
        """1 email with 2 xlsx attachments -> 2 orders created, status PROCESSED, auto-reply confirmation sent."""
        xlsx_1 = create_sample_po_xlsx_bytes("PO-EMAIL-001", "LAPTOP-A14", 2)
        xlsx_2 = create_sample_po_xlsx_bytes("PO-EMAIL-002", "MOUSE-WL", 5)

        msg = EmailMessageItem(
            message_id="msg-uuid-1001@northstar.vn",
            sender_name="Purchasing Team",
            sender_email="orders@northstar.vn",
            subject="Đơn hàng tháng 9 - Đợt 1",
            date_str=datetime.now(UTC).isoformat(),
            attachments=[
                EmailAttachment(filename="PO_001.xlsx", content_bytes=xlsx_1),
                EmailAttachment(filename="PO_002.xlsx", content_bytes=xlsx_2),
            ],
        )

        result = self.service.process_message(msg, catalog_path=self.catalog_path)

        self.assertEqual(result.status, "PROCESSED")
        self.assertEqual(result.orders_created, 2)
        self.assertEqual(len(result.analysis_ids), 2)
        self.assertEqual(result.customer_resolved, "Northstar Retail")
        self.assertTrue(result.auto_reply_sent)

        # Check DB log
        log = self.store.get_email_inbox_log("msg-uuid-1001@northstar.vn")
        self.assertIsNotNone(log)
        self.assertEqual(log["status"], "PROCESSED")
        self.assertEqual(log["orders_created"], 2)

        # Check SMTP auto-reply sent
        self.assertEqual(len(self.smtp_client.sent_messages), 1)
        sent = self.smtp_client.sent_messages[0]
        self.assertEqual(sent["to"], "orders@northstar.vn")
        self.assertIn("Tiếp nhận PO thành công", sent["subject"])
        self.assertIn("PO-EMAIL-001", sent["body"])
        self.assertIn("PO-EMAIL-002", sent["body"])

    def test_idempotent_processing_duplicate_message_id_skipped(self):
        """Submitting the same message_id twice must be idempotent (no duplicate orders created)."""
        xlsx = create_sample_po_xlsx_bytes("PO-EMAIL-DUP", "LAPTOP-A14", 1)
        msg = EmailMessageItem(
            message_id="unique-msg-id-888@company.com",
            sender_name="Sender",
            sender_email="orders@northstar.vn",
            subject="PO Urgent",
            date_str=datetime.now(UTC).isoformat(),
            attachments=[EmailAttachment(filename="PO_Dup.xlsx", content_bytes=xlsx)],
        )

        res1 = self.service.process_message(msg, catalog_path=self.catalog_path)
        self.assertEqual(res1.status, "PROCESSED")
        self.assertEqual(res1.orders_created, 1)

        # Process same message again
        res2 = self.service.process_message(msg, catalog_path=self.catalog_path)
        self.assertEqual(res2.status, "DUPLICATE")
        self.assertEqual(len(self.smtp_client.sent_messages), 1)  # No second email sent

    def test_invalid_attachment_docx_ignored_and_auto_replies_with_template(self):
        """Email with only .docx attachment -> IGNORED, auto-reply sent with PO_MAU.xlsx template."""
        msg = EmailMessageItem(
            message_id="msg-docx-only@unknown.vn",
            sender_name="Khach Hang",
            sender_email="customer@unknown.vn",
            subject="Gửi đơn hàng bằng Word",
            date_str=datetime.now(UTC).isoformat(),
            attachments=[
                EmailAttachment(filename="DonHang.docx", content_bytes=b"FAKE DOCX BYTES"),
            ],
        )

        res = self.service.process_message(msg, catalog_path=self.catalog_path)
        self.assertEqual(res.status, "IGNORED")
        self.assertEqual(res.orders_created, 0)
        self.assertTrue(res.auto_reply_sent)

        # Check DB log
        log = self.store.get_email_inbox_log("msg-docx-only@unknown.vn")
        self.assertIsNotNone(log)
        self.assertEqual(log["status"], "IGNORED")

        # Check reply attached PO_MAU.xlsx
        self.assertEqual(len(self.smtp_client.sent_messages), 1)
        sent = self.smtp_client.sent_messages[0]
        self.assertEqual(sent["to"], "customer@unknown.vn")
        self.assertIn("Yêu cầu gửi lại đơn hàng", sent["subject"])
        self.assertIn("PO_MAU.xlsx", sent["attachment"])

    def test_customer_resolution_by_contact_emails(self):
        """Sender email in contact_emails maps to corresponding CustomerMaster."""
        # Add new customer with contact email
        cust = CustomerMaster(
            code="CUST-TEST-MAIL",
            name="Công Ty Phân Phối Ánh Dương",
            tax_code="0319998888",
            tier="VIP",
            aliases=["Ánh Dương", "Anh Duong Co"],
            contact_emails=["order@anhduong.vn", "procurement@anhduong.vn"],
        )
        self.store.create_customer(cust)

        found = self.store.get_customer_by_contact_email("procurement@anhduong.vn")
        self.assertIsNotNone(found)
        self.assertEqual(found.code, "CUST-TEST-MAIL")
        self.assertEqual(found.name, "Công Ty Phân Phối Ánh Dương")

        # Unknown email
        unknown = self.store.get_customer_by_contact_email("stranger@xyz.com")
        self.assertIsNone(unknown)

    def test_unresolved_customer_generates_finding(self):
        """Email from unregistered sender creates finding CUSTOMER_UNRESOLVED."""
        xlsx = create_sample_po_xlsx_bytes("PO-UNRESOLVED-01", "LAPTOP-A14", 1)
        msg = EmailMessageItem(
            message_id="msg-unresolved-123@stranger.org",
            sender_name="Stranger",
            sender_email="stranger@stranger.org",
            subject="Đơn hàng mới",
            date_str=datetime.now(UTC).isoformat(),
            attachments=[EmailAttachment(filename="Order.xlsx", content_bytes=xlsx)],
        )

        res = self.service.process_message(msg, catalog_path=self.catalog_path)
        self.assertEqual(res.status, "PROCESSED")
        self.assertEqual(res.orders_created, 1)

        # Inspect analysis in store
        analysis_id = res.analysis_ids[0]
        stored = self.store.get_order(analysis_id)
        self.assertIsNotNone(stored)
        findings = json.loads(stored["findings_json"])
        has_unresolved_finding = any(f.get("code") == "CUSTOMER_UNRESOLVED" for f in findings)
        self.assertTrue(has_unresolved_finding)

    def test_email_intake_api_routes(self):
        """Test GET /api/v1/intake/email/status and POST /api/v1/intake/email/poll."""
        client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})

        # Test status endpoint
        res = client.get("/api/v1/intake/email/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("enabled", data)
        self.assertIn("imap_configured", data)
        self.assertIn("recent_error_count", data)

        # Test poll endpoint
        res_poll = client.post("/api/v1/intake/email/poll")
        self.assertEqual(res_poll.status_code, 200)
        poll_data = res_poll.json()
        self.assertEqual(poll_data["status"], "success")
        self.assertIn("processed_count", poll_data)

        # Test logs endpoint
        res_logs = client.get("/api/v1/intake/email/logs")
        self.assertEqual(res_logs.status_code, 200)
        self.assertIsInstance(res_logs.json(), list)


if __name__ == "__main__":
    unittest.main()
