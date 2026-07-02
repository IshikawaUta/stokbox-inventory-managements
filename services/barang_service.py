"""Service untuk barang / item inventaris."""
from __future__ import annotations

from typing import Optional

from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from models import barang, barang_keluar, barang_masuk, kategori
from services import cloudinary_service
from utils.helpers import (
    parse_object_id,
    serialize_doc,
    serialize_docs,
    utcnow,
)


def list_barang(keyword: str = "", kategori_id: str = "", stok_filter: str = "") -> list[dict]:
    query: dict = {}
    if keyword:
        query["$or"] = [
            {"kode_barang": {"$regex": keyword, "$options": "i"}},
            {"nama_barang": {"$regex": keyword, "$options": "i"}},
        ]
    if kategori_id:
        oid = parse_object_id(kategori_id)
        if oid is not None:
            query["kategori_id"] = oid

    if stok_filter == "hampir-habis":
        all_items = list(barang().find(query).sort("created_at", DESCENDING))
        items = [d for d in all_items if 0 < int(d.get("stok", 0)) <= int(d.get("stok_minimum", 0))]
    elif stok_filter == "habis":
        query["stok"] = 0
        items = list(barang().find(query).sort("created_at", DESCENDING))
    elif stok_filter == "tersedia":
        all_items = list(barang().find(query).sort("created_at", DESCENDING))
        items = [d for d in all_items if int(d.get("stok", 0)) > int(d.get("stok_minimum", 0))]
    else:
        items = list(barang().find(query).sort("created_at", DESCENDING))

    kategori_map = {d["_id"]: d for d in kategori().find({})}
    for item in items:
        kid = item.get("kategori_id")
        if kid and kid in kategori_map:
            item["nama_kategori"] = kategori_map[kid].get("nama_kategori")
            item["icon_kategori"] = kategori_map[kid].get("icon_kategori")
        else:
            item["nama_kategori"] = None
            item["icon_kategori"] = None
    return serialize_docs(items)


def get_barang(barang_id: str) -> Optional[dict]:
    oid = parse_object_id(barang_id)
    if oid is None:
        return None
    pipeline = [
        {"$match": {"_id": oid}},
        {
            "$lookup": {
                "from": "kategori",
                "localField": "kategori_id",
                "foreignField": "_id",
                "as": "kategori_info",
            }
        },
        {"$unwind": {"path": "$kategori_info", "preserveNullAndEmptyArrays": True}},
        {
            "$addFields": {
                "nama_kategori": "$kategori_info.nama_kategori",
                "icon_kategori": "$kategori_info.icon_kategori",
            }
        },
        {"$project": {"kategori_info": 0}},
    ]
    docs = list(barang().aggregate(pipeline))
    return serialize_doc(docs[0]) if docs else None


def _validate_common(payload: dict, *, is_update: bool, current: Optional[dict] = None) -> dict:
    kode = (payload.get("kode_barang") or "").strip().upper()
    if not kode:
        raise ValueError("Kode barang wajib diisi.")
    nama = (payload.get("nama_barang") or "").strip()
    if not nama:
        raise ValueError("Nama barang wajib diisi.")
    satuan = (payload.get("satuan") or "").strip()
    if not satuan:
        raise ValueError("Satuan wajib diisi.")
    kategori_id = parse_object_id(payload.get("kategori_id"))
    if kategori_id is None or not kategori().find_one({"_id": kategori_id}):
        raise ValueError("Kategori tidak valid.")

    stok_awal = int(payload.get("stok_awal", 0) or 0)
    stok_minimum = int(payload.get("stok_minimum", 0) or 0)
    if stok_awal < 0 or stok_minimum < 0:
        raise ValueError("Stok tidak boleh negatif.")

    return {
        "kode_barang": kode,
        "nama_barang": nama,
        "deskripsi_barang": (payload.get("deskripsi_barang") or "").strip() or None,
        "kategori_id": kategori_id,
        "satuan": satuan,
        "lokasi_barang": (payload.get("lokasi_barang") or "").strip() or None,
        "stok_awal": stok_awal,
        "stok_minimum": stok_minimum,
        "qrcode": kode,
        "barcode": kode,
    }


