from __future__ import annotations

import enum
import os
from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import Depends, Header, HTTPException, status


class Role(enum.IntEnum):
    VIEWER = 1
    AUDITOR = 2
    MANAGER = 3
    ADMIN = 4


@dataclass(frozen=True)
class UserPrincipal:
    username: str
    role: Role
    api_key_id: str


import secrets

# Default dev keys for local development and test harness outside production
DEFAULT_API_KEYS: dict[str, tuple[str, Role]] = {
    "pf_dev_adm_9901": ("system_administrator", Role.ADMIN),
    "pf_dev_mgr_8802": ("operations_manager", Role.MANAGER),
    "pf_dev_aud_7703": ("compliance_auditor", Role.AUDITOR),
    "pf_dev_view_6604": ("readonly_viewer", Role.VIEWER),
}


def get_api_key_registry() -> dict[str, tuple[str, Role]]:
    """Load API key registry. Dev keys are only available outside production."""
    env_name = os.getenv("PREFLIGHT_ENV", "development").strip().lower()
    is_production = env_name in ("production", "prod")

    registry: dict[str, tuple[str, Role]] = {}
    if not is_production:
        registry.update(DEFAULT_API_KEYS)

    for env_key, role in [
        ("PREFLIGHT_ADMIN_KEY", Role.ADMIN),
        ("PREFLIGHT_MANAGER_KEY", Role.MANAGER),
        ("PREFLIGHT_AUDITOR_KEY", Role.AUDITOR),
        ("PREFLIGHT_VIEWER_KEY", Role.VIEWER),
    ]:
        val = os.getenv(env_key)
        if val:
            registry[val] = (f"{role.name.lower()}_user", role)
    return registry


from preflight.api.errors import Forbidden, Unauthorized


from fastapi import Cookie, Depends, Header, HTTPException, status


def get_current_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    pf_session: Optional[str] = Cookie(None, alias="pf_session"),
) -> UserPrincipal:
    """Validate Session Cookie, API Key or Bearer Token and return authenticated UserPrincipal."""
    auth_required = os.getenv("PREFLIGHT_AUTH_REQUIRED", "true").lower() in ("true", "1", "yes")

    # 1. Check Session Cookie
    if pf_session:
        from preflight.security.session import verify_session_token
        try:
            return verify_session_token(pf_session)
        except Unauthorized:
            # If cookie is expired or invalid, fall through to check headers before rejecting
            pass

    # 2. Check API Key or Authorization Bearer header
    registry = get_api_key_registry()
    token = None
    if x_api_key:
        token = x_api_key.strip()
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if token:
        for registered_key, (username, role) in registry.items():
            if secrets.compare_digest(token, registered_key):
                return UserPrincipal(username=username, role=role, api_key_id=token[:8] + "...")
        raise Unauthorized("Khóa API không hợp lệ hoặc đã hết hạn.")

    if auth_required:
        raise Unauthorized("Yêu cầu xác thực. Vui lòng cung cấp cookie 'pf_session' hoặc header 'X-API-Key'.")

    # Open development mode — never allowed in production
    env_name = os.getenv("PREFLIGHT_ENV", "development").strip().lower()
    if env_name in ("production", "prod"):
        raise Unauthorized("Yêu cầu xác thực bắt buộc trong môi trường production.")

    return UserPrincipal(
        username="dev_admin",
        role=Role.ADMIN,
        api_key_id="dev_mode_open",
    )



def require_role(min_role: Role) -> Callable[[UserPrincipal], UserPrincipal]:
    """Dependency factory enforcing minimum required Role-Based Access Control."""

    def role_checker(user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
        if user.role < min_role:
            raise Forbidden(
                f"Truy cập bị từ chối: Yêu cầu vai trò tối thiểu '{min_role.name}' (Vai trò hiện tại của bạn: '{user.role.name}')."
            )
        return user

    return role_checker
