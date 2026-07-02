"""Konfigurasi fixtures untuk seluruh suite tes."""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import date, datetime, timezone
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId

# Pastikan root project ada di sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["USE_MONGOMOCK"] = "1"
os.environ["MONGO_URI"] = ""
os.environ["MONGO_DB_NAME"] = "test_inventaris"
os.environ["APP_SECRET_KEY"] = "test-secret-key"
os.environ["FENRIR_DEV_MODE"] = "0"
# Disable rate limiting during tests
os.environ["FENRIR_RATE_LIMIT"] = "0"


@pytest.fixture(autouse=True)
def _reset_db():
    """Reset singleton DB sebelum dan sesudah setiap tes."""
    from config.database import reset_db
    reset_db()
    yield
    reset_db()


@pytest.fixture(autouse=True)
def _disable_rate_limit():
    """Nonaktifkan rate limit selama testing."""
    from app import app
    from fenrir.middleware import RateLimitMiddleware
    # Remove RateLimitMiddleware before the ASGI stack is compiled
    original = list(app._asgi_middlewares)
    app._asgi_middlewares = [
        (cls, opts) for cls, opts in app._asgi_middlewares
        if cls is not RateLimitMiddleware
    ]
    app._asgi_app = None  # Force recompilation
    yield
    app._asgi_middlewares = original
    app._asgi_app = None


@pytest.fixture()
def db():
    """Mengembalikan instance Database mongomock."""
    from config.database import get_db
    return get_db()


@pytest.fixture()
def mock_session():
    """Mock fenrir.session untuk service tests yang akses session di luar request."""
    session_data = {}
    mock = MagicMock()
    mock.get = lambda key, default=None: session_data.get(key, default)
    mock.__getitem__ = lambda self, key: session_data[key]
    mock.__setitem__ = lambda self, key, value: session_data.__setitem__(key, value)
    mock.__contains__ = lambda self, key: key in session_data
    mock.clear = lambda: session_data.clear()
    mock.keys = lambda: session_data.keys()

    with patch("fenrir.session", mock):
        yield session_data


@pytest.fixture()
def client():
    """Mengembalikan Fenrir test client wrapper synchronous dengan session persist."""
    from app import app
    from fenrir.testing import FenrirTestClient

    class SyncClient:
        def __init__(self, app):
            self._app = app
            self._tc = None
            self._entered = False

        def _ensure_client(self):
            if not self._entered:
                self._tc = FenrirTestClient(self._app)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._tc.__aenter__())
                self._entered = True

        def request(self, method, url, **kwargs):
            self._ensure_client()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._tc.request(method, url, **kwargs))

        def get(self, url, **kwargs):
            return self.request("GET", url, **kwargs)

        def post(self, url, **kwargs):
            return self.request("POST", url, **kwargs)

        def put(self, url, **kwargs):
            return self.request("PUT", url, **kwargs)

        def delete(self, url, **kwargs):
            return self.request("DELETE", url, **kwargs)

    yield SyncClient(app)


# ── Sample data fixtures ──────────────────────────────────────────────


@pytest.fixture()
def sample_user(db) -> dict:
    """Insert user admin ke DB dan kembalikan datanya."""
    from utils.security import hash_password
    uid = ObjectId()
    doc = {
        "_id": uid,
        "name": "Admin Test",
        "email": "admin@test.com",
        "password": hash_password("admin123"),
        "role": "admin",
        "photo": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }
    db["users"].insert_one(doc)
    return doc


@pytest.fixture()
def sample_staff_user(db) -> dict:
    """Insert user staff ke DB."""
    from utils.security import hash_password
    uid = ObjectId()
    doc = {
        "_id": uid,
        "name": "Staff Test",
        "email": "staff@test.com",
        "password": hash_password("staff123"),
        "role": "staff",
        "photo": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }
    db["users"].insert_one(doc)
    return doc


@pytest.fixture()
def sample_kategori(db) -> dict:
    """Insert kategori ke DB."""
    kid = ObjectId()
    doc = {
        "_id": kid,
        "nama_kategori": "Elektronik",
        "icon_kategori": "bi-laptop",
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }
    db["kategori"].insert_one(doc)
    return doc


@pytest.fixture()
def sample_suplier(db) -> dict:
    """Insert suplier ke DB."""
    sid = ObjectId()
    doc = {
        "_id": sid,
        "nama": "Suplier A",
        "no_hp": "081234567890",
        "email": "suplier@a.com",
        "alamat": "Jakarta",
        "perusahaan": "PT. Suplier A",
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }
    db["suplier"].insert_one(doc)
    return doc


@pytest.fixture()
def sample_barang(db, sample_kategori) -> dict:
    """Insert barang ke DB."""
    bid = ObjectId()
    doc = {
        "_id": bid,
        "kode_barang": "BRG-001",
        "nama_barang": "Laptop Asus",
        "deskripsi_barang": "Laptop untuk kerja",
        "kategori_id": sample_kategori["_id"],
        "satuan": "pcs",
        "lokasi_barang": "Gudang A",
        "stok_awal": 10,
        "stok_minimum": 2,
        "stok": 10,
        "harga_satuan": 10000000,
        "qrcode": "BRG-001",
        "barcode": "BRG-001",
        "foto": None,
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }
    db["barang"].insert_one(doc)
    return doc


@pytest.fixture()
def sample_barang_stok_zero(db, sample_kategori) -> dict:
    """Insert barang dengan stok 0."""
    bid = ObjectId()
    doc = {
        "_id": bid,
        "kode_barang": "BRG-002",
        "nama_barang": "Mouse Logitech",
        "deskripsi_barang": None,
        "kategori_id": sample_kategori["_id"],
        "satuan": "pcs",
        "lokasi_barang": None,
        "stok_awal": 0,
        "stok_minimum": 5,
        "stok": 0,
        "harga_satuan": 250000,
        "qrcode": "BRG-002",
        "barcode": "BRG-002",
        "foto": None,
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }
    db["barang"].insert_one(doc)
    return doc


@pytest.fixture()
def sample_setting(db):
    """Insert setting default."""
    db["setting"].insert_one({
        "key": "nama_aplikasi",
        "value": "InventarisKu",
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
    })
    db["setting"].insert_one({
        "key": "nama_perusahaan",
        "value": "PT. Test",
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
    })


# ── Session helper ────────────────────────────────────────────────────


def login_as(client, user: dict) -> None:
    """Helper: login sebagai user tertentu via POST /auth/login."""
    client.post("/auth/login", json={
        "email": user["email"],
        "password": "admin123" if user.get("role") == "admin" else "staff123",
    })
