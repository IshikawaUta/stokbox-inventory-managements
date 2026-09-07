"""API manajemen user."""
from __future__ import annotations

import asyncio

from fenrir import Body, Blueprint, File, HTTPBadRequest, HTTPNotFound, UploadFile, session

from services import auth_service
from utils.decorators import api_login_required, role_required

user_bp = Blueprint("api-user", url_prefix="/api/user")


# ---- literal routes dulu, baru parameterized ----

@user_bp.get("")
@api_login_required
@role_required("admin")
async def index():
    return {"data": await asyncio.to_thread(auth_service.list_users)}


@user_bp.post("")
@api_login_required
@role_required("admin")
async def create(payload: dict = Body(...)):
    try:
        return await asyncio.to_thread(auth_service.create_user, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))


@user_bp.put("/profile")
@api_login_required
async def update_profile(payload: dict = Body(...)):
    user_id = session.get("userId")
    if not user_id:
        raise HTTPNotFound("Sesi berakhir.")
    try:
        user = await asyncio.to_thread(auth_service.update_profile, user_id, payload)
        session["userName"] = user.get("name", "")
        session["userEmail"] = user.get("email", "")
        photo = user.get("photo")
        session["userPhoto"] = photo if isinstance(photo, str) else (photo or {}).get("url")
        return user
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))


@user_bp.put("/change-password")
@api_login_required
async def change_password(payload: dict = Body(...)):
    user_id = session.get("userId")
    if not user_id:
        raise HTTPNotFound("Sesi berakhir.")
    try:
        await asyncio.to_thread(auth_service.change_password, user_id, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    return {"message": "Password berhasil diubah."}


@user_bp.post("/profile/photo")
@api_login_required
async def upload_photo(file: UploadFile = File(...)):
    user_id = session.get("userId")
    if not user_id:
        raise HTTPNotFound("Sesi berakhir.")
    if not file or not getattr(file, "filename", None):
        raise HTTPBadRequest("File foto wajib diisi.")
    raw = await file.read()
    user = await asyncio.to_thread(auth_service.upload_photo, user_id, raw, file.filename, file.content_type or "image/jpeg")
    photo = user.get("photo")
    session["userPhoto"] = photo if isinstance(photo, str) else (photo or {}).get("url")
    return user


# ---- parameterized routes ----

@user_bp.get("/<user_id>")
@api_login_required
@role_required("admin")
async def show(user_id: str):
    doc = await asyncio.to_thread(auth_service.get_user, user_id)
    if not doc:
        raise HTTPNotFound("User tidak ditemukan.")
    return doc


@user_bp.put("/<user_id>")
@api_login_required
@role_required("admin")
async def update(user_id: str, payload: dict = Body(...)):
    try:
        result = await asyncio.to_thread(auth_service.update_user, user_id, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not result:
        raise HTTPNotFound("User tidak ditemukan.")
    # update session jika user yg diedit adalah user login
    current_user_id = session.get("userId")
    if current_user_id == user_id:
        session["userName"] = result.get("name", "")
        session["userEmail"] = result.get("email", "")
        session["userRole"] = result.get("role", "staff")
        photo = result.get("photo")
        session["userPhoto"] = photo if isinstance(photo, str) else (photo or {}).get("url")
    return result


@user_bp.delete("/<user_id>")
@api_login_required
@role_required("admin")
async def destroy(user_id: str):
    if not await asyncio.to_thread(auth_service.delete_user, user_id):
        raise HTTPNotFound("User tidak ditemukan.")
    return {"message": "User berhasil dihapus."}


@user_bp.post("/<user_id>/toggle-active")
@api_login_required
@role_required("admin")
async def toggle_active(user_id: str):
    result = await asyncio.to_thread(auth_service.toggle_active, user_id)
    if not result:
        raise HTTPNotFound("User tidak ditemukan.")
    return result
