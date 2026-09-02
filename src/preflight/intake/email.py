from __future__ import annotations

import email
import email.policy
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
import imaplib
import logging
import os
from dataclasses import dataclass, field, replace
from datetime import datetime, UTC
from pathlib import Path
import smtplib
from typing import Any

from preflight.catalog import get_catalog
from preflight.ingestion.pipeline import IntelligentIngestionPipeline
from preflight.models import Order, Finding
from preflight.rules import analyze_order
from preflight.rules_context import build_rule_context
from preflight.store import BaseAuditStore, create_audit_store

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".pdf", ".png", ".jpg", ".jpeg", ".json"}
DEFAULT_TEMPLATE_PATH = "examples/templates/PO_MAU.xlsx"


@dataclass
class EmailIntakeConfig:
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""
    imap_folder: str = "INBOX"
    imap_ssl: bool = True
    
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@preflight.vn"
    smtp_ssl: bool = False
    
    poll_interval_seconds: int = 120
    enabled: bool = False

    @classmethod
    def from_env(cls) -> EmailIntakeConfig:
        return cls(
            imap_host=os.getenv("IMAP_HOST", ""),
            imap_port=int(os.getenv("IMAP_PORT", "993")),
            imap_user=os.getenv("IMAP_USER", os.getenv("IMAP_USERNAME", "")),
            imap_password=os.getenv("IMAP_PASSWORD", ""),
            imap_folder=os.getenv("IMAP_FOLDER", "INBOX"),
            imap_ssl=os.getenv("IMAP_SSL", "true").lower() in ("true", "1", "yes"),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_from=os.getenv("SMTP_FROM", "noreply@preflight.vn"),
            smtp_ssl=os.getenv("SMTP_SSL", "false").lower() in ("true", "1", "yes"),
            poll_interval_seconds=int(os.getenv("EMAIL_POLL_INTERVAL", "120")),
            enabled=os.getenv("EMAIL_INTAKE_ENABLED", "false").lower() in ("true", "1", "yes"),
        )


@dataclass
class EmailAttachment:
    filename: str
    content_bytes: bytes
    content_type: str = "application/octet-stream"

    @property
    def extension(self) -> str:
        return Path(self.filename).suffix.lower()

    @property
    def is_supported(self) -> bool:
        return self.extension in SUPPORTED_EXTENSIONS


@dataclass
class EmailMessageItem:
    message_id: str
    sender_name: str
    sender_email: str
    subject: str
    date_str: str
    body_text: str = ""
    attachments: list[EmailAttachment] = field(default_factory=list)
    raw_uid: str | None = None


@dataclass
class EmailProcessResult:
    message_id: str
    sender_email: str
    subject: str
    status: str  # "PROCESSED", "IGNORED", "ERROR", "DUPLICATE"
    orders_created: int = 0
    analysis_ids: list[int] = field(default_factory=list)
    po_numbers: list[str] = field(default_factory=list)
    error_message: str | None = None
    auto_reply_sent: bool = False
    customer_resolved: str | None = None


