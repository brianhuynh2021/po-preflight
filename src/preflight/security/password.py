"""Secure password hashing and verification using Argon2."""

from __future__ import annotations

import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

logger = logging.getLogger("PreflightAuth")

# Configure Argon2 Password Hasher with OWASP recommended parameters
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    if not plain_password:
        raise ValueError("Mật khẩu không được để trống.")
    return _hasher.hash(plain_password)


def verify_password(arg1: str, arg2: str) -> bool:
    """Verify a plaintext password against an Argon2 hash, accepting (plain, hash) or (hash, plain)."""
    if not arg1 or not arg2:
        return False
    if arg1.startswith("$"):
        p_hash, plain = arg1, arg2
    elif arg2.startswith("$"):
        plain, p_hash = arg1, arg2
    else:
        return False
    try:
        return _hasher.verify(p_hash, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception as exc:
        logger.warning(f"Unexpected error verifying password hash: {exc}")
        return False


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """Validate password meets minimum security standards."""
    if not password or len(password) < 8:
        return False, "Mật khẩu phải có độ dài tối thiểu 8 ký tự."
    has_letter = any(c.isalpha() for c in password)
    has_digit_or_symbol = any(not c.isalpha() for c in password)
    if not (has_letter and has_digit_or_symbol):
        return False, "Mật khẩu phải bao gồm cả chữ cái và số/ký tự đặc biệt."
    return True, None


def needs_rehash(password_hash: str) -> bool:
    """Check if password hash needs to be upgraded to newer parameters."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except Exception:
        return True
