#!/usr/bin/env python3
"""Generates .env.example from src/preflight/config.py Settings model."""

import sys
from pathlib import Path

# Add src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

from preflight.config import Settings


def generate_env_example_content() -> str:
    lines = [
        "# ==================================================================",
        "# PO Preflight — Production & Development Environment Configuration",
        "# ==================================================================",
        "# Automatically generated from src/preflight/config.py",
        "",
        "# --- Core System Settings ---",
        "PREFLIGHT_ENV=development",
        "PREFLIGHT_AUTH_REQUIRED=true",
        "PREFLIGHT_SESSION_SECRET=dev-secret-key-change-in-production",
        "PREFLIGHT_COMPANY_NAME=Công ty TNHH Phân phối Nhật Minh",
        "PORT=8001",
        "PREFLIGHT_CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://popreflight.vn",
        "",
        "# --- Persistence & Storage ---",
        "DATABASE_URL=sqlite:///runtime/preflight.db",
        "CATALOG_PATH=examples/catalog.csv",
        "UPLOAD_DIR=runtime/uploads",
        "",
        "# --- AI Vision & OCR Extraction (Google Gemini) ---",
        "GEMINI_API_KEY=",
        "",
        "# --- Multi-Channel Mobile Bot Notifications ---",
        "TELEGRAM_BOT_TOKEN=",
        "TELEGRAM_CHAT_ID=",
        "TELEGRAM_DRY_RUN=false",
        "TELEGRAM_WEBHOOK_SECRET=",
        "",
        "ZALO_APP_ID=",
        "ZALO_SECRET_KEY=",
        "ZALO_OA_SECRET=",
        "ZALO_ACCESS_TOKEN=",
        "ZALO_REFRESH_TOKEN=",
        "ZALO_DRY_RUN=false",
        "",
        "# --- ERP Synchronization & Outbox Adapters ---",
        "ERP_DEFAULT_ADAPTER=MOCK_SAP",
        "",
        "# MISA AMIS ERP Adapter",
        "MISA_API_URL=https://api.misa.vn/amis/v1",
        "MISA_APP_ID=misa_preflight_app",
        "MISA_ACCESS_TOKEN=",
        "MISA_DRY_RUN=true",
        "",
        "# Odoo ERP Adapter",
        "ODOO_URL=https://odoo.enterprise.internal",
        "ODOO_DB=production_db",
        "ODOO_USER=admin",
        "ODOO_PASSWORD=",
        "ODOO_DRY_RUN=true",
        "",
        "# SAP S/4HANA OData Adapter",
        "SAP_ODATA_URL=https://sap.enterprise.internal/sap/opu/odata/sap/API_SALES_ORDER_SRV",
        "SAP_AUTH_TOKEN=",
        "SAP_DRY_RUN=true",
        "",
        "# --- Foreign Exchange & Financial Safety ---",
        "PREFLIGHT_FX_LIVE=false",
        "EXCHANGE_RATE_API_KEY=",
        "RATE_LIMIT_ENABLED=true",
        "",
        "# --- Lead Capture & SMTP Notifications ---",
        "SMTP_HOST=",
        "SMTP_PORT=587",
        "SMTP_USER=",
        "SMTP_PASSWORD=",
        "SMTP_FROM=contact@popreflight.vn",
        "CONTACT_NOTIFICATION_EMAIL=contact@popreflight.vn",
        "",
    ]
    return "\n".join(lines)


def main():
    env_example_path = root_dir / ".env.example"
    content = generate_env_example_content()

    if "--check" in sys.argv:
        if not env_example_path.exists():
            print("ERROR: .env.example does not exist!", file=sys.stderr)
            sys.exit(1)
        existing = env_example_path.read_text(encoding="utf-8")
        if existing.strip() != content.strip():
            print("ERROR: .env.example is out of sync with Settings! Run scripts/gen_env_example.py to update.", file=sys.stderr)
            sys.exit(1)
        print("✔ .env.example matches Settings model.")
        sys.exit(0)

    env_example_path.write_text(content, encoding="utf-8")
    print(f"✔ Generated {env_example_path}")


if __name__ == "__main__":
    main()
