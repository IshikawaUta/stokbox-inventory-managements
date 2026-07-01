"""Utilitas keamanan: hashing password, dsb."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from typing import Tuple


def _pbkdf2(password: str, salt: bytes, iterations: int = 120_000) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def hash_password(password: str) -> str:
    """Hash password menggunakan PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    digest = _pbkdf2(password, salt)
    return f"pbkdf2_sha256$120000${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verifikasi password terhadap hash PBKDF2."""
    try:
        algo, iter_str, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    candidate = _pbkdf2(password, salt, int(iter_str))
    return hmac.compare_digest(expected, candidate)


def generate_no_transaksi(prefix: str) -> str:
    """Buat nomor transaksi: PREFIX-YYYYMMDD-XXXXXX."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    suffix = secrets.token_hex(3).upper()
    return f"{prefix}-{now.strftime('%Y%m%d')}-{suffix}"
