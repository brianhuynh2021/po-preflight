from __future__ import annotations

import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from preflight.api.errors import Unauthorized
from preflight.api.deps import get_audit_store
from preflight.security.password import hash_password, needs_rehash, verify_password
from preflight.security.rbac import (
    Role,
    UserPrincipal,
    get_api_key_registry,
    get_current_user,
    role_from_str,
)
from preflight.security.session import COOKIE_NAME, SESSION_DURATION_SECONDS, create_session_token
from preflight.store import BaseAuditStore

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Session"])


class LoginRequest(BaseModel):
    username: str | None = Field(None, description="Username for password auth", example="admin")
    password: str | None = Field(None, description="Password for password auth", example="Admin@123456")
    api_key: str | None = Field(None, description="Developer API Key (e.g., pf_dev_mgr_8802)", example="pf_dev_mgr_8802")


class AuthResponse(BaseModel):
    user: str = Field(..., description="Authenticated username", example="operations_manager")
    display_name: str | None = Field(None, description="User display name", example="Trưởng Phòng Vận Hành")
    role: str = Field(..., description="Role name (ADMIN, DIRECTOR, MANAGER, SALES_ADMIN, AUDITOR, VIEWER)", example="MANAGER")
    role_id: int = Field(..., description="Numeric role ID", example=4)
    api_key_id: str | None = Field(None, description="Masked key identifier")
    token: str | None = Field(None, description="JWT session access token")


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="User Session Login",
    description="Authenticate with username & password or an API key and obtain an HttpOnly pf_session JWT session cookie.",
)
def login(
    request: LoginRequest,
    response: Response,
    store: BaseAuditStore = Depends(get_audit_store),
) -> AuthResponse:
    # 1. Username & Password Authentication
    if request.username and request.password:
        clean_user = request.username.strip().lower()
        if store.is_user_locked(clean_user):
            raise HTTPException(
                status_code=429,
                detail="Tài khoản đã bị tạm khóa 15 phút do nhập sai mật khẩu 5 lần liên tiếp.",
            )

        user = store.get_user(clean_user)
        if not user or not user.is_active or not user.password_hash:
            attempts = store.record_failed_login(clean_user)
            if attempts >= 5:
                raise HTTPException(
                    status_code=429,
                    detail="Tài khoản đã bị tạm khóa 15 phút do nhập sai mật khẩu 5 lần liên tiếp.",
                )
            raise Unauthorized("Tên đăng nhập hoặc mật khẩu không chính xác.")

        if not verify_password(request.password, user.password_hash):
            attempts = store.record_failed_login(clean_user)
            if attempts >= 5:
                raise HTTPException(
                    status_code=429,
                    detail="Tài khoản đã bị tạm khóa 15 phút do nhập sai mật khẩu 5 lần liên tiếp.",
                )
            raise Unauthorized("Tên đăng nhập hoặc mật khẩu không chính xác.")

        # Check for Argon2 parameter upgrade
        if needs_rehash(user.password_hash):
            store.update_user(username=user.username, password_hash=hash_password(request.password))

        store.reset_failed_logins(clean_user)
        role = role_from_str(user.role)
        principal = UserPrincipal(
            username=user.username,
            role=role,
            api_key_id=f"usr_{user.id or user.username}",
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
            display_name=user.display_name,
            role=principal.role.name,
            role_id=principal.role.value,
            api_key_id=principal.api_key_id,
            token=session_token,
        )

    # 2. API Key Authentication
    if request.api_key:
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
                    display_name=username,
                    role=principal.role.name,
                    role_id=principal.role.value,
                    api_key_id=principal.api_key_id,
                    token=session_token,
                )

        raise Unauthorized("Khóa API không chính xác hoặc không tồn tại trong hệ thống.")

    raise Unauthorized("Vui lòng cung cấp 'username'/'password' hoặc 'api_key'.")


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
