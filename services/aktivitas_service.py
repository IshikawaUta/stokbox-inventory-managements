"""Service untuk mencatat aktivitas / audit trail."""
from __future__ import annotations

from models import aktivitas as aktivitas_col
from utils.helpers import serialize_doc, serialize_docs, utcnow


def log(
    user_id: str,
    user_name: str,
    user_role: str,
    aksi: str,
    entitas: str,
    entitas_id: str,
    deskripsi: str,
    detail: dict | None = None,
    ip_address: str = "",
) -> None:
    aktivitas_col().insert_one({
        "user_id": user_id,
        "user_name": user_name,
        "user_role": user_role,
        "aksi": aksi,
        "entitas": entitas,
        "entitas_id": entitas_id,
        "deskripsi": deskripsi,
        "detail": detail,
        "ip_address": ip_address,
        "created_at": utcnow().isoformat(),
    })


def list_aktivitas(
    keyword: str = "",
    entitas: str = "",
    aksi: str = "",
    page: int = 1,
    per_page: int = 25,
) -> dict:
    query: dict = {}
    if keyword:
        query["$or"] = [
            {"user_name": {"$regex": keyword, "$options": "i"}},
            {"deskripsi": {"$regex": keyword, "$options": "i"}},
        ]
    if entitas:
        query["entitas"] = entitas
    if aksi:
        query["aksi"] = aksi

    col = aktivitas_col()
    total = col.count_documents(query)
    skip = (max(page, 1) - 1) * per_page
    cursor = col.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    items = serialize_docs(list(cursor))

    return {
        "data": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(-(-total // per_page), 1) if total else 1,
    }


def get_aktivitas(id: str) -> dict | None:
    from utils.helpers import parse_object_id
    oid = parse_object_id(id)
    if oid is None:
        return None
    doc = aktivitas_col().find_one({"_id": oid})
    return serialize_doc(doc) if doc else None
