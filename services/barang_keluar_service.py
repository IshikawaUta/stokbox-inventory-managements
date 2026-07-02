"""Service untuk transaksi barang keluar."""
from __future__ import annotations

from typing import Optional

from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from models import barang, barang_keluar, users
from utils.helpers import (
    parse_date,
    parse_object_id,
    serialize_doc,
    serialize_docs,
    utcnow,
)
from utils.security import generate_no_transaksi


def list_barang_keluar(
    keyword: str = "",
    tanggal_awal: str = "",
    tanggal_akhir: str = "",
    tujuan: str = "",
) -> list[dict]:
    query: dict = {}
    if keyword:
        query["$or"] = [
            {"no_transaksi": {"$regex": keyword, "$options": "i"}},
            {"tujuan_penerima": {"$regex": keyword, "$options": "i"}},
        ]
    if tanggal_awal or tanggal_akhir:
        rg = {}
        if tanggal_awal:
            d = parse_date(tanggal_awal)
            if d: rg["$gte"] = d.isoformat()
        if tanggal_akhir:
            d = parse_date(tanggal_akhir)
            if d: rg["$lte"] = d.isoformat()
        if rg: query["tanggal_keluar"] = rg
    if tujuan:
        query["tujuan_penerima"] = {"$regex": tujuan, "$options": "i"}

    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "_id",
            "as": "user_info",
        }},
        {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
        {"$addFields": {"nama_user": "$user_info.name"}},
        {"$project": {"user_info": 0}},
        {"$sort": {"tanggal_keluar": -1, "created_at": -1}},
    ]
    docs = list(barang_keluar().aggregate(pipeline))
    for d in docs:
        detail = d.get("detail", [])
        d["item_count"] = len(detail)
        d["total_jumlah"] = sum(int(x.get("jumlah", 0)) for x in detail)
    return serialize_docs(docs)



def get_barang_keluar(transaksi_id: str) -> Optional[dict]:
    oid = parse_object_id(transaksi_id)
    if oid is None:
        return None
    doc = barang_keluar().find_one({"_id": oid})
    if doc:
        user_map = {u["_id"]: u.get("name") for u in users().find({})}
        doc["nama_user"] = user_map.get(doc.get("user_id"))
    return serialize_doc(doc)


def _validate_items(items: list) -> list:
    if not items:
        raise ValueError("Detail barang wajib diisi.")
    result = []
    for item in items:
        barang_id = parse_object_id(item.get("barang_id"))
        if barang_id is None:
            raise ValueError("Barang pada detail tidak valid.")
        jumlah = int(item.get("jumlah", 0) or 0)
        if jumlah <= 0:
            raise ValueError("Jumlah barang harus lebih dari 0.")
        barang_doc = barang().find_one({"_id": barang_id})
        if not barang_doc:
            raise ValueError("Barang tidak ditemukan.")
        if int(barang_doc.get("stok", 0)) < jumlah:
            raise ValueError(
                f"Stok {barang_doc['nama_barang']} tidak cukup (tersisa {barang_doc.get('stok', 0)})."
            )
        result.append({
            "barang_id": barang_id,
            "kode_barang": barang_doc["kode_barang"],
            "nama_barang": barang_doc["nama_barang"],
            "satuan": barang_doc.get("satuan", ""),
            "jumlah": jumlah,
        })
    return result


