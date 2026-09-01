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


# Default enterprise demo keys
DEFAULT_API_KEYS: dict[str, tuple[str, Role]] = {
    "pf_live_adm_9901": ("system_administrator", Role.ADMIN),
    "pf_live_mgr_8802": ("operations_manager", Role.MANAGER),
    "pf_live_aud_7703": ("compliance_auditor", Role.AUDITOR),
    "pf_live_view_6604": ("readonly_viewer", Role.VIEWER),
}


def get_api_key_registry() -> dict[str, tuple[str, Role]]:
    """Load API key registry from environment or fallback to defaults."""
    registry = dict(DEFAULT_API_KEYS)
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


def get_current_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> UserPrincipal:
    """Validate API Key or Bearer Token and return authenticated UserPrincipal."""
    auth_required = os.getenv("PREFLIGHT_AUTH_REQUIRED", "false").lower() in ("true", "1", "yes")
    registry = get_api_key_registry()

    token = None
    if x_api_key:
        token = x_api_key.strip()
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if token:
        if token in registry:
            username, role = registry[token]
            return UserPrincipal(username=username, role=role, api_key_id=token[:8] + "...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if auth_required:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide 'X-API-Key' or 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # In open development mode, default to Admin privileges
    return UserPrincipal(
        username="dev_admin",
        role=Role.ADMIN,
        api_key_id="dev_mode_open",
    )


def require_role(min_role: Role) -> Callable[[UserPrincipal], UserPrincipal]:
    """Dependency factory enforcing minimum required Role-Based Access Control."""

    def role_checker(user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
        if user.role < min_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires at least '{min_role.name}' role (Your role: '{user.role.name}').",
            )
        return user

    return role_checker