def create_barang(payload: dict) -> dict:
    data = _validate_common(payload, is_update=False)
    data["stok"] = data["stok_awal"]
    data["foto"] = payload.get("foto")
    data["created_at"] = utcnow()
    data["updated_at"] = utcnow()
    try:
        result = barang().insert_one(data)
    except DuplicateKeyError:
        raise ValueError("Kode barang sudah digunakan.") from None
    created = get_barang(str(result.inserted_id)) or {}
    if created:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "create", "barang", str(result.inserted_id),
            f"Membuat barang {created.get('kode_barang', '')} - {created.get('nama_barang', '')}")
        stok = created.get("stok", 0)
        catat_riwayat_stok(str(result.inserted_id), created.get("kode_barang", ""),
            created.get("nama_barang", ""), 0, stok, stok, "edit_stok_awal",
            keterangan="Stok awal")
    return created


def update_barang(barang_id: str, payload: dict) -> Optional[dict]:
    oid = parse_object_id(barang_id)
    if oid is None:
        return None
    current = barang().find_one({"_id": oid})
    if not current:
        return None

    data = _validate_common(payload, is_update=True, current=current)
    old_photo = current.get("foto")
    new_photo = payload.get("foto", old_photo)

    has_transactions = (
        barang_masuk().count_documents({"detail.barang_id": oid}) > 0
        or barang_keluar().count_documents({"detail.barang_id": oid}) > 0
    )

    update: dict = {
        "kode_barang": data["kode_barang"],
        "nama_barang": data["nama_barang"],
        "deskripsi_barang": data["deskripsi_barang"],
        "kategori_id": data["kategori_id"],
        "satuan": data["satuan"],
        "lokasi_barang": data["lokasi_barang"],
        "stok_awal": data["stok_awal"],
        "stok_minimum": data["stok_minimum"],
        "qrcode": data["qrcode"],
        "barcode": data["barcode"],
        "foto": new_photo,
        "updated_at": utcnow(),
    }

    if not has_transactions:
        current_stok = int(current.get("stok", 0))
        delta = data["stok_awal"] - int(current.get("stok_awal", 0))
        update["stok"] = max(0, current_stok + delta)
    try:
        barang().update_one({"_id": oid}, {"$set": update})
    except DuplicateKeyError:
        raise ValueError("Kode barang sudah digunakan.") from None

    if new_photo != old_photo and old_photo:
        public_id = (old_photo or {}).get("public_id")
        if public_id:
            cloudinary_service.remove_photo(public_id)

    from fenrir import session
    from services import aktivitas_service
    userId = session.get("userId", "")
    userName = session.get("userName", "")
    userRole = session.get("userRole", "")
    aktivitas_service.log(userId, userName, userRole, "update", "barang", barang_id,
        f"Memperbarui barang {current.get('kode_barang', '')}")

    if not has_transactions:
        old_stok = int(current.get("stok", 0))
        new_stok = max(0, old_stok + data["stok_awal"] - int(current.get("stok_awal", 0)))
        if old_stok != new_stok:
            catat_riwayat_stok(barang_id, current.get("kode_barang", ""), current.get("nama_barang", ""),
                old_stok, new_stok, new_stok - old_stok, "edit_stok_awal",
                keterangan="Perubahan stok awal")

    return get_barang(barang_id)


def delete_barang(barang_id: str) -> bool:
    oid = parse_object_id(barang_id)
    if oid is None:
        return False
    has_masuk = barang_masuk().count_documents({"detail.barang_id": oid}) > 0
    has_keluar = barang_keluar().count_documents({"detail.barang_id": oid}) > 0
    if has_masuk or has_keluar:
        raise ValueError(
            "Barang tidak dapat dihapus karena sudah memiliki transaksi."
        )
    current = barang().find_one({"_id": oid})
    if current and current.get("foto"):
        public_id = (current["foto"] or {}).get("public_id")
        if public_id:
            cloudinary_service.remove_photo(public_id)
    if current:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "delete", "barang", barang_id,
            f"Menghapus barang {current.get('kode_barang', '')} - {current.get('nama_barang', '')}")
    result = barang().delete_one({"_id": oid})
    return result.deleted_count > 0


