from __future__ import annotations

import email
import email.policy
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr, parsedate_to_datetime
import imaplib
import logging
import os
import traceback
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
# A poll runs synchronously, so cap how many messages one call may parse.
DEFAULT_MAX_MESSAGES = 20

# Attachments are read fully into memory, so refuse anything unreasonable.
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024  # 25 MB, matches common provider caps
MAX_ATTACHMENTS_PER_MESSAGE = 20

# Network calls must never hang the poll loop forever.
DEFAULT_NETWORK_TIMEOUT = 30

# How many times a failing message is retried before it is given up on. Without
# a ceiling, a permanently broken mail is retried every cycle and, once the
# per-poll cap fills with such mail, new orders are never reached.
MAX_PROCESSING_ATTEMPTS = 3

# Fetch beyond the per-poll cap so that new mail sitting behind a backlog of
# failed mail can still be prioritised, bounded so a huge mailbox stays cheap.
FETCH_OVERSCAN = 5
MAX_FETCH_WINDOW = 200

# Local-parts that indicate an automated mailbox. Replying to one of these can
# bounce straight back into this inbox and loop forever.
AUTOMATED_LOCAL_PARTS = frozenset({
    "mailer-daemon", "postmaster", "noreply", "no-reply", "donotreply",
    "do-not-reply", "bounce", "bounces", "notification", "notifications",
    "automailer", "auto-reply", "autoreply",
})


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


def _received_sort_key(msg: EmailMessageItem) -> str:
    """Sortable timestamp for a message, oldest first.

    Falls back to the raw header (then empty) when the date is unparseable, so
    a malformed Date never breaks ordering for the rest of the mailbox.
    """
    try:
        parsed = parsedate_to_datetime(msg.date_str)
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC).isoformat()
    except (TypeError, ValueError):
        pass
    return msg.date_str or ""


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
    # Headers set by mailing lists and auto-responders; used to avoid mail loops.
    auto_submitted: str = ""
    precedence: str = ""
    list_id: str = ""

    @property
    def is_automated(self) -> bool:
        """True when replying to this message risks a mail loop.

        Bounces, out-of-office responders and list traffic must never receive an
        auto-reply: the reply bounces back into this same inbox and repeats.
        """
        if self.auto_submitted and self.auto_submitted.lower().strip() != "no":
            return True
        if self.precedence.lower().strip() in ("bulk", "list", "junk", "auto_reply"):
            return True
        if self.list_id:
            return True
        local_part = self.sender_email.split("@", 1)[0].lower()
        return local_part in AUTOMATED_LOCAL_PARTS


