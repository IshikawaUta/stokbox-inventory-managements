"""API CRUD suplier."""
from __future__ import annotations

import asyncio

from fenrir import Body, Blueprint, Depends, HTTPBadRequest, HTTPNotFound, Query

from config.schemas import PaginationParams
from services import suplier_service
from utils.decorators import api_login_required, role_required

suplier_bp = Blueprint("api-suplier", url_prefix="/api/suplier")


@suplier_bp.get("")
@api_login_required
async def index(
    keyword: str = Query(""),
    pagination: PaginationParams = Depends(PaginationParams),
):
    return {"data": await asyncio.to_thread(suplier_service.list_suplier, keyword)}


@suplier_bp.get("/<suplier_id>")
@api_login_required
async def show(suplier_id: str):
    doc = await asyncio.to_thread(suplier_service.get_suplier, suplier_id)
    if not doc:
        raise HTTPNotFound("Suplier tidak ditemukan.")
    return doc


@suplier_bp.post("")
@role_required("admin")
async def create(payload: dict = Body(...)):
    try:
        return await asyncio.to_thread(suplier_service.create_suplier, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))


@suplier_bp.put("/<suplier_id>")
@role_required("admin")
async def update(suplier_id: str, payload: dict = Body(...)):
    try:
        result = await asyncio.to_thread(suplier_service.update_suplier, suplier_id, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not result:
        raise HTTPNotFound("Suplier tidak ditemukan.")
    return result


@suplier_bp.delete("/<suplier_id>")
@role_required("admin")
async def destroy(suplier_id: str):
    try:
        deleted = await asyncio.to_thread(suplier_service.delete_suplier, suplier_id)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not deleted:
        raise HTTPNotFound("Suplier tidak ditemukan.")
    return {"message": "Suplier berhasil dihapus."}
