from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from preflight.api.errors import Forbidden, NotFound, ValidationFailed
from preflight.api.deps import get_audit_store
from preflight.models import User
from preflight.security.password import hash_password, validate_password_strength
from preflight.security.rbac import Role, UserPrincipal, get_current_user, require_role, role_from_str
from preflight.store import BaseAuditStore

router = APIRouter(prefix="/api/v1/users", tags=["User Management"])


class UserOut(BaseModel):
    id: int | None = None
    org_id: str
    username: str
    display_name: str
    email: str
    role: str
    is_active: bool
    failed_attempts: int
    locked_until: str | None = None
    created_at: str


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="Unique username")
    display_name: str = Field(..., min_length=2, max_length=128, description="Full name")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Initial password")
    role: str = Field("viewer", description="Role: admin, director, manager, sales_admin, auditor, viewer")
    org_id: str = Field("org_default", description="Organization ID")


class UpdateUserRequest(BaseModel):
    display_name: str | None = Field(None, min_length=2, max_length=128)
    email: str | None = None
    role: str | None = Field(None, description="Role: admin, director, manager, sales_admin, auditor, viewer")
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, description="New password")


@router.get(
    "",
    response_model=list[UserOut],
    summary="List Users",
    description="Retrieve all registered users and their roles.",
)
def list_users(
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: BaseAuditStore = Depends(get_audit_store),
) -> list[UserOut]:
    users = store.list_users()
    return [
        UserOut(
            id=u.id,
            org_id=u.org_id,
            username=u.username,
            display_name=u.display_name,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            failed_attempts=u.failed_attempts,
            locked_until=u.locked_until,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post(
    "",
    response_model=UserOut,
    status_code=201,
    summary="Create User",
    description="Create a new user account with Argon2 hashed password.",
)
def create_user(
    payload: CreateUserRequest,
    user: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: BaseAuditStore = Depends(get_audit_store),
) -> UserOut:
    clean_username = payload.username.strip().lower()
    existing = store.get_user(clean_username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tên người dùng '{clean_username}' đã tồn tại trong hệ thống.",
        )

    # Validate password strength
    valid_pwd, pwd_err = validate_password_strength(payload.password)
    if not valid_pwd:
        raise ValidationFailed(pwd_err or "Mật khẩu không đạt tiêu chuẩn bảo mật.")

    role_val = role_from_str(payload.role).name.lower()
    pwd_hash = hash_password(payload.password)

    new_u = User(
        org_id=payload.org_id,
        username=clean_username,
        display_name=payload.display_name.strip(),
        email=str(payload.email).strip().lower(),
        password_hash=pwd_hash,
        role=role_val,
        is_active=True,
    )
    saved = store.create_user(new_u)
    return UserOut(
        id=saved.id,
        org_id=saved.org_id,
        username=saved.username,
        display_name=saved.display_name,
        email=saved.email,
        role=saved.role,
        is_active=saved.is_active,
        failed_attempts=saved.failed_attempts,
        locked_until=saved.locked_until,
        created_at=saved.created_at,
    )


@router.get(
    "/{username}",
    response_model=UserOut,
    summary="Get User Detail",
    description="Get details for a specific user.",
)
def get_user(
    username: str,
    user: UserPrincipal = Depends(get_current_user),
    store: BaseAuditStore = Depends(get_audit_store),
) -> UserOut:
    clean = username.strip().lower()
    if user.role < Role.ADMIN and user.username.lower() != clean:
        raise Forbidden("Bạn không có quyền xem thông tin tài khoản người dùng khác.")

    u = store.get_user(clean)
    if not u:
        raise NotFound(f"Không tìm thấy người dùng '{username}'.")

    return UserOut(
        id=u.id,
        org_id=u.org_id,
        username=u.username,
        display_name=u.display_name,
        email=u.email,
        role=u.role,
        is_active=u.is_active,
        failed_attempts=u.failed_attempts,
        locked_until=u.locked_until,
        created_at=u.created_at,
    )


@router.put(
    "/{username}",
    response_model=UserOut,
    summary="Update User",
    description="Update user profile, role, or active status.",
)
def update_user(
    username: str,
    payload: UpdateUserRequest,
    user: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: BaseAuditStore = Depends(get_audit_store),
) -> UserOut:
    clean = username.strip().lower()
    existing = store.get_user(clean)
    if not existing:
        raise NotFound(f"Không tìm thấy người dùng '{username}'.")

    role_val = role_from_str(payload.role).name.lower() if payload.role is not None else None

    updated = store.update_user(
        username=clean,
        display_name=payload.display_name,
        email=str(payload.email) if payload.email is not None else None,
        role=role_val,
        is_active=payload.is_active,
    )
    if not updated:
        raise NotFound(f"Không tìm thấy người dùng '{username}'.")

    return UserOut(
        id=updated.id,
        org_id=updated.org_id,
        username=updated.username,
        display_name=updated.display_name,
        email=updated.email,
        role=updated.role,
        is_active=updated.is_active,
        failed_attempts=updated.failed_attempts,
        locked_until=updated.locked_until,
        created_at=updated.created_at,
    )


@router.delete(
    "/{username}",
    summary="Delete User",
    description="Permanently delete a user account.",
)
def delete_user(
    username: str,
    user: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: BaseAuditStore = Depends(get_audit_store),
) -> dict[str, Any]:
    clean = username.strip().lower()
    if clean == user.username.lower():
        raise ValidationFailed("Không thể xóa tài khoản của chính mình đang đăng nhập.")

    deleted = store.delete_user(clean)
    if not deleted:
        raise NotFound(f"Không tìm thấy người dùng '{username}'.")

    return {"success": True, "message": f"Đã xóa người dùng '{username}' thành công."}


@router.post(
    "/{username}/reset-password",
    summary="Reset User Password",
    description="Reset a user's password using Argon2 hashing.",
)
def reset_password(
    username: str,
    payload: ResetPasswordRequest,
    user: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: BaseAuditStore = Depends(get_audit_store),
) -> dict[str, Any]:
    clean = username.strip().lower()
    existing = store.get_user(clean)
    if not existing:
        raise NotFound(f"Không tìm thấy người dùng '{username}'.")

    valid_pwd, pwd_err = validate_password_strength(payload.new_password)
    if not valid_pwd:
        raise ValidationFailed(pwd_err or "Mật khẩu không đạt tiêu chuẩn bảo mật.")

    new_hash = hash_password(payload.new_password)
    store.update_user(username=clean, password_hash=new_hash)
    store.reset_failed_logins(clean)

    return {"success": True, "message": f"Đã đặt lại mật khẩu cho '{username}' thành công."}


@router.post(
    "/{username}/unlock",
    summary="Unlock User Account",
    description="Manually unlock a locked user account and reset failed login attempts.",
)
def unlock_user(
    username: str,
    user: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: BaseAuditStore = Depends(get_audit_store),
) -> dict[str, Any]:
    clean = username.strip().lower()
    existing = store.get_user(clean)
    if not existing:
        raise NotFound(f"Không tìm thấy người dùng '{username}'.")

    store.reset_failed_logins(clean)
    return {"success": True, "message": f"Đã mở khóa tài khoản '{username}' thành công."}
