from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    id: int = Field(..., description="Telegram user ID")
    username: str | None = Field(None, description="Telegram username")
    first_name: str | None = Field(None, description="Telegram first name")


class TelegramMessage(BaseModel):
    message_id: int = Field(..., description="Unique message ID")
    chat_id: int | None = Field(None, description="Chat ID")
    text: str | None = Field(None, description="Message text content")


class TelegramCallbackQuery(BaseModel):
    id: str = Field(..., description="Unique callback query identifier")
    from_user: TelegramUser = Field(..., alias="from", description="Sender of the callback query")
    data: str = Field(..., description="Data associated with the callback button (e.g. approve:1)")
    message: TelegramMessage | None = Field(None, description="Message with the callback button")


class TelegramUpdate(BaseModel):
    update_id: int = Field(..., description="Unique update identifier")
    message: TelegramMessage | None = Field(None, description="New incoming message")
    callback_query: TelegramCallbackQuery | None = Field(None, description="Incoming callback button click")


from typing import Any, Literal


class BotNotificationResult(BaseModel):
    success: bool = Field(..., description="Whether notification was dispatched successfully")
    channel: str = Field(..., description="Target channel (telegram / zalo)")
    order_id: int | str = Field(..., description="Purchase order identifier")
    message_id: str | None = Field(None, description="Dispatched message ID")
    dry_run: bool = Field(False, description="Whether notification was executed in dry-run mode")
    mode: Literal["live", "dry_run", "unconfigured"] = Field("live", description="Bot dispatch execution mode")
    details: str = Field(..., description="Status explanation or error message")


class BotConfigStatus(BaseModel):
    telegram_enabled: bool = Field(..., description="Whether Telegram bot token & chat ID are configured")
    telegram_chat_id: str | None = Field(None, description="Configured Telegram chat ID")
    zalo_enabled: bool = Field(..., description="Whether Zalo OA is configured")
    webhook_url: str = Field(..., description="Registered webhook endpoint")
