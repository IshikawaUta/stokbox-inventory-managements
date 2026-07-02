"""API untuk aktivitas / audit trail."""
from __future__ import annotations

from fenrir import Blueprint, Query

from services import aktivitas_service
from utils.decorators import api_login_required

aktivitas_bp = Blueprint("api-aktivitas", url_prefix="/api/aktivitas")


@aktivitas_bp.get("")
@api_login_required
async def list_aktivitas(
    keyword: str = Query(""),
    entitas: str = Query(""),
    aksi: str = Query(""),
    page: int = Query(1),
    per_page: int = Query(25),
):
    per_page = min(per_page, 100)
    return aktivitas_service.list_aktivitas(
        keyword=keyword, entitas=entitas, aksi=aksi,
        page=page, per_page=per_page,
    )
