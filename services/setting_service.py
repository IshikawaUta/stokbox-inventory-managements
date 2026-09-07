"""Service untuk pengaturan aplikasi."""
from __future__ import annotations

from typing import Optional

from models import setting
from utils.helpers import serialize_doc, serialize_docs, utcnow


DEFAULTS = {
    "nama_aplikasi": "InventarisKu",
    "judul_aplikasi": "Sistem Manajemen Inventaris",
    "tagline": "Kelola barang, kategori, suplier, dan transaksi dengan mudah.",
    "nama_perusahaan": "PT. Inventaris Nusantara",
    "logo": None,
    "favicon": None,
}


def _get_cache():
    from config.cache import cache
    return cache


def get_settings() -> dict:
    """Kembalikan seluruh setting sebagai dict (cached 5 menit)."""
    cached = _get_cache().get("app_settings")
    if cached is not None:
        return cached
    result = dict(DEFAULTS)
    for doc in setting().find():
        result[doc["key"]] = doc.get("value")
    _get_cache().set("app_settings", result, ttl=300)
    return result


def get_setting(key: str, default=None):
    doc = setting().find_one({"key": key})
    return doc.get("value") if doc else default


def update_settings(payload: dict) -> dict:
    for key, value in payload.items():
        if key not in DEFAULTS:
            continue
        setting().update_one(
            {"key": key},
            {"$set": {"value": value, "updated_at": utcnow()}},
            upsert=True,
        )
    _get_cache().invalidate("app_settings")
    return get_settings()


def upload_asset(kind: str, raw: bytes, filename: str, content_type: str) -> dict:
    """Upload logo/favicon dan simpan URL ke setting."""
    if kind not in {"logo", "favicon"}:
        raise ValueError("Kind harus 'logo' atau 'favicon'.")
    try:
        from config.cloudinary_client import upload_file
        result = upload_file(raw, folder="settings", resource_type="image", public_id=kind)
        url = result.get("secure_url") or result.get("url")
    except Exception:
        from pathlib import Path
        ext = (filename.rsplit(".", 1)[-1] if "." in filename else "png").lower()
        upload_dir = Path("static/uploads/settings")
        upload_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{kind}.{ext}"
        path = upload_dir / fname
        path.write_bytes(raw)
        url = f"/static/uploads/settings/{fname}"
    setting().update_one(
        {"key": kind},
        {"$set": {"value": url, "updated_at": utcnow()}},
        upsert=True,
    )
    _get_cache().invalidate("app_settings")
    return {kind: url}