def check_kode(kode: str, exclude_id: str = "") -> bool:
    """Mengembalikan True jika kode tersedia."""
    kode = (kode or "").strip().upper()
    if not kode:
        return False
    query: dict = {"kode_barang": kode}
    exclude_oid = parse_object_id(exclude_id)
    if exclude_oid is not None:
        query["_id"] = {"$ne": exclude_oid}
    return barang().count_documents(query) == 0


def dashboard_stats() -> dict:
    """Ringkasan statistik untuk dashboard - lengkap seperti PHP."""
    from datetime import date, timedelta
    from models import (
        suplier, barang_masuk, barang_keluar, stok_penyesuaian, users
    )

    total_barang = barang().count_documents({})
    total_kategori = kategori().count_documents({})
    total_suplier = suplier().count_documents({})
    total_masuk_all = barang_masuk().count_documents({})
    total_keluar_all = barang_keluar().count_documents({})

    today = date.today()
    this_month_start = today.replace(day=1).isoformat()
    next_month_start = (today.replace(day=1) + timedelta(days=32)).replace(day=1).isoformat()
    month_query = {"$gte": this_month_start, "$lt": next_month_start}

    barang_masuk_bulan = barang_masuk().count_documents({"tanggal_masuk": month_query})
    barang_keluar_bulan = barang_keluar().count_documents({"tanggal_keluar": month_query})
    penyesuaian_bulan = stok_penyesuaian().count_documents({"tanggal_penyesuaian": month_query})

    # Qty totals via aggregation (server-side, hemat memori)
    masuk_qty_result = list(barang_masuk().aggregate([
        {"$match": {"tanggal_masuk": month_query}},
        {"$unwind": "$detail"},
        {"$group": {"_id": None, "total": {"$sum": {"$toInt": "$detail.jumlah"}}}},
    ]))
    masuk_qty = masuk_qty_result[0]["total"] if masuk_qty_result else 0

    keluar_qty_result = list(barang_keluar().aggregate([
        {"$match": {"tanggal_keluar": month_query}},
        {"$unwind": "$detail"},
        {"$group": {"_id": None, "total": {"$sum": {"$toInt": "$detail.jumlah"}}}},
    ]))
    keluar_qty = keluar_qty_result[0]["total"] if keluar_qty_result else 0

    penyesuaian_qty_result = list(stok_penyesuaian().aggregate([
        {"$match": {"tanggal_penyesuaian": month_query}},
        {"$group": {"_id": None, "total": {"$sum": {"$toInt": "$selisih"}}}},
    ]))
    penyesuaian_qty = penyesuaian_qty_result[0]["total"] if penyesuaian_qty_result else 0

    # Stok hampir habis & kosong via aggregation
    stok_stats = list(barang().aggregate([
        {"$project": {"stok": 1, "stok_minimum": 1}},
        {"$group": {
            "_id": None,
            "stok_kosong": {"$sum": {"$cond": [{"$eq": ["$stok", 0]}, 1, 0]}},
            "hampir_habis": {"$sum": {"$cond": [
                {"$and": [{"$gt": ["$stok", 0]}, {"$lte": ["$stok", "$stok_minimum"]}]},
                1, 0
            ]}},
        }},
    ]))
    stok_kosong = stok_stats[0]["stok_kosong"] if stok_stats else 0
    hampir_habis = stok_stats[0]["hampir_habis"] if stok_stats else 0

    # User stats
    total_user = users().count_documents({})
    total_staff = users().count_documents({"role": "staff"})

    # Total nilai stok via aggregation
    nilai_result = list(barang().aggregate([
        {"$project": {"stok": 1, "harga_satuan": 1}},
        {"$group": {
            "_id": None,
            "total_stok": {"$sum": "$stok"},
            "total_nilai": {"$sum": {"$multiply": ["$stok", {"$ifNull": ["$harga_satuan", 0]}]}},
        }},
    ]))
    total_stok = nilai_result[0]["total_stok"] if nilai_result else 0
    total_nilai = nilai_result[0]["total_nilai"] if nilai_result else 0

    return {
        "total_barang": total_barang,
        "total_stok": total_stok,
        "total_kategori": total_kategori,
        "total_suplier": total_suplier,
        "total_user": total_user,
        "total_staff": total_staff,
        "total_masuk": total_masuk_all,
        "total_keluar": total_keluar_all,
        "hampir_habis": hampir_habis,
        "stok_kosong": stok_kosong,
        "barang_masuk_bulan_ini": barang_masuk_bulan,
        "qty_barang_masuk_bulan_ini": masuk_qty,
        "barang_keluar_bulan_ini": barang_keluar_bulan,
        "qty_barang_keluar_bulan_ini": keluar_qty,
        "penyesuaian_bulan_ini": penyesuaian_bulan,
        "qty_penyesuaian_bulan_ini": penyesuaian_qty,
        "total_nilai": total_nilai,
    }


