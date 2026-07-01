"""Utilitas umum: serialisasi ObjectId, formatter, dsb."""
from __future__ import annotations

from datetime import datetime, date, timezone
from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId


def parse_object_id(value: Any) -> Optional[ObjectId]:
    """Parse string ke ObjectId. Mengembalikan None jika tidak valid."""
    if value is None or value == "":
        return None
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        return None


def serialize_doc(doc: Optional[dict]) -> Optional[dict]:
    """Konversi ObjectId dan datetime menjadi string agar JSON-serializable."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]

    result: dict = {}
    for key, value in doc.items():
        if key == "_id":
            result["id"] = str(value)
            continue
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, date):
            result[key] = value.isoformat()
        elif isinstance(value, list):
            result[key] = [serialize_doc(v) if isinstance(v, dict) else v for v in value]
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        else:
            result[key] = value

    if "_id" in doc and "id" not in result:
        result["id"] = str(doc["_id"])
    return result


def serialize_docs(docs: list[dict]) -> list[dict]:
    """Serialize list of documents."""
    return [serialize_doc(d) for d in docs]


def utcnow() -> datetime:
    """Kembalikan datetime UTC sekarang (naive, untuk kompatibilitas MongoDB)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(value: Any) -> Optional[date]:
    """Parse string ISO (YYYY-MM-DD) ke date. None jika kosong/invalid."""
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None