class EmailIntakeService:
    """Automated Email Intake Processor for PO documents with IMAP polling and Vietnamese auto-reply."""

    def __init__(
        self,
        config: EmailIntakeConfig | None = None,
        store: BaseAuditStore | None = None,
        pipeline: IntelligentIngestionPipeline | None = None,
        smtp_client: Any | None = None,
        imap_client: Any | None = None,
    ):
        self.config = config or EmailIntakeConfig.from_env()
        self.store = store or create_audit_store()
        self.pipeline = pipeline or IntelligentIngestionPipeline()
        self._smtp_client = smtp_client
        self._imap_client = imap_client

    def parse_mime_message(self, raw_bytes: bytes, uid: str | None = None) -> EmailMessageItem:
        """Parse raw RFC822 email bytes into structured EmailMessageItem."""
        msg = email.message_from_bytes(raw_bytes, policy=email.policy.default)
        
        msg_id = msg.get("Message-ID") or f"gen-{hash(raw_bytes)}-{datetime.now(UTC).timestamp()}"
        from_header = msg.get("From", "")
        sender_name, sender_email = parseaddr(from_header)
        subject = msg.get("Subject", "(Không có tiêu đề)")
        date_str = msg.get("Date", datetime.now(UTC).isoformat())

        body_text = ""
        attachments: list[EmailAttachment] = []

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                content_type = part.get_content_type()
                filename = part.get_filename()

                if "attachment" in content_disposition or filename:
                    if filename:
                        payload = part.get_payload(decode=True)
                        if payload:
                            attachments.append(
                                EmailAttachment(
                                    filename=filename,
                                    content_bytes=payload,
                                    content_type=content_type,
                                )
                            )
                elif content_type == "text/plain" and not body_text:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body_text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

        return EmailMessageItem(
            message_id=msg_id.strip("<> "),
            sender_name=sender_name,
            sender_email=sender_email.strip().lower(),
            subject=subject,
            date_str=date_str,
            body_text=body_text,
            attachments=attachments,
            raw_uid=uid,
        )

    def fetch_unread_messages(self) -> list[EmailMessageItem]:
        """Connect to IMAP server and fetch UNSEEN messages."""
        if self._imap_client is not None:
            return self._imap_client.fetch_messages()

        if not self.config.imap_host or not self.config.imap_user:
            logger.info("IMAP intake not configured. Skipping mailbox poll.")
            return []

        messages: list[EmailMessageItem] = []
        try:
            if self.config.imap_ssl:
                imap = imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port)
            else:
                imap = imaplib.IMAP4(self.config.imap_host, self.config.imap_port)

            imap.login(self.config.imap_user, self.config.imap_password)
            imap.select(self.config.imap_folder)

            typ, data = imap.search(None, "UNSEEN")
            if typ == "OK" and data[0]:
                for num in data[0].split():
                    typ, msg_data = imap.fetch(num, "(RFC822)")
                    if typ == "OK" and msg_data and isinstance(msg_data[0], tuple):
                        raw_email = msg_data[0][1]
                        parsed = self.parse_mime_message(raw_email, uid=num.decode())
                        messages.append(parsed)

            imap.close()
            imap.logout()
        except Exception as exc:
            logger.error("Error polling IMAP mailbox: %s", exc)
            self.store.record_request_error(
                request_id=f"email-poll-{int(datetime.now(UTC).timestamp())}",
                endpoint="imap_poll",
                status_code=500,
                error_message=f"IMAP poll failure: {exc}",
                traceback_str="",
            )

        return messages

    def send_auto_reply(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachment_path: str | Path | None = None,
    ) -> bool:
        """Send automated response via SMTP or mock."""
        if not to_email:
            return False

        if self._smtp_client is not None:
            return self._smtp_client.send_email(to_email, subject, body, attachment_path)

        if not self.config.smtp_host:
            logger.info("SMTP host not configured. Simulated auto-reply to %s", to_email)
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.smtp_from
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            if attachment_path and Path(attachment_path).exists():
                path = Path(attachment_path)
                with open(path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=path.name)
                part["Content-Disposition"] = f'attachment; filename="{path.name}"'
                msg.attach(part)

            if self.config.smtp_ssl:
                server = smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port)
            else:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
                server.starttls()

            if self.config.smtp_user and self.config.smtp_password:
                server.login(self.config.smtp_user, self.config.smtp_password)

            server.send_message(msg)
            server.quit()
            return True
        except Exception as exc:
            logger.error("Failed to send auto-reply to %s: %s", to_email, exc)
            return False

    def process_message(
        self,
        msg: EmailMessageItem,
        catalog_path: str | Path = "examples/catalog.csv",
    ) -> EmailProcessResult:
        """Process a single email message: validate idempotency, extract attachments, run rules, and auto-reply."""
        # 1. Check idempotency
        existing_log = self.store.get_email_inbox_log(msg.message_id)
        if existing_log and existing_log.get("status") in ("PROCESSED", "IGNORED"):
            logger.info("Email message %s already processed. Skipping.", msg.message_id)
            return EmailProcessResult(
                message_id=msg.message_id,
                sender_email=msg.sender_email,
                subject=msg.subject,
                status="DUPLICATE",
                orders_created=existing_log.get("orders_created", 0),
            )

        # 2. Resolve Customer by sender email
        matched_customer = self.store.get_customer_by_contact_email(msg.sender_email)
        resolved_customer_name = matched_customer.name if matched_customer else None

        # 3. Filter valid attachments
        valid_attachments = [a for a in msg.attachments if a.is_supported]

        # 4. Handle case with NO valid attachments (e.g. .docx or empty mail)
        if not valid_attachments:
            err_msg = "Không tìm thấy file đính kèm hợp lệ (.xlsx, .xls, .csv, .pdf, .json, ảnh)."
            self.store.record_email_inbox_log(
                message_id=msg.message_id,
                sender=msg.sender_email,
                subject=msg.subject,
                received_at=msg.date_str,
                attachments_count=len(msg.attachments),
                orders_created=0,
                status="IGNORED",
                error_message=err_msg,
            )

            # Send Vietnamese rejection auto-reply with PO_MAU.xlsx
            reply_subject = f"Re: {msg.subject} - Yêu cầu gửi lại đơn hàng"
            reply_body = (
                f"Kính gửi Quý khách,\n\n"
                f"Hệ thống tiếp nhận PO tự động không tìm thấy file đính kèm hợp lệ trong thư '{msg.subject}'.\n"
                f"Các định dạng được chấp nhận: Excel (.xlsx, .xls), CSV, PDF, hoặc Ảnh chụp PO.\n\n"
                f"Vui lòng điền thông tin đơn hàng theo file mẫu Excel đính kèm và gửi lại.\n\n"
                f"Trân trọng,\n"
                f"Bộ phận Xử lý Đơn hàng (PO Preflight)"
            )
            template_file = DEFAULT_TEMPLATE_PATH if Path(DEFAULT_TEMPLATE_PATH).exists() else None
            auto_reply_sent = self.send_auto_reply(
                to_email=msg.sender_email,
                subject=reply_subject,
                body=reply_body,
                attachment_path=template_file,
            )

            return EmailProcessResult(
                message_id=msg.message_id,
                sender_email=msg.sender_email,
                subject=msg.subject,
                status="IGNORED",
                orders_created=0,
                error_message=err_msg,
                auto_reply_sent=auto_reply_sent,
                customer_resolved=resolved_customer_name,
            )

        # 5. Process valid attachments
        orders_created = 0
        analysis_ids: list[int] = []
        po_numbers: list[str] = []
        catalog = get_catalog(catalog_path)

        for attachment in valid_attachments:
            try:
                extracted, domain_order = self.pipeline.process_file_bytes(
                    attachment.content_bytes,
                    attachment.filename,
                )

                # If customer is resolved via sender email, apply it
                if matched_customer:
                    customer_name = matched_customer.name
                else:
                    customer_name = domain_order.customer

                # Reconstruct domain order, overriding the customer when the
                # sender email resolved to a known customer master record.
                effective_order = replace(
                    domain_order,
                    customer=customer_name,
                    created_by=f"email:{msg.sender_email}",
                    last_modified_by=f"email:{msg.sender_email}",
                )
                source_file = f"email://{msg.sender_email}/{attachment.filename}"

                # Build rule context & Evaluate Order
                ctx = build_rule_context(self.store, catalog, effective_order)
                analysis = analyze_order(effective_order, ctx)

                # Add CUSTOMER_UNRESOLVED finding if customer could not be resolved
                if not matched_customer and not self.store.get_customer_by_normalized_name(effective_order.customer):
                    analysis.findings.append(
                        Finding(
                            code="CUSTOMER_UNRESOLVED",
                            severity="warning",
                            message=f"Người gửi email '{msg.sender_email}' chưa được liên kết với khách hàng nào trong hệ thống.",
                            evidence={"sender_email": msg.sender_email, "customer": effective_order.customer},
                        )
                    )

                # Save Analysis
                analysis_id = self.store.record_analysis(analysis, source_file)
                analysis_ids.append(analysis_id)
                po_numbers.append(effective_order.po_number)
                orders_created += 1

                # Audit block
                self.store.append_audit_block(
                    po_number=effective_order.po_number,
                    action="ORDER_INGESTED_EMAIL",
                    actor=f"email:{msg.sender_email}",
                    payload={
                        "analysis_id": analysis_id,
                        "message_id": msg.message_id,
                        "sender": msg.sender_email,
                        "subject": msg.subject,
                        "attachment": attachment.filename,
                        "status": analysis.status,
                    },
                )

            except Exception as exc:
                logger.error("Error processing attachment '%s': %s", attachment.filename, exc)

        # 6. Record log & Send confirmation auto-reply
        if orders_created > 0:
            status_str = "PROCESSED"
            self.store.record_email_inbox_log(
                message_id=msg.message_id,
                sender=msg.sender_email,
                subject=msg.subject,
                received_at=msg.date_str,
                attachments_count=len(msg.attachments),
                orders_created=orders_created,
                status=status_str,
            )

            reply_subject = f"Re: {msg.subject} - Tiếp nhận PO thành công"
            po_list_str = ", ".join(po_numbers)
            ids_str = ", ".join(str(i) for i in analysis_ids)
            reply_body = (
                f"Kính gửi Quý khách,\n\n"
                f"Hệ thống đã tiếp nhận thành công {orders_created} đơn hàng từ thư '{msg.subject}':\n"
                f"- Mã đơn hàng (PO): {po_list_str}\n"
                f"- Mã theo dõi hệ thống: {ids_str}\n\n"
                f"Đơn hàng đang được tự động kiểm tra đối soát quy chuẩn bán hàng và tồn kho.\n\n"
                f"Trân trọng,\n"
                f"Bộ phận Xử lý Đơn hàng (PO Preflight)"
            )
            auto_reply_sent = self.send_auto_reply(
                to_email=msg.sender_email,
                subject=reply_subject,
                body=reply_body,
            )

            return EmailProcessResult(
                message_id=msg.message_id,
                sender_email=msg.sender_email,
                subject=msg.subject,
                status=status_str,
                orders_created=orders_created,
                analysis_ids=analysis_ids,
                po_numbers=po_numbers,
                auto_reply_sent=auto_reply_sent,
                customer_resolved=resolved_customer_name,
            )
        else:
            err_msg = "Không thể bóc tách dữ liệu từ các file đính kèm trong email."
            self.store.record_email_inbox_log(
                message_id=msg.message_id,
                sender=msg.sender_email,
                subject=msg.subject,
                received_at=msg.date_str,
                attachments_count=len(msg.attachments),
                orders_created=0,
                status="ERROR",
                error_message=err_msg,
            )
            return EmailProcessResult(
                message_id=msg.message_id,
                sender_email=msg.sender_email,
                subject=msg.subject,
                status="ERROR",
                orders_created=0,
                error_message=err_msg,
                customer_resolved=resolved_customer_name,
            )

    def poll_once(
        self,
        catalog_path: str | Path = "examples/catalog.csv",
    ) -> list[EmailProcessResult]:
        """Fetch all unread messages and process them sequentially."""
        messages = self.fetch_unread_messages()
        results: list[EmailProcessResult] = []
        for msg in messages:
            res = self.process_message(msg, catalog_path=catalog_path)
            results.append(res)
        return results