def list_low_stock(limit: int = 20) -> list[dict]:
    """Daftar barang dengan stok <= stok_minimum."""
    items = []
    for doc in barang().find({}).sort([("stok", 1), ("nama_barang", 1)]):
        if int(doc.get("stok", 0)) <= int(doc.get("stok_minimum", 0)):
            items.append(serialize_doc(doc))
        if len(items) >= limit:
            break
    return items


def recent_barang_masuk(limit: int = 5) -> list[dict]:
    """Transaksi barang masuk terbaru + ringkasan item/jumlah."""
    from models import barang_masuk as bm_col, suplier
    suplier_map = {s["_id"]: s for s in suplier().find({})}
    items = []
    for d in bm_col().find({}).sort("created_at", DESCENDING).limit(limit):
        detail = d.get("detail", [])
        total_jumlah = sum(int(x.get("jumlah", 0)) for x in detail)
        sid = d.get("suplier_id")
        items.append({
            "id": str(d["_id"]),
            "no_transaksi": d.get("no_transaksi"),
            "tanggal_masuk": d.get("tanggal_masuk"),
            "nama_suplier": suplier_map.get(sid, {}).get("nama") if sid else None,
            "total_jumlah": total_jumlah,
            "item_count": len(detail),
        })
    return items


def recent_barang_keluar(limit: int = 5) -> list[dict]:
    """Transaksi barang keluar terbaru + ringkasan item/jumlah."""
    from models import barang_keluar as bk_col
    items = []
    for d in bk_col().find({}).sort("created_at", DESCENDING).limit(limit):
        detail = d.get("detail", [])
        total_jumlah = sum(int(x.get("jumlah", 0)) for x in detail)
        items.append({
            "id": str(d["_id"]),
            "no_transaksi": d.get("no_transaksi"),
            "tanggal_keluar": d.get("tanggal_keluar"),
            "tujuan_penerima": d.get("tujuan_penerima"),
            "total_jumlah": total_jumlah,
            "item_count": len(detail),
        })
    return items


def monthly_trend(months: int = 6) -> dict:
    """Data tren N bulan terakhir: masuk vs keluar."""
    from datetime import date, timedelta
    from collections import defaultdict
    from models import barang_masuk as bm_col, barang_keluar as bk_col
    today = date.today()
    labels, masuk_map, keluar_map = [], defaultdict(int), defaultdict(int)
    for i in range(months - 1, -1, -1):
        m = (today.replace(day=1) - timedelta(days=30 * i))
        labels.append(m.strftime("%b %y"))
        masuk_map[m.strftime("%Y-%m")] = 0
        keluar_map[m.strftime("%Y-%m")] = 0

    # Aggregation pipeline: parse tanggal string ke $year-$month, lalu group
    bm_pipeline = [
        {"$addFields": {"_parsed": {"$dateFromString": {
            "dateString": "$tanggal_masuk",
            "onError": None,
            "onNull": None,
        }}}},
        {"$match": {"_parsed": {"$ne": None}}},
        {"$addFields": {"_key": {"$dateToString": {"format": "%Y-%m", "date": "$_parsed"}}}},
        {"$match": {"_key": {"$in": list(masuk_map.keys())}}},
        {"$unwind": "$detail"},
        {"$group": {"_id": "$_key", "total": {"$sum": {"$toInt": "$detail.jumlah"}}}},
    ]
    for r in bm_col().aggregate(bm_pipeline):
        masuk_map[r["_id"]] = r["total"]

    bk_pipeline = [
        {"$addFields": {"_parsed": {"$dateFromString": {
            "dateString": "$tanggal_keluar",
            "onError": None,
            "onNull": None,
        }}}},
        {"$match": {"_parsed": {"$ne": None}}},
        {"$addFields": {"_key": {"$dateToString": {"format": "%Y-%m", "date": "$_parsed"}}}},
        {"$match": {"_key": {"$in": list(keluar_map.keys())}}},
        {"$unwind": "$detail"},
        {"$group": {"_id": "$_key", "total": {"$sum": {"$toInt": "$detail.jumlah"}}}},
    ]
    for r in bk_col().aggregate(bk_pipeline):
        keluar_map[r["_id"]] = r["total"]

    keys = sorted(masuk_map.keys())
    return {
        "labels": [labels[i] for i, k in enumerate(keys)],
        "masuk": [masuk_map[k] for k in keys],
        "keluar": [keluar_map[k] for k in keys],
    }


