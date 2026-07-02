"""Tambahan test untuk utils/decorators.py, config/database.py, app.py."""
from __future__ import annotations

from unittest.mock import patch, MagicMock
from bson import ObjectId


# ── Decorators ────────────────────────────────────────────────────────


class TestDecorators:
    def test_login_required_redirect(self, client):
        resp = client.get("/dashboard")
        assert resp.status_code in (302, 401)

    def test_api_login_required_401(self, client):
        resp = client.get("/api/barang/")
        assert resp.status_code == 401

    def test_role_required_403(self, client, sample_staff_user):
        login_as_admin = client.post("/auth/login", json={
            "email": "staff@test.com",
            "password": "staff123",
        })
        resp = client.get("/api/barang/low-stock")
        assert resp.status_code == 403

    def test_role_required_not_logged_in(self, client):
        resp = client.get("/api/barang/low-stock")
        assert resp.status_code == 401


# Need to import login_as for the test above
from tests.conftest import login_as


# ── Config Database ───────────────────────────────────────────────────


class TestConfigDatabase:
    def test_ping_mongomock(self, db):
        from config.database import ping
        assert ping() is True

    def test_collection(self, db):
        from config.database import collection
        col = collection("users")
        assert col is not None

    def test_reset_db(self):
        from config.database import reset_db, get_db, _client, _db
        reset_db()
        import config.database
        assert config.database._client is None
        assert config.database._db is None

    def test_get_db_creates_indexes(self, db):
        from config.database import get_db
        result = get_db()
        assert result is not None


class TestCloudinaryClient:
    def test_is_configured_false(self):
        import os
        os.environ.pop("CLOUDINARY_URL", None)
        os.environ.pop("CLOUDINARY_CLOUD_NAME", None)
        from config.cloudinary_client import is_configured
        assert is_configured() is False

    def test_get_folder(self):
        from config.cloudinary_client import get_folder
        result = get_folder()
        assert isinstance(result, str)

    def test_parse_cloudinary_url_valid(self):
        from config.cloudinary_client import _parse_cloudinary_url
        result = _parse_cloudinary_url("cloudinary://key:secret@cloud")
        assert result == ("cloud", "key", "secret")

    def test_parse_cloudinary_url_empty(self):
        from config.cloudinary_client import _parse_cloudinary_url
        assert _parse_cloudinary_url("") is None
        assert _parse_cloudinary_url(None) is None

    def test_parse_cloudinary_url_invalid(self):
        from config.cloudinary_client import _parse_cloudinary_url
        assert _parse_cloudinary_url("invalid-url") is None

    def test_configure_no_creds(self):
        import os
        os.environ.pop("CLOUDINARY_URL", None)
        os.environ.pop("CLOUDINARY_CLOUD_NAME", None)
        from config.cloudinary_client import configure
        configure()

    def test_reload_env(self):
        from config.cloudinary_client import reload_env
        reload_env()


# ── App.py ────────────────────────────────────────────────────────────


class TestAppFilters:
    def test_format_number(self):
        from app import _format_number
        assert _format_number(1000000) == "1.000.000"
        assert _format_number(None) == "0"
        assert _format_number("abc") == "0"
        assert _format_number(0) == "0"
        assert _format_number(42) == "42"

    def test_format_rupiah(self):
        from app import _format_rupiah
        assert _format_rupiah(1000000) == "Rp 1.000.000"
        assert _format_rupiah(None) == "Rp 0"
        assert _format_rupiah("abc") == "Rp 0"
        assert _format_rupiah(0) == "Rp 0"

    def test_format_date(self):
        from app import _format_date
        from datetime import datetime
        assert _format_date(datetime(2025, 1, 15)) == "15/01/2025"
        assert _format_date(datetime(2025, 12, 31, 10, 30)) == "31/12/2025"
        assert _format_date("") == "-"
        assert _format_date(None) == "-"
        assert _format_date("invalid-date") == "invalid-date"

    def test_format_date_with_string(self):
        from app import _format_date
        result = _format_date("2025-01-15")
        assert isinstance(result, str)

    def test_format_datetime(self):
        from app import _format_datetime
        from datetime import datetime
        assert _format_datetime(datetime(2025, 1, 15, 10, 30)) == "15/01/2025 10:30"
        assert _format_datetime(datetime(2025, 12, 31, 23, 59)) == "31/12/2025 23:59"
        assert _format_datetime("") == "-"
        assert _format_datetime(None) == "-"
        assert _format_datetime("invalid") == "invalid"

    def test_format_datetime_with_string(self):
        from app import _format_datetime
        result = _format_datetime("2025-01-15T10:30:00.000")
        assert isinstance(result, str)


class TestAppHealth:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["mongo"] == "connected"


class TestAppSessionProxy:
    def test_session_proxy_exists(self):
        from app import _SessionProxy
        proxy = _SessionProxy()
        assert proxy is not None

    def test_session_proxy_methods_exist(self):
        from app import _SessionProxy
        proxy = _SessionProxy()
        assert callable(getattr(proxy, "get", None))
        assert callable(getattr(proxy, "keys", None))
