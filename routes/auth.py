"""Route autentikasi (login & logout)."""
from __future__ import annotations

import asyncio

from fenrir import Blueprint, Body, HTTPBadRequest, HTTPUnauthorized, session

from services import auth_service

auth_bp = Blueprint("auth", url_prefix="/auth")


@auth_bp.post("/login")
async def login(payload: dict = Body(...)):
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    if not email or not password:
        raise HTTPBadRequest("Email dan password wajib diisi.")
    user = await asyncio.to_thread(auth_service.authenticate, email, password)
    if user is None:
        raise HTTPUnauthorized("Email atau password salah.")
    if not user.get("is_active", True):
        raise HTTPUnauthorized("Akun tidak aktif.")
    session["isLoggedIn"] = True
    session["userId"] = str(user["_id"])
    session["userName"] = user.get("name", "")
    session["userEmail"] = user.get("email", "")
    session["userRole"] = user.get("role", "staff")
    photo = user.get("photo")
    photo_url = photo if isinstance(photo, str) else (photo or {}).get("url")
    session["userPhoto"] = photo_url
    return {
        "message": "Login berhasil.",
        "user": {
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "photo": photo_url,
        },
    }


@auth_bp.post("/logout")
async def logout():
    session.clear()
    return {"message": "Logout berhasil."}


@auth_bp.get("/logout")
async def logout_get():
    session.clear()
    from fenrir import redirect
    return redirect("/login")


@auth_bp.get("/me")
async def me():
    if not session.get("isLoggedIn"):
        raise HTTPUnauthorized("Sesi telah berakhir.")
    return {
        "id": session.get("userId"),
        "name": session.get("userName"),
        "email": session.get("userEmail"),
        "role": session.get("userRole"),
        "photo": session.get("userPhoto"),
    }
