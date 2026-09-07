"""API untuk aktivitas / audit trail."""
from __future__ import annotations

import asyncio

from fenrir import Blueprint, Depends, Query

from config.schemas import PaginationParams
from services import aktivitas_service
from utils.decorators import api_login_required

aktivitas_bp = Blueprint("api-aktivitas", url_prefix="/api/aktivitas")


@aktivitas_bp.get("")
@api_login_required
async def list_aktivitas(
    keyword: str = Query(""),
    entitas: str = Query(""),
    aksi: str = Query(""),
    pagination: PaginationParams = Depends(PaginationParams),
):
    return await asyncio.to_thread(
        aktivitas_service.list_aktivitas,
        keyword=keyword, entitas=entitas, aksi=aksi,
        page=pagination.page, per_page=pagination.per_page,
    )