def kategori_distribution() -> dict:
    """Distribusi total stok per kategori (top 6 + Lainnya)."""
    pipeline = [
        {"$lookup": {
            "from": "kategori",
            "localField": "kategori_id",
            "foreignField": "_id",
            "as": "kat_info",
        }},
        {"$unwind": {"path": "$kat_info", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": {"$ifNull": ["$kat_info.nama_kategori", "Tanpa Kategori"]},
            "total": {"$sum": "$stok"},
        }},
        {"$sort": {"total": -1}},
    ]
    results = list(barang().aggregate(pipeline))
    if not results:
        return {"labels": [], "values": []}
    top = results[:6]
    if len(results) > 6:
        rest = sum(r["total"] for r in results[6:])
        top.append({"_id": "Lainnya", "total": rest})
    return {
        "labels": [r["_id"] for r in top],
        "values": [r["total"] for r in top],
    }


def list_lookup(keyword: str = "", limit: int = 50) -> list[dict]:
    """Lookup barang untuk modal pilih barang pada transaksi."""
    q: dict = {}
    if keyword:
        q["$or"] = [
            {"kode_barang": {"$regex": keyword, "$options": "i"}},
            {"nama_barang": {"$regex": keyword, "$options": "i"}},
        ]
    items = list(barang().find(q, {"kode_barang": 1, "nama_barang": 1, "satuan": 1, "stok": 1}).limit(limit))
    return serialize_docs(items)


def import_xlsx(headers: list[str], rows: list[tuple]) -> dict:
    """Import data barang dari XLSX. Headers adalah baris header; rows adalah baris data.
    Mengembalikan {success_count, failed_count, errors:[{row, message}]}.
    """
    expected = ["kode_barang", "nama_barang", "nama_kategori", "satuan",
                "stok_awal", "stok_minimum", "lokasi_barang", "deskripsi_barang"]
    if not all(h in headers for h in ["kode_barang", "nama_barang", "nama_kategori", "satuan"]):
        raise ValueError("Header minimal: kode_barang, nama_barang, nama_kategori, satuan")

    idx = {h: headers.index(h) if h in headers else -1 for h in expected}
    success = 0
    errors = []
    kat_cache = {k["nama_kategori"].lower(): k for k in kategori().find({})}

    for r_idx, row in enumerate(rows, start=2):
        try:
            if not row or all(c is None or str(c).strip() == "" for c in row):
                continue
            kode = str(row[idx["kode_barang"]] or "").strip().upper()
            nama = str(row[idx["nama_barang"]] or "").strip()
            nama_kat = str(row[idx["nama_kategori"]] or "").strip()
            satuan = str(row[idx["satuan"]] or "").strip()
            if not kode or not nama or not nama_kat or not satuan:
                raise ValueError("Field wajib kosong")
            kat = kat_cache.get(nama_kat.lower())
            if not kat:
                kat_id = kategori().insert_one({
                    "nama_kategori": nama_kat,
                    "icon_kategori": "bi-box-seam",
                    "created_at": utcnow(),
                    "updated_at": utcnow(),
                }).inserted_id
                kat = {"_id": kat_id, "nama_kategori": nama_kat}
                kat_cache[nama_kat.lower()] = kat
            else:
                kat_id = kat["_id"]
            stok_awal = int(row[idx["stok_awal"]] or 0) if idx["stok_awal"] >= 0 else 0
            stok_min = int(row[idx["stok_minimum"]] or 0) if idx["stok_minimum"] >= 0 else 0
            lokasi = str(row[idx["lokasi_barang"]] or "").strip() if idx["lokasi_barang"] >= 0 else ""
            deskripsi = str(row[idx["deskripsi_barang"]] or "").strip() if idx["deskripsi_barang"] >= 0 else ""
            doc = {
                "kode_barang": kode, "nama_barang": nama, "kategori_id": kat_id,
                "satuan": satuan, "stok_awal": stok_awal, "stok_minimum": stok_min,
                "stok": stok_awal, "lokasi_barang": lokasi or None,
                "deskripsi_barang": deskripsi or None,
                "qrcode": kode, "barcode": kode,
                "created_at": utcnow(), "updated_at": utcnow(),
            }
            barang().insert_one(doc)
            success += 1
        except Exception as exc:
            errors.append({"row": r_idx, "message": str(exc)})

    return {"success_count": success, "failed_count": len(errors), "errors": errors}


