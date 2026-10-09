"""Test the real Gmail connection for the PO intake flow.

SAFE MODE IS THE DEFAULT: read-only, does NOT send mail to anyone, does NOT
mark mail as read. Your mailbox is left exactly as it was.

    export IMAP_USER="ban@gmail.com"
    export IMAP_PASSWORD="16-character app password"
    python scripts/thu_gmail_that.py

Only processes mail from the listed addresses (if any); strongly recommended
when the mailbox still holds personal mail:

    export EMAIL_ALLOWED_SENDERS="khach1@congty.vn,khach2@congty.vn"
"""
from __future__ import annotations

import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s")

from preflight.intake.email import EmailIntakeConfig, EmailIntakeService
from preflight.store import AuditStore


def main() -> int:
    user = os.getenv("IMAP_USER", "")
    password = os.getenv("IMAP_PASSWORD", "")

    if not user or not password:
        print("\n❌ Thiếu thông tin đăng nhập.\n")
        print("   export IMAP_USER='ban@gmail.com'")
        print("   export IMAP_PASSWORD='app password 16 ky tu'\n")
        print("   Lấy App Password tại: https://myaccount.google.com/apppasswords")
        print("   (Mật khẩu Gmail thường KHÔNG dùng được, phải bật 2FA trước.)\n")
        return 1

    allowed = frozenset(
        a.strip().lower() for a in os.getenv("EMAIL_ALLOWED_SENDERS", "").split(",") if a.strip()
    )

    config = EmailIntakeConfig(
        imap_host=os.getenv("IMAP_HOST", "imap.gmail.com"),
        imap_port=int(os.getenv("IMAP_PORT", "993")),
        imap_user=user,
        imap_password=password,
        imap_folder=os.getenv("IMAP_FOLDER", "INBOX"),
        imap_ssl=True,
        dry_run=True,          # do not send mail, do not mark as read
        allowed_senders=allowed,
    )

    print("\n" + "=" * 72)
    print("  KIỂM TRA KẾT NỐI GMAIL — CHẾ ĐỘ AN TOÀN")
    print("=" * 72)
    print(f"  Hộp thư    : {config.imap_user}")
    print(f"  Máy chủ    : {config.imap_host}:{config.imap_port}")
    print(f"  Thư mục    : {config.imap_folder}")
    print(f"  Lọc người gửi: {', '.join(sorted(allowed)) if allowed else '(không lọc — đọc mọi thư chưa đọc)'}")
    print("\n  🔒 KHÔNG gửi mail cho bất kỳ ai")
    print("  🔒 KHÔNG đánh dấu thư đã đọc")
    print("=" * 72)

    if not allowed:
        print("\n  ⚠️  CẢNH BÁO: chưa đặt EMAIL_ALLOWED_SENDERS.")
        print("     Script sẽ ĐỌC mọi thư chưa đọc trong hộp thư này.")
        print("     Vẫn an toàn (không gửi, không đánh dấu), nhưng nếu đây là")
        print("     hộp thư cá nhân thì nên đặt danh sách cho phép.\n")
        if input("     Tiếp tục? (go/không): ").strip().lower() != "go":
            print("\n  Đã huỷ.\n")
            return 0

    store = AuditStore("runtime/thu_gmail.db")
    try:
        service = EmailIntakeService(config=config, store=store)

        print("\n  Đang kết nối...")
        messages = service.fetch_unread_messages(max_messages=10)

        if not messages:
            print("\n  ✅ Kết nối THÀNH CÔNG.")
            print("     Không có thư chưa đọc nào (hoặc đã bị lọc hết).")
            print("     Hãy tự gửi cho mình 1 mail kèm file PO .xlsx rồi chạy lại.\n")
            return 0

        print(f"\n  ✅ Kết nối THÀNH CÔNG — đọc được {len(messages)} thư chưa đọc:\n")
        for i, m in enumerate(messages, 1):
            print(f"   {i}. Từ    : {m.sender_email}")
            print(f"      Tiêu đề: {m.subject[:60]}")
            if m.is_automated:
                print("      → Thư tự động, hệ thống sẽ KHÔNG trả lời")
            hop_le = [a for a in m.attachments if a.is_supported]
            if hop_le:
                print(f"      → Tệp đọc được: {', '.join(a.filename for a in hop_le)}")
            elif m.attachments:
                print(f"      → Tệp KHÔNG đọc được: {', '.join(a.filename for a in m.attachments)}")
            else:
                print("      → Không có tệp đính kèm")
            print()

        print("  " + "-" * 68)
        print("  Thử bóc tách các thư trên (vẫn không gửi, không đánh dấu)...\n")
        results = service.poll_once(catalog_path="examples/catalog.csv", max_messages=10)

        dien_giai = {
            "PROCESSED": "✅ Tạo đơn thành công",
            "PARTIAL": "⚠️  Tạo đơn một phần",
            "IGNORED": "⏭️  Bỏ qua",
            "ERROR": "❌ Không bóc tách được",
            "SKIPPED": "⏭️  Ngoài danh sách cho phép",
            "GAVE_UP": "🛑 Đã thử nhiều lần",
            "DUPLICATE": "🔁 Đã xử lý trước đó",
        }
        for r in results:
            print(f"   {dien_giai.get(r.status, r.status)} — {r.subject[:50]}")
            if r.po_numbers:
                print(f"      Mã PO: {', '.join(r.po_numbers)}")
            if r.customer_resolved:
                print(f"      Khách: {r.customer_resolved}")
            if r.error_message:
                print(f"      Lý do: {r.error_message[:70]}")

        print(f"\n  🔒 Hộp thư giữ nguyên: không mail nào được gửi, không thư nào bị đánh dấu.\n")
        return 0

    except Exception as exc:
        print(f"\n  ❌ LỖI: {type(exc).__name__}: {exc}\n")
        low = str(exc).lower()
        if "authenticationfailed" in low.replace(" ", "") or "invalid credentials" in low:
            print("     Nguyên nhân thường gặp: dùng mật khẩu Gmail thường.")
            print("     Phải bật 2FA rồi tạo App Password 16 ký tự:")
            print("     https://myaccount.google.com/apppasswords\n")
        return 1
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
