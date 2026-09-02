from __future__ import annotations

import os
import time
from typing import Any

import jwt

from preflight.api.errors import ConfigurationError, Unauthorized
from preflight.security.rbac import Role, UserPrincipal

COOKIE_NAME = "pf_session"
SESSION_DURATION_SECONDS = 8 * 3600  # 8 hours
DEFAULT_DEV_SECRET = "dev_preflight_jwt_secret_key_8899"


def get_jwt_secret() -> str:
    secret = os.getenv("PREFLIGHT_SESSION_SECRET")
    env_name = os.getenv("PREFLIGHT_ENV", "development").strip().lower()
    is_prod = env_name in ("production", "prod")

    if not secret:
        if is_prod:
            raise ConfigurationError(
                "PREFLIGHT_SESSION_SECRET bắt buộc phải được cấu hình trong môi trường Production."
            )
        return DEFAULT_DEV_SECRET
    return secret


def create_session_token(principal: UserPrincipal) -> str:
    secret = get_jwt_secret()
    now = int(time.time())
    payload = {
        "sub": principal.username,
        "role": principal.role.name,
        "role_id": principal.role.value,
        "api_key_id": principal.api_key_id,
        "iat": now,
        "exp": now + SESSION_DURATION_SECONDS,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_session_token(token: str) -> UserPrincipal:
    secret = get_jwt_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        username = payload.get("sub")
        role_name = payload.get("role")
        api_key_id = payload.get("api_key_id", "session")

        if not username or not role_name or role_name not in Role.__members__:
            raise Unauthorized("Phiên đăng nhập không hợp lệ hoặc đã hết hạn.")

        role = Role[role_name]
        return UserPrincipal(username=username, role=role, api_key_id=api_key_id)
    except jwt.ExpiredSignatureError as exc:
        raise Unauthorized("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.") from exc
    except jwt.PyJWTError as exc:
        raise Unauthorized("Mã định danh phiên không hợp lệ.") from exc