@dataclass
class EmailProcessResult:
    message_id: str
    sender_email: str
    subject: str
    status: str  # PROCESSED | PARTIAL | IGNORED | ERROR | DUPLICATE | GAVE_UP
    orders_created: int = 0
    analysis_ids: list[int] = field(default_factory=list)
    po_numbers: list[str] = field(default_factory=list)
    # (filename, error message) for each attachment that failed to parse.
    failed_attachments: list[tuple[str, str]] = field(default_factory=list)
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
                        if len(attachments) >= MAX_ATTACHMENTS_PER_MESSAGE:
                            logger.warning(
                                "Message %s exceeds %d attachments; ignoring the rest.",
                                msg_id, MAX_ATTACHMENTS_PER_MESSAGE,
                            )
                            continue
                        payload = part.get_payload(decode=True)
                        if payload:
                            # Oversized payloads are already in memory here, but
                            # dropping them keeps them out of the parser.
                            if len(payload) > MAX_ATTACHMENT_BYTES:
                                logger.warning(
                                    "Skipping oversized attachment '%s' (%d bytes) in %s",
                                    filename, len(payload), msg_id,
                                )
                                continue
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
            auto_submitted=msg.get("Auto-Submitted", "") or "",
            precedence=msg.get("Precedence", "") or "",
            list_id=msg.get("List-Id", "") or "",
        )

    def fetch_unread_messages(self, max_messages: int | None = None) -> list[EmailMessageItem]:
        """Connect to IMAP server and fetch UNSEEN messages (at most max_messages)."""
        limit = DEFAULT_MAX_MESSAGES if max_messages is None else max(1, max_messages)
        # Look past the cap so poll_once can pick fresh mail ahead of a backlog
        # of previously failed messages before trimming to the cap itself.
        limit = min(limit * FETCH_OVERSCAN, MAX_FETCH_WINDOW)

        if self._imap_client is not None:
            return list(self._imap_client.fetch_messages())[:limit]

        if not self.config.imap_host or not self.config.imap_user:
            logger.info("IMAP intake not configured. Skipping mailbox poll.")
            return []

        messages: list[EmailMessageItem] = []
        try:
            if self.config.imap_ssl:
                imap = imaplib.IMAP4_SSL(
                    self.config.imap_host, self.config.imap_port,
                    timeout=DEFAULT_NETWORK_TIMEOUT,
                )
            else:
                imap = imaplib.IMAP4(
                    self.config.imap_host, self.config.imap_port,
                    timeout=DEFAULT_NETWORK_TIMEOUT,
                )

            imap.login(self.config.imap_user, self.config.imap_password)
            imap.select(self.config.imap_folder)

            # UID search/fetch: sequence numbers shift as the mailbox changes,
            # so flagging by them can mark the wrong message.
            typ, data = imap.uid("SEARCH", None, "UNSEEN")
            if typ == "OK" and data and data[0]:
                for uid in data[0].split()[:limit]:
                    # BODY.PEEK avoids setting \Seen here; the flag is set
                    # explicitly in mark_processed() only after the message has
                    # actually been handled, so a crash mid-poll leaves it unread.
                    typ, msg_data = imap.uid("FETCH", uid, "(BODY.PEEK[])")
                    if typ == "OK" and msg_data and isinstance(msg_data[0], tuple):
                        raw_email = msg_data[0][1]
                        parsed = self.parse_mime_message(raw_email, uid=uid.decode())
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

    def mark_processed(self, uids: list[str]) -> int:
        """Flag handled messages as \\Seen so later polls skip them.

        Without this the same mail is re-fetched every cycle, and once the
        per-poll cap fills with old messages, genuinely new orders are never
        reached. Returns how many UIDs were flagged.
        """
        if not uids:
            return 0

        if self._imap_client is not None:
            marker = getattr(self._imap_client, "mark_seen", None)
            return marker(uids) if marker else 0

        if not self.config.imap_host or not self.config.imap_user:
            return 0

        try:
            if self.config.imap_ssl:
                imap = imaplib.IMAP4_SSL(
                    self.config.imap_host, self.config.imap_port,
                    timeout=DEFAULT_NETWORK_TIMEOUT,
                )
            else:
                imap = imaplib.IMAP4(
                    self.config.imap_host, self.config.imap_port,
                    timeout=DEFAULT_NETWORK_TIMEOUT,
                )
            imap.login(self.config.imap_user, self.config.imap_password)
            imap.select(self.config.imap_folder)
            typ, _ = imap.uid("STORE", ",".join(uids), "+FLAGS", "(\\Seen)")
            imap.close()
            imap.logout()
            if typ != "OK":
                logger.warning("IMAP refused to flag UIDs %s as Seen", uids)
                return 0
            return len(uids)
        except Exception as exc:
            # Non-fatal: the orders are already saved, and idempotency stops a
            # re-poll from duplicating them.
            logger.error("Could not flag messages as Seen: %s", exc)
            return 0

    def send_auto_reply(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachment_path: str | Path | None = None,
        in_reply_to: str | None = None,
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
            # Mark this as machine-generated so well-behaved responders on the
            # far side do not reply to it and start a loop.
            msg["Auto-Submitted"] = "auto-replied"
            msg["X-Auto-Response-Suppress"] = "All"
            if in_reply_to:
                # Keeps the reply in the customer's original mail thread.
                msg["In-Reply-To"] = f"<{in_reply_to}>"
                msg["References"] = f"<{in_reply_to}>"
            msg.attach(MIMEText(body, "plain", "utf-8"))

            if attachment_path and Path(attachment_path).exists():
                path = Path(attachment_path)
                with open(path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=path.name)
                part["Content-Disposition"] = f'attachment; filename="{path.name}"'
                msg.attach(part)

            if self.config.smtp_ssl:
                server = smtplib.SMTP_SSL(
                    self.config.smtp_host, self.config.smtp_port,
                    timeout=DEFAULT_NETWORK_TIMEOUT,
                )
            else:
                server = smtplib.SMTP(
                    self.config.smtp_host, self.config.smtp_port,
                    timeout=DEFAULT_NETWORK_TIMEOUT,
                )
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
        # PARTIAL counts as processed: some orders were already recorded, so a
        # re-poll must not duplicate them. ERROR is retried (nothing landed).
        attempts = int(existing_log.get("attempts", 0)) if existing_log else 0
        if existing_log and existing_log.get("status") == "ERROR" and attempts >= MAX_PROCESSING_ATTEMPTS:
            # Give up rather than retry forever; a human needs to look at it.
            logger.warning(
                "Message %s failed %d times; giving up.", msg.message_id, attempts
            )
            return EmailProcessResult(
                message_id=msg.message_id,
                sender_email=msg.sender_email,
                subject=msg.subject,
                status="GAVE_UP",
                orders_created=0,
                error_message=(
                    f"Đã thử xử lý {attempts} lần không thành công. "
                    f"Cần nhân viên kiểm tra thủ công."
                ),
            )

        if existing_log and existing_log.get("status") in ("PROCESSED", "PARTIAL", "IGNORED"):
            logger.info("Email message %s already processed. Skipping.", msg.message_id)
            return EmailProcessResult(
                message_id=msg.message_id,
                sender_email=msg.sender_email,
                subject=msg.subject,
                status="DUPLICATE",
                orders_created=existing_log.get("orders_created", 0),
            )

        # 2. Never auto-reply to bounces, vacation responders or list traffic:
        #    the reply lands back in this inbox and loops. Log and move on.
        if msg.is_automated:
            logger.info("Skipping automated message %s from %s", msg.message_id, msg.sender_email)
            self.store.record_email_inbox_log(
                message_id=msg.message_id,
                sender=msg.sender_email,
                subject=msg.subject,
                received_at=msg.date_str,
                attachments_count=len(msg.attachments),
                orders_created=0,
                status="IGNORED",
                error_message="Thư tự động (bounce/auto-reply/mailing list) - không xử lý, không trả lời.",
            )
            return EmailProcessResult(
                message_id=msg.message_id,
                sender_email=msg.sender_email,
                subject=msg.subject,
                status="IGNORED",
                orders_created=0,
                error_message="Thư tự động - bỏ qua để tránh vòng lặp email.",
                auto_reply_sent=False,
            )

        # 3. Resolve Customer by sender email
        matched_customer = self.store.get_customer_by_contact_email(msg.sender_email)
        resolved_customer_name = matched_customer.name if matched_customer else None

        # 4. Filter valid attachments
        valid_attachments = [a for a in msg.attachments if a.is_supported]

        # 5. Handle case with NO valid attachments (e.g. .docx or empty mail)
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
                in_reply_to=msg.message_id,
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

        # 6. Process valid attachments
        orders_created = 0
        analysis_ids: list[int] = []
        po_numbers: list[str] = []
        failed_attachments: list[tuple[str, str]] = []
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
                # One bad attachment must not abort the rest of the message, but
                # it must stay visible: recorded here, surfaced in the DB log,
                # and reported back to the sender in the auto-reply.
                logger.exception("Error processing attachment '%s'", attachment.filename)
                failed_attachments.append((attachment.filename, str(exc)))
                try:
                    self.store.record_request_error(
                        request_id=f"email-intake-{msg.message_id}",
                        endpoint="email_intake_attachment",
                        status_code=422,
                        error_message=f"{attachment.filename}: {exc}",
                        traceback_str=traceback.format_exc(),
                    )
                except Exception:
                    logger.warning("Could not persist attachment error for '%s'", attachment.filename)

        # 7. Record log & Send auto-reply reflecting the real outcome
        failed_lines = "".join(
            f"- {name}: {reason}\n" for name, reason in failed_attachments
        )

        if orders_created > 0:
            # A message with some unreadable attachments is only a partial
            # success; reporting it as fully PROCESSED would hide lost POs.
            status_str = "PARTIAL" if failed_attachments else "PROCESSED"
            err_msg = (
                f"{len(failed_attachments)} tệp đính kèm không bóc tách được."
                if failed_attachments
                else None
            )
            self.store.record_email_inbox_log(
                message_id=msg.message_id,
                sender=msg.sender_email,
                subject=msg.subject,
                received_at=msg.date_str,
                attachments_count=len(msg.attachments),
                orders_created=orders_created,
                status=status_str,
                error_message=err_msg,
            )

            po_list_str = ", ".join(po_numbers)
            ids_str = ", ".join(str(i) for i in analysis_ids)
            if failed_attachments:
                reply_subject = f"Re: {msg.subject} - Tiếp nhận PO một phần"
                reply_body = (
                    f"Kính gửi Quý khách,\n\n"
                    f"Hệ thống đã tiếp nhận {orders_created} đơn hàng từ thư '{msg.subject}':\n"
                    f"- Mã đơn hàng (PO): {po_list_str}\n"
                    f"- Mã theo dõi hệ thống: {ids_str}\n\n"
                    f"Tuy nhiên, {len(failed_attachments)} tệp sau KHÔNG đọc được và chưa được ghi nhận:\n"
                    f"{failed_lines}\n"
                    f"Vui lòng kiểm tra lại các tệp trên theo file mẫu đính kèm và gửi lại.\n\n"
                    f"Trân trọng,\n"
                    f"Bộ phận Xử lý Đơn hàng (PO Preflight)"
                )
                template_file = DEFAULT_TEMPLATE_PATH if Path(DEFAULT_TEMPLATE_PATH).exists() else None
            else:
                reply_subject = f"Re: {msg.subject} - Tiếp nhận PO thành công"
                reply_body = (
                    f"Kính gửi Quý khách,\n\n"
                    f"Hệ thống đã tiếp nhận thành công {orders_created} đơn hàng từ thư '{msg.subject}':\n"
                    f"- Mã đơn hàng (PO): {po_list_str}\n"
                    f"- Mã theo dõi hệ thống: {ids_str}\n\n"
                    f"Đơn hàng đang được tự động kiểm tra đối soát quy chuẩn bán hàng và tồn kho.\n\n"
                    f"Trân trọng,\n"
                    f"Bộ phận Xử lý Đơn hàng (PO Preflight)"
                )
                template_file = None

            auto_reply_sent = self.send_auto_reply(
                to_email=msg.sender_email,
                subject=reply_subject,
                body=reply_body,
                attachment_path=template_file,
                in_reply_to=msg.message_id,
            )

            return EmailProcessResult(
                message_id=msg.message_id,
                sender_email=msg.sender_email,
                subject=msg.subject,
                status=status_str,
                orders_created=orders_created,
                analysis_ids=analysis_ids,
                po_numbers=po_numbers,
                failed_attachments=failed_attachments,
                error_message=err_msg,
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

            # The sender must be told their PO was not accepted, otherwise the
            # order is silently lost on both ends.
            reply_body = (
                f"Kính gửi Quý khách,\n\n"
                f"Hệ thống KHÔNG bóc tách được dữ liệu đơn hàng từ thư '{msg.subject}'.\n"
                f"Chi tiết các tệp không đọc được:\n"
                f"{failed_lines or '- (không có tệp nào đọc được)'}\n"
                f"Vui lòng điền thông tin theo file mẫu Excel đính kèm và gửi lại.\n\n"
                f"Trân trọng,\n"
                f"Bộ phận Xử lý Đơn hàng (PO Preflight)"
            )
            template_file = DEFAULT_TEMPLATE_PATH if Path(DEFAULT_TEMPLATE_PATH).exists() else None
            auto_reply_sent = self.send_auto_reply(
                to_email=msg.sender_email,
                subject=f"Re: {msg.subject} - Không tiếp nhận được đơn hàng",
                body=reply_body,
                attachment_path=template_file,
                in_reply_to=msg.message_id,
            )

            return EmailProcessResult(
                message_id=msg.message_id,
                sender_email=msg.sender_email,
                subject=msg.subject,
                status="ERROR",
                orders_created=0,
                failed_attachments=failed_attachments,
                error_message=err_msg,
                auto_reply_sent=auto_reply_sent,
                customer_resolved=resolved_customer_name,
            )

    def poll_once(
        self,
        catalog_path: str | Path = "examples/catalog.csv",
        max_messages: int | None = None,
    ) -> list[EmailProcessResult]:
        """Fetch unread messages (up to max_messages) and process them sequentially."""
        messages = self.fetch_unread_messages(max_messages=max_messages)

        cap = DEFAULT_MAX_MESSAGES if max_messages is None else max(1, max_messages)

        # Split by whether this mailbox has been seen before. A backlog of
        # unreadable mail must never consume the whole per-poll budget, or a
        # new order sitting behind it waits cycle after cycle.
        fresh: list[EmailMessageItem] = []
        retried: list[EmailMessageItem] = []
        for m in messages:
            log = self.store.get_email_inbox_log(m.message_id)
            (retried if log else fresh).append(m)

        # Newest first among unseen mail. An old message still sitting unread
        # has usually already failed to parse on a previous cycle, so serving
        # today's orders first keeps the queue responsive; the older ones still
        # get their turn from the remaining budget and the retry lane.
        fresh.sort(key=_received_sort_key, reverse=True)
        retried.sort(key=_received_sort_key)

        # Reserve most of the budget for first-time mail, but always leave room
        # to retry, so transient failures still get another attempt.
        retry_budget = max(1, cap // 4)
        selected = fresh[: cap - retry_budget]
        selected += retried[: cap - len(selected)]
        # Any budget the retry queue did not use goes back to fresh mail.
        if len(selected) < cap:
            already = {id(m) for m in selected}
            selected += [m for m in fresh if id(m) not in already][: cap - len(selected)]

        messages = selected

        results: list[EmailProcessResult] = []
        handled_uids: list[str] = []

        for msg in messages:
            res = self.process_message(msg, catalog_path=catalog_path)
            results.append(res)
            # An ERROR is retryable, so leave it unread for the next poll.
            # Everything else is settled and must not be picked up again.
            if msg.raw_uid and res.status != "ERROR":  # GAVE_UP included: stop retrying
                handled_uids.append(msg.raw_uid)

        self.mark_processed(handled_uids)
        return results
