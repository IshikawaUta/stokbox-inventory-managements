"""API pengaturan aplikasi."""
from __future__ import annotations

import asyncio

from fenrir import Body, Blueprint, File, HTTPBadRequest, Query, UploadFile

from services import setting_service
from utils.decorators import api_login_required, role_required

setting_bp = Blueprint("api-setting", url_prefix="/api/setting")


@setting_bp.get("")
@api_login_required
async def index():
    return {"data": await asyncio.to_thread(setting_service.get_settings)}


@setting_bp.put("")
@api_login_required
@role_required("admin")
async def update(payload: dict = Body(...)):
    return {"data": await asyncio.to_thread(setting_service.update_settings, payload)}


@setting_bp.post("/upload-asset")
@api_login_required
@role_required("admin")
async def upload_asset(file: UploadFile = File(...), kind: str = Query("logo")):
    if not file or not getattr(file, "filename", None):
        raise HTTPBadRequest("File wajib diisi.")
    if kind not in {"logo", "favicon"}:
        raise HTTPBadRequest("Kind harus 'logo' atau 'favicon'.")
    raw = await file.read()
    return {"data": await asyncio.to_thread(setting_service.upload_asset, kind, raw, file.filename, file.content_type or "image/png")}
