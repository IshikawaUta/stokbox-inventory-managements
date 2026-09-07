"""API transaksi barang masuk."""
from __future__ import annotations

import asyncio

from fenrir import Body, Blueprint, Depends, HTTPBadRequest, HTTPNotFound, Query, session

from config.schemas import PaginationParams
from services import barang_masuk_service
from utils.decorators import api_login_required, role_required

bm_bp = Blueprint("api-barang-masuk", url_prefix="/api/barang-masuk")


@bm_bp.get("")
@api_login_required
async def index(
    keyword: str = Query(""),
    tanggal_awal: str = Query(""),
    tanggal_akhir: str = Query(""),
    suplier_id: str = Query(""),
    pagination: PaginationParams = Depends(PaginationParams),
):
    return {"data": await asyncio.to_thread(
        barang_masuk_service.list_barang_masuk,
        keyword=keyword, tanggal_awal=tanggal_awal, tanggal_akhir=tanggal_akhir, suplier_id=suplier_id
    )}


@bm_bp.get("/generate-number")
@api_login_required
async def generate_number():
    from utils.security import generate_no_transaksi
    return {"no_transaksi": await asyncio.to_thread(generate_no_transaksi, "BM")}


@bm_bp.get("/<transaksi_id>")
@api_login_required
async def show(transaksi_id: str):
    doc = await asyncio.to_thread(barang_masuk_service.get_barang_masuk, transaksi_id)
    if not doc:
        raise HTTPNotFound("Transaksi tidak ditemukan.")
    return doc


@bm_bp.post("")
@role_required("admin", "staff")
async def create(payload: dict = Body(...)):
    payload = dict(payload or {})
    if not payload.get("user_id") and session.get("userId"):
        payload["user_id"] = session.get("userId")
    try:
        return await asyncio.to_thread(barang_masuk_service.create_barang_masuk, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))


@bm_bp.put("/<transaksi_id>")
@role_required("admin", "staff")
async def update(transaksi_id: str, payload: dict = Body(...)):
    payload = dict(payload or {})
    if not payload.get("user_id") and session.get("userId"):
        payload["user_id"] = session.get("userId")
    try:
        result = await asyncio.to_thread(barang_masuk_service.update_barang_masuk, transaksi_id, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not result:
        raise HTTPNotFound("Transaksi tidak ditemukan.")
    return result


@bm_bp.delete("/<transaksi_id>")
@role_required("admin")
async def destroy(transaksi_id: str):
    try:
        deleted = await asyncio.to_thread(barang_masuk_service.delete_barang_masuk, transaksi_id)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not deleted:
        raise HTTPNotFound("Transaksi tidak ditemukan.")
    return {"message": "Transaksi berhasil dihapus."}
