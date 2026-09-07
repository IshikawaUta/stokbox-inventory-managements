"""API stok penyesuaian."""
from __future__ import annotations

import asyncio

from fenrir import Body, Blueprint, Depends, HTTPBadRequest, HTTPNotFound, Query, session

from config.schemas import PaginationParams
from services import stok_penyesuaian_service
from utils.decorators import api_login_required, role_required

sp_bp = Blueprint("api-stok-penyesuaian", url_prefix="/api/stok-penyesuaian")


@sp_bp.get("")
@api_login_required
async def index(
    barang_id: str = Query(""),
    status: str = Query(""),
    pagination: PaginationParams = Depends(PaginationParams),
):
    return {
        "data": await asyncio.to_thread(
            stok_penyesuaian_service.list_penyesuaian,
            barang_id=barang_id, status=status
        )
    }


@sp_bp.get("/generate-number")
@api_login_required
async def generate_number():
    from utils.security import generate_no_transaksi
    return {"no_penyesuaian": await asyncio.to_thread(generate_no_transaksi, "SP")}


@sp_bp.get("/<penyesuaian_id>")
@api_login_required
async def show(penyesuaian_id: str):
    doc = await asyncio.to_thread(stok_penyesuaian_service.get_penyesuaian, penyesuaian_id)
    if not doc:
        raise HTTPNotFound("Penyesuaian tidak ditemukan.")
    return doc


@sp_bp.post("")
@role_required("admin", "staff")
async def create(payload: dict = Body(...)):
    payload = dict(payload or {})
    if not payload.get("user_id") and session.get("userId"):
        payload["user_id"] = session.get("userId")
    try:
        return await asyncio.to_thread(stok_penyesuaian_service.create_penyesuaian, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))


@sp_bp.post("/<penyesuaian_id>/batal")
@role_required("admin", "staff")
async def batal(penyesuaian_id: str, payload: dict = Body(...)):
    payload = dict(payload or {})
    if not payload.get("user_id") and session.get("userId"):
        payload["user_id"] = session.get("userId")
    try:
        result = await asyncio.to_thread(stok_penyesuaian_service.batal_penyesuaian, penyesuaian_id, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not result:
        raise HTTPNotFound("Penyesuaian tidak ditemukan.")
    return result


@sp_bp.delete("/<penyesuaian_id>")
@role_required("admin")
async def destroy(penyesuaian_id: str):
    try:
        deleted = await asyncio.to_thread(stok_penyesuaian_service.delete_penyesuaian, penyesuaian_id)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not deleted:
        raise HTTPNotFound("Penyesuaian tidak ditemukan.")
    return {"message": "Penyesuaian berhasil dihapus."}
