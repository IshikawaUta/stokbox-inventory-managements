"""Service untuk suplier."""
from __future__ import annotations

from typing import Optional

from models import suplier
from utils.helpers import parse_object_id, serialize_doc, serialize_docs, utcnow


def _get_cache():
    """Lazy import cache untuk hindari circular import."""
    from config.cache import cache
    return cache


def list_suplier(keyword: str = "") -> list[dict]:
    cache_key = f"suplier_list:{keyword}"
    cached = _get_cache().get(cache_key)
    if cached is not None:
        return cached
    query: dict = {}
    if keyword:
        query["$or"] = [
            {"nama": {"$regex": keyword, "$options": "i"}},
            {"perusahaan": {"$regex": keyword, "$options": "i"}},
        ]
    result = serialize_docs(list(suplier().find(query).sort("nama", 1)))
    _get_cache().set(cache_key, result, ttl=300)
    return result


def get_suplier(suplier_id: str) -> Optional[dict]:
    oid = parse_object_id(suplier_id)
    if oid is None:
        return None
    return serialize_doc(suplier().find_one({"_id": oid}))


def create_suplier(payload: dict) -> dict:
    nama = (payload.get("nama") or "").strip()
    if not nama:
        raise ValueError("Nama suplier wajib diisi.")
    doc = {
        "nama": nama,
        "no_hp": (payload.get("no_hp") or "").strip(),
        "email": (payload.get("email") or "").strip(),
        "alamat": (payload.get("alamat") or "").strip(),
        "perusahaan": (payload.get("perusahaan") or "").strip(),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    result = suplier().insert_one(doc)
    created = serialize_doc(suplier().find_one({"_id": result.inserted_id}))
    if created:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "create", "suplier", str(result.inserted_id),
            f"Membuat suplier {created.get('nama', '')}")
    _get_cache().invalidate("suplier_list:")
    return created


def update_suplier(suplier_id: str, payload: dict) -> Optional[dict]:
    oid = parse_object_id(suplier_id)
    if oid is None:
        return None
    update: dict = {"updated_at": utcnow()}
    for field in ("nama", "no_hp", "email", "alamat", "perusahaan"):
        if field in payload:
            value = (payload.get(field) or "").strip()
            if field == "nama" and not value:
                raise ValueError("Nama suplier wajib diisi.")
            update[field] = value
    suplier().update_one({"_id": oid}, {"$set": update})
    updated = serialize_doc(suplier().find_one({"_id": oid}))
    if updated:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "update", "suplier", suplier_id,
            f"Memperbarui suplier {updated.get('nama', '')}")
    _get_cache().invalidate("suplier_list:")
    return updated


def delete_suplier(suplier_id: str) -> bool:
    oid = parse_object_id(suplier_id)
    if oid is None:
        return False
    from models import barang_masuk

    if barang_masuk().count_documents({"suplier_id": oid}) > 0:
        raise ValueError("Suplier masih memiliki transaksi barang masuk.")
    current = suplier().find_one({"_id": oid})
    if current:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "delete", "suplier", suplier_id,
            f"Menghapus suplier {current.get('nama', '')}")
    result = suplier().delete_one({"_id": oid})
    _get_cache().invalidate("suplier_list:")
    return result.deleted_count > 0