def create_barang_keluar(payload: dict) -> dict:
    tanggal = parse_date(payload.get("tanggal_keluar"))
    if tanggal is None:
        raise ValueError("Tanggal keluar wajib diisi.")
    tujuan = (payload.get("tujuan_penerima") or "").strip()
    if not tujuan:
        raise ValueError("Tujuan penerima wajib diisi.")
    items = _validate_items(payload.get("items") or payload.get("detail") or [])

    no_transaksi = (payload.get("no_transaksi") or "").strip() or generate_no_transaksi("BK")
    doc = {
        "no_transaksi": no_transaksi,
        "tanggal_keluar": tanggal.isoformat(),
        "tujuan_penerima": tujuan,
        "keperluan": (payload.get("keperluan") or "").strip(),
        "nomor_dokumen": (payload.get("nomor_dokumen") or "").strip(),
        "user_id": parse_object_id(payload.get("user_id")),
        "catatan": (payload.get("catatan") or "").strip(),
        "detail": items,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    try:
        result = barang_keluar().insert_one(doc)
    except DuplicateKeyError:
        raise ValueError("Nomor transaksi sudah digunakan.") from None

    for item in items:
        barang().update_one(
            {"_id": item["barang_id"]},
            {"$inc": {"stok": -item["jumlah"]}, "$set": {"updated_at": utcnow()}},
        )

    result_id = str(result.inserted_id)
    from fenrir import session
    from services import aktivitas_service, barang_service
    userId = session.get("userId", "")
    userName = session.get("userName", "")
    userRole = session.get("userRole", "")
    aktivitas_service.log(userId, userName, userRole, "create", "barang_keluar", result_id,
        f"Membuat transaksi barang keluar {no_transaksi}")

    for item in items:
        barang_doc = barang().find_one({"_id": item["barang_id"]})
        if barang_doc:
            stok_sesudah = int(barang_doc.get("stok", 0))
            stok_sebelum = stok_sesudah + int(item["jumlah"])
            barang_service.catat_riwayat_stok(str(item["barang_id"]), item["kode_barang"], item["nama_barang"],
                stok_sebelum, stok_sesudah, -int(item["jumlah"]), "keluar",
                ref_id=result_id, ref_no=no_transaksi)

    return get_barang_keluar(result_id) or {}


def update_barang_keluar(transaksi_id: str, payload: dict) -> Optional[dict]:
    oid = parse_object_id(transaksi_id)
    if oid is None:
        return None
    current = barang_keluar().find_one({"_id": oid})
    if not current:
        return None

    old_items = current.get("detail", [])
    for item in old_items:
        barang().update_one(
            {"_id": item["barang_id"]},
            {"$inc": {"stok": int(item["jumlah"])}, "$set": {"updated_at": utcnow()}},
        )

    tanggal = parse_date(payload.get("tanggal_keluar"))
    if tanggal is None:
        raise ValueError("Tanggal keluar wajib diisi.")
    tujuan = (payload.get("tujuan_penerima") or "").strip()
    if not tujuan:
        raise ValueError("Tujuan penerima wajib diisi.")
    new_items = _validate_items(payload.get("items") or payload.get("detail") or [])

    update: dict = {
        "tanggal_keluar": tanggal.isoformat(),
        "tujuan_penerima": tujuan,
        "keperluan": (payload.get("keperluan") or "").strip(),
        "nomor_dokumen": (payload.get("nomor_dokumen") or "").strip(),
        "user_id": parse_object_id(payload.get("user_id")),
        "catatan": (payload.get("catatan") or "").strip(),
        "detail": new_items,
        "updated_at": utcnow(),
    }
    barang_keluar().update_one({"_id": oid}, {"$set": update})

    for item in new_items:
        barang().update_one(
            {"_id": item["barang_id"]},
            {"$inc": {"stok": -item["jumlah"]}, "$set": {"updated_at": utcnow()}},
        )

    no_trans = current.get("no_transaksi", "")
    from fenrir import session
    from services import aktivitas_service, barang_service
    userId = session.get("userId", "")
    userName = session.get("userName", "")
    userRole = session.get("userRole", "")
    aktivitas_service.log(userId, userName, userRole, "update", "barang_keluar", transaksi_id,
        f"Memperbarui transaksi barang keluar {no_trans}")

    new_by_barang = {str(it["barang_id"]): it for it in new_items}

    for item in old_items:
        bid = str(item["barang_id"])
        new_item = new_by_barang.get(bid)
        new_jml = int(new_item["jumlah"]) if new_item else 0
        old_jml = int(item["jumlah"])
        doc = barang().find_one({"_id": item["barang_id"]}, {"stok": 1, "kode_barang": 1, "nama_barang": 1})
        if doc:
            final_stok = int(doc["stok"])
            stok_sebelum = final_stok - old_jml + new_jml
            stok_sesudah = final_stok + new_jml
            barang_service.catat_riwayat_stok(bid, doc["kode_barang"], doc["nama_barang"],
                stok_sebelum, stok_sesudah, old_jml, "keluar",
                ref_id=transaksi_id, ref_no=no_trans,
                keterangan="Perubahan barang keluar (reversal)")

    for item in new_items:
        bid = str(item["barang_id"])
        doc = barang().find_one({"_id": item["barang_id"]}, {"stok": 1, "kode_barang": 1, "nama_barang": 1})
        if doc:
            final_stok = int(doc["stok"])
            stok_sebelum = final_stok + int(item["jumlah"])
            barang_service.catat_riwayat_stok(bid, doc["kode_barang"], doc["nama_barang"],
                stok_sebelum, final_stok, -int(item["jumlah"]), "keluar",
                ref_id=transaksi_id, ref_no=no_trans,
                keterangan="Perubahan barang keluar (penambahan)")

    return get_barang_keluar(transaksi_id)


def delete_barang_keluar(transaksi_id: str) -> bool:
    oid = parse_object_id(transaksi_id)
    if oid is None:
        return False
    current = barang_keluar().find_one({"_id": oid})
    if not current:
        return False
    for item in current.get("detail", []):
        barang().update_one(
            {"_id": item["barang_id"]},
            {"$inc": {"stok": int(item["jumlah"])}, "$set": {"updated_at": utcnow()}},
        )
    no_trans = current.get("no_transaksi", "")
    from fenrir import session
    from services import aktivitas_service, barang_service
    userId = session.get("userId", "")
    userName = session.get("userName", "")
    userRole = session.get("userRole", "")
    aktivitas_service.log(userId, userName, userRole, "delete", "barang_keluar", transaksi_id,
        f"Menghapus transaksi barang keluar {no_trans}")

    for item in current.get("detail", []):
        doc = barang().find_one({"_id": item["barang_id"]})
        if doc:
            stok_sesudah = int(doc.get("stok", 0))
            stok_sebelum = stok_sesudah - int(item["jumlah"])
            barang_service.catat_riwayat_stok(str(item["barang_id"]), item["kode_barang"], item["nama_barang"],
                stok_sebelum, stok_sesudah, int(item["jumlah"]), "keluar",
                ref_id=transaksi_id, ref_no=no_trans,
                keterangan="Penghapusan barang keluar")

    result = barang_keluar().delete_one({"_id": oid})
    return result.deleted_count > 0
