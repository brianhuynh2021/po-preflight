from __future__ import annotations

import secrets
from typing import Any

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from preflight.api.errors import Unauthorized
from preflight.security.rbac import Role, UserPrincipal, get_api_key_registry, get_current_user
from preflight.security.session import COOKIE_NAME, SESSION_DURATION_SECONDS, create_session_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Session"])


class LoginRequest(BaseModel):
    api_key: str = Field(..., description="Developer API Key (e.g., pf_dev_mgr_8802)", example="pf_dev_mgr_8802")


class AuthResponse(BaseModel):
    user: str = Field(..., description="Authenticated username", example="operations_manager")
    role: str = Field(..., description="Role name (ADMIN, MANAGER, AUDITOR, VIEWER)", example="MANAGER")
    role_id: int = Field(..., description="Numeric role ID", example=3)
    api_key_id: str | None = Field(None, description="Masked key identifier")


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="User Session Login",
    description="Authenticate with an API key and obtain an HttpOnly pf_session JWT session cookie.",
)
def login(request: LoginRequest, response: Response) -> AuthResponse:
    registry = get_api_key_registry()
    token = request.api_key.strip()

    for registered_key, (username, role) in registry.items():
        if secrets.compare_digest(token, registered_key):
            principal = UserPrincipal(
                username=username,
                role=role,
                api_key_id=token[:8] + "...",
            )
            session_token = create_session_token(principal)
            response.set_cookie(
                key=COOKIE_NAME,
                value=session_token,
                httponly=True,
                samesite="lax",
                max_age=SESSION_DURATION_SECONDS,
                path="/",
            )
            return AuthResponse(
                user=principal.username,
                role=principal.role.name,
                role_id=principal.role.value,
                api_key_id=principal.api_key_id,
            )

    raise Unauthorized("Khóa API không chính xác hoặc không tồn tại trong hệ thống.")


@router.get(
    "/me",
    response_model=AuthResponse,
    summary="Get Current User Profile",
    description="Retrieve the currently authenticated user identity and role.",
)
def get_me(principal: UserPrincipal = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(
        user=principal.username,
        role=principal.role.name,
        role_id=principal.role.value,
        api_key_id=principal.api_key_id,
    )


@router.post(
    "/logout",
    summary="User Session Logout",
    description="Clear the pf_session cookie.",
)
def logout(response: Response) -> dict[str, Any]:
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {
        "success": True,
        "message": "Đã đăng xuất thành công.",
    }
