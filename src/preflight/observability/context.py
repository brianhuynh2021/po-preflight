from __future__ import annotations

import contextvars
from typing import Any

# Global context variables for request correlation
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")
order_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("order_id", default="")


def get_request_id() -> str:
    return request_id_var.get()


def set_request_id(req_id: str) -> contextvars.Token[str]:
    return request_id_var.set(req_id)


def get_user_id() -> str:
    return user_id_var.get()


def set_user_id(user_id: str) -> contextvars.Token[str]:
    return user_id_var.set(user_id)


def get_order_id() -> str:
    return order_id_var.get()


def set_order_id(order_id: str) -> contextvars.Token[str]:
    return order_id_var.set(order_id)


def get_logging_context() -> dict[str, str]:
    ctx: dict[str, str] = {}
    req = get_request_id()
    if req:
        ctx["request_id"] = req
    user = get_user_id()
    if user:
        ctx["user_id"] = user
    order = get_order_id()
    if order:
        ctx["order_id"] = order
    return ctx