def top_outgoing_items(limit: int = 5) -> dict:
    """Top barang paling sering keluar (qty). Return labels, values, table."""
    from models import barang_keluar as bk_col
    pipeline = [
        {"$unwind": "$detail"},
        {"$group": {
            "_id": {"$concat": [
                {"$ifNull": ["$detail.kode_barang", ""]}, " - ", {"$ifNull": ["$detail.nama_barang", ""]}
            ]},
            "total": {"$sum": {"$toInt": "$detail.jumlah"}},
        }},
        {"$sort": {"total": -1}},
        {"$limit": limit},
    ]
    results = list(bk_col().aggregate(pipeline))
    if not results:
        return {"labels": [], "values": [], "table": []}
    labels = [r["_id"] for r in results]
    values = [r["total"] for r in results]
    table = [{"label": r["_id"], "value": r["total"]} for r in results]
    return {"labels": labels, "values": values, "table": table}


def catat_riwayat_stok(
    barang_id: str,
    kode_barang: str,
    nama_barang: str,
    stok_sebelum: int,
    stok_sesudah: int,
    perubahan: int,
    tipe: str,
    ref_id: str = "",
    ref_no: str = "",
    keterangan: str = "",
) -> None:
    from models import riwayat_stok as rs_col
    rs_col().insert_one({
        "barang_id": barang_id,
        "kode_barang": kode_barang,
        "nama_barang": nama_barang,
        "stok_sebelum": stok_sebelum,
        "stok_sesudah": stok_sesudah,
        "perubahan": perubahan,
        "tipe": tipe,
        "ref_id": ref_id,
        "ref_no": ref_no,
        "keterangan": keterangan,
        "created_at": utcnow().isoformat(),
    })


def get_riwayat_stok(
    barang_id: str,
    keyword: str = "",
    tipe: str = "",
    page: int = 1,
    per_page: int = 25,
) -> dict:
    from models import riwayat_stok as rs_col
    oid = parse_object_id(barang_id)
    if oid is None:
        return {"data": [], "total": 0, "page": 1, "per_page": per_page, "total_pages": 1}

    query: dict = {"barang_id": str(oid)}
    if keyword:
        query["$or"] = [
            {"ref_no": {"$regex": keyword, "$options": "i"}},
            {"keterangan": {"$regex": keyword, "$options": "i"}},
        ]
    if tipe:
        query["tipe"] = tipe

    col = rs_col()
    total = col.count_documents(query)
    skip = (max(page, 1) - 1) * per_page
    docs = list(col.find(query).sort("created_at", -1).skip(skip).limit(per_page))
    total_pages = max(-(-total // per_page), 1) if total else 1

    return {
        "data": serialize_docs(docs),
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def recent_penyesuaian(limit: int = 5) -> list[dict]:
    """Penyesuaian stok terbaru."""
    from models import stok_penyesuaian as sp_col
    items = []
    for d in sp_col().find({}).sort("created_at", DESCENDING).limit(limit):
        items.append({
            "id": str(d["_id"]),
            "no_penyesuaian": d.get("no_penyesuaian"),
            "tanggal_penyesuaian": d.get("tanggal_penyesuaian"),
            "kode_barang": d.get("kode_barang"),
            "nama_barang": d.get("nama_barang"),
            "stok_sistem": d.get("stok_sistem"),
            "stok_fisik": d.get("stok_fisik"),
            "selisih": d.get("selisih"),
            "jenis": d.get("jenis"),
            "status": d.get("status"),
            "alasan": d.get("alasan"),
        })
    return items

