"""PO Preflight Centralized Typed Configuration Module.

Uses pydantic-settings to load and validate environment variables with strict typing,
production validation checks, and masked logging summaries.
"""

from functools import lru_cache
import os
import sys
from typing import Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core Environment & Security
    env: str = Field(default="development", alias="PREFLIGHT_ENV")
    auth_required: bool = Field(default=True, alias="PREFLIGHT_AUTH_REQUIRED")
    session_secret: str = Field(default="dev-secret-key-change-in-production", alias="PREFLIGHT_SESSION_SECRET")
    company_name: str = Field(default="Công ty TNHH Phân phối Nhật Minh", alias="PREFLIGHT_COMPANY_NAME")
    port: int = Field(default=8001, alias="PORT")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,https://popreflight.vn",
        alias="PREFLIGHT_CORS_ORIGINS",
    )

    # Persistence & Catalog
    database_url: str = Field(default="sqlite:///runtime/preflight.db", alias="DATABASE_URL")
    catalog_path: str = Field(default="examples/catalog.csv", alias="CATALOG_PATH")
    upload_dir: str = Field(default="runtime/uploads", alias="UPLOAD_DIR")

    # Document Extraction & Vision (Gemini)
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")

    # Bot & Notification Channels
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")
    telegram_dry_run: bool = Field(default=False, alias="TELEGRAM_DRY_RUN")
    telegram_webhook_secret: str | None = Field(default=None, alias="TELEGRAM_WEBHOOK_SECRET")

    zalo_app_id: str | None = Field(default=None, alias="ZALO_APP_ID")
    zalo_secret_key: str | None = Field(default=None, alias="ZALO_SECRET_KEY")
    zalo_oa_secret: str | None = Field(default=None, alias="ZALO_OA_SECRET")
    zalo_access_token: str | None = Field(default=None, alias="ZALO_ACCESS_TOKEN")
    zalo_refresh_token: str | None = Field(default=None, alias="ZALO_REFRESH_TOKEN")
    zalo_dry_run: bool = Field(default=False, alias="ZALO_DRY_RUN")

    # ERP Adapters & Synchronization
    erp_default_adapter: str = Field(default="MOCK_SAP", alias="ERP_DEFAULT_ADAPTER")

    misa_api_url: str = Field(default="https://api.misa.vn/amis/v1", alias="MISA_API_URL")
    misa_app_id: str = Field(default="misa_preflight_app", alias="MISA_APP_ID")
    misa_access_token: str = Field(default="", alias="MISA_ACCESS_TOKEN")
    misa_dry_run: bool = Field(default=True, alias="MISA_DRY_RUN")

    odoo_url: str = Field(default="https://odoo.enterprise.internal", alias="ODOO_URL")
    odoo_db: str = Field(default="production_db", alias="ODOO_DB")
    odoo_user: str = Field(default="admin", alias="ODOO_USER")
    odoo_password: str = Field(default="", alias="ODOO_PASSWORD")
    odoo_dry_run: bool = Field(default=True, alias="ODOO_DRY_RUN")

    sap_odata_url: str = Field(
        default="https://sap.enterprise.internal/sap/opu/odata/sap/API_SALES_ORDER_SRV",
        alias="SAP_ODATA_URL",
    )
    sap_auth_token: str = Field(default="", alias="SAP_AUTH_TOKEN")
    sap_dry_run: bool = Field(default=True, alias="SAP_DRY_RUN")

    # Currency & FX Rates
    fx_live: bool = Field(default=False, alias="PREFLIGHT_FX_LIVE")
    exchange_rate_api_key: str | None = Field(default=None, alias="EXCHANGE_RATE_API_KEY")

    # Security & Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")

    # Lead Capture & SMTP Notifications
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="contact@popreflight.vn", alias="SMTP_FROM")
    contact_notification_email: str = Field(default="contact@popreflight.vn", alias="CONTACT_NOTIFICATION_EMAIL")

    @field_validator("env")
    @classmethod
    def normalize_env(cls, v: str) -> str:
        return v.strip().lower()

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_production_requirements(self) -> list[str]:
        """Returns list of missing or invalid configuration items when running in production."""
        missing = []
        if self.is_production:
            if not self.session_secret or self.session_secret == "dev-secret-key-change-in-production":
                missing.append("PREFLIGHT_SESSION_SECRET (must be configured with strong secret in production)")
            if not self.database_url or self.database_url.startswith("sqlite"):
                # Warning or requirement for production persistence
                pass
        return missing

    def get_safe_summary(self) -> dict[str, Any]:
        """Returns non-sensitive configuration dictionary with secrets masked."""
        return {
            "environment": self.env,
            "auth_required": self.auth_required,
            "port": self.port,
            "company_name": self.company_name,
            "database_driver": "postgresql" if self.database_url.startswith("postgres") else "sqlite",
            "catalog_path": self.catalog_path,
            "upload_dir": self.upload_dir,
            "gemini_ocr": "configured" if self.gemini_api_key else "unconfigured",
            "telegram": "dry_run" if self.telegram_dry_run else ("live" if self.telegram_bot_token else "unconfigured"),
            "zalo": "dry_run" if self.zalo_dry_run else ("live" if self.zalo_access_token else "unconfigured"),
            "erp_default_adapter": self.erp_default_adapter,
            "fx_mode": "live" if self.fx_live else "static",
            "rate_limiting": "enabled" if self.rate_limit_enabled else "disabled",
            "smtp": "configured" if self.smtp_host else "unconfigured",
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton settings instance."""
    return Settings()


def enforce_startup_configuration(settings: Settings | None = None) -> None:
    """Validates configuration at startup and prints configuration summary."""
    cfg = settings or get_settings()
    errors = cfg.validate_production_requirements()
    if errors:
        sys.stderr.write("====================================================\n")
        sys.stderr.write("CRITICAL CONFIGURATION ERROR (PRODUCTION MODE)\n")
        sys.stderr.write("====================================================\n")
        for err in errors:
            sys.stderr.write(f"  • {err}\n")
        sys.stderr.write("====================================================\n")
        sys.exit(1)
