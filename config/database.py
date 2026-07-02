"""Konfigurasi dan koneksi basis data MongoDB Atlas."""
from __future__ import annotations

import os
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

MONGO_URI = os.getenv("MONGO_URI", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "inventaris")
USE_MONGOMOCK = os.getenv("USE_MONGOMOCK", "").lower() in {"1", "true", "yes"}

_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def _build_client() -> MongoClient:
    if USE_MONGOMOCK:
        try:
            import mongomock
            return mongomock.MongoClient()
        except ImportError as exc:
            raise RuntimeError(
                "USE_MONGOMOCK=1 membutuhkan paket 'mongomock'."
            ) from exc
    if not MONGO_URI:
        raise RuntimeError(
            "MONGO_URI belum dikonfigurasi. Atur pada file .env"
        )
    return MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=50,
        minPoolSize=5,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
    )


def get_client() -> MongoClient:
    """Mengembalikan instance MongoClient (singleton)."""
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def get_db() -> Database:
    """Mengembalikan instance Database."""
    global _db
    if _db is None:
        _db = get_client()[MONGO_DB_NAME]
        _ensure_indexes(_db)
    return _db


def _ensure_indexes(db: Database) -> None:
    """Membuat index yang dibutuhkan untuk performa query."""
    db["users"].create_index("email", unique=True, background=True)
    db["kategori"].create_index("nama_kategori", unique=True, background=True)
    db["barang"].create_index("kode_barang", unique=True, background=True)
    db["barang"].create_index("kategori_id", background=True)
    db["suplier"].create_index("nama", background=True)
    db["barang_masuk"].create_index("no_transaksi", unique=True, background=True)
    db["barang_masuk"].create_index("tanggal_masuk", background=True)
    db["barang_keluar"].create_index("no_transaksi", unique=True, background=True)
    db["barang_keluar"].create_index("tanggal_keluar", background=True)
    db["stok_penyesuaian"].create_index("no_penyesuaian", unique=True, background=True)
    db["stok_penyesuaian"].create_index("barang_id", background=True)
    db["setting"].create_index("key", unique=True, background=True)


def reset_db() -> None:
    """Reset singleton (untuk testing)."""
    global _client, _db
    _client = None
    _db = None


def collection(name: str) -> Collection:
    """Akses cepat ke sebuah koleksi."""
    return get_db()[name]


def ping() -> bool:
    """Cek koneksi MongoDB. Mengembalikan True jika berhasil."""
    try:
        if USE_MONGOMOCK:
            return True
        get_client().admin.command("ping")
        return True
    except Exception:
        return False
