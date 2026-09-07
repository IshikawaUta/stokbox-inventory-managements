"""API CRUD kategori."""
from __future__ import annotations

import asyncio

from fenrir import Blueprint, Body, Depends, HTTPBadRequest, HTTPNotFound, Query, request

from config.schemas import PaginationParams
from services import kategori_service
from utils.decorators import api_login_required, role_required

kategori_bp = Blueprint("api-kategori", url_prefix="/api/kategori")


def _payload() -> dict:
    try:
        return request.json or {}
    except Exception:
        raise HTTPBadRequest("Body harus berupa JSON valid.")


@kategori_bp.get("")
@api_login_required
async def index(
    keyword: str = Query(""),
    pagination: PaginationParams = Depends(PaginationParams),
):
    return {"data": await asyncio.to_thread(kategori_service.list_kategori, keyword)}


@kategori_bp.get("/<kategori_id>")
@api_login_required
async def show(kategori_id: str):
    doc = await asyncio.to_thread(kategori_service.get_kategori, kategori_id)
    if not doc:
        raise HTTPNotFound("Kategori tidak ditemukan.")
    return doc


@kategori_bp.post("")
@role_required("admin")
async def create(payload: dict = Body(...)):
    try:
        return await asyncio.to_thread(kategori_service.create_kategori, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))


@kategori_bp.put("/<kategori_id>")
@role_required("admin")
async def update(kategori_id: str, payload: dict = Body(...)):
    try:
        result = await asyncio.to_thread(kategori_service.update_kategori, kategori_id, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not result:
        raise HTTPNotFound("Kategori tidak ditemukan.")
    return result


@kategori_bp.delete("/<kategori_id>")
@role_required("admin")
async def destroy(kategori_id: str):
    try:
        deleted = await asyncio.to_thread(kategori_service.delete_kategori, kategori_id)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not deleted:
        raise HTTPNotFound("Kategori tidak ditemukan.")
    return {"message": "Kategori berhasil dihapus."}
