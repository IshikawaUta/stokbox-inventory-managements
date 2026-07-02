"""Unit test untuk utils/security.py."""
from __future__ import annotations

from utils.security import (
    hash_password,
    verify_password,
    generate_no_transaksi,
)


class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("password123")
        assert isinstance(result, str)

    def test_starts_with_algo_prefix(self):
        result = hash_password("password123")
        assert result.startswith("pbkdf2_sha256$")

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("password123")
        h2 = hash_password("password123")
        assert h1 != h2

    def test_hash_contains_iterations(self):
        result = hash_password("password123")
        parts = result.split("$")
        assert len(parts) == 4
        assert parts[1] == "120000"


class TestVerifyPassword:
    def test_correct_password(self):
        hashed = hash_password("admin123")
        assert verify_password("admin123", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("admin123")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_stored_hash(self):
        assert verify_password("password", "") is False

    def test_invalid_format(self):
        assert verify_password("password", "invalid-hash-format") is False

    def test_wrong_algo(self):
        assert verify_password("password", "md5$1000$abc$def") is False

    def test_different_passwords_fail(self):
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert verify_password("password1", h2) is False
        assert verify_password("password2", h1) is False


class TestGenerateNoTransaksi:
    def test_starts_with_prefix(self):
        result = generate_no_transaksi("BM")
        assert result.startswith("BM-")

    def test_format_prefix_date_hex(self):
        result = generate_no_transaksi("BK")
        parts = result.split("-")
        assert len(parts) == 3
        assert parts[0] == "BK"
        assert len(parts[1]) == 8
        assert len(parts[2]) == 6

    def test_different_prefixes(self):
        bm = generate_no_transaksi("BM")
        bk = generate_no_transaksi("BK")
        sp = generate_no_transaksi("SP")
        assert bm.startswith("BM-")
        assert bk.startswith("BK-")
        assert sp.startswith("SP-")

    def test_unique_results(self):
        results = {generate_no_transaksi("BM") for _ in range(100)}
        assert len(results) == 100
