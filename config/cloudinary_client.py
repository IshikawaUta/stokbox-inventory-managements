"""Konfigurasi dan klien Cloudinary untuk penyimpanan media."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional, Tuple

import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

_DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def reload_env() -> None:
    """Reload .env file (berguna setelah user edit .env tanpa restart)."""
    global _configured_for
    load_dotenv(dotenv_path=str(_DOTENV_PATH), override=True)
    _configured_for = None  # force re-configure on next call


def _env(name: str, default: str = "") -> str:
    """Baca env var setiap saat (tidak di-cache), agar update .env langsung生效."""
    return os.getenv(name, default) or default


_CLOUDINARY_URL_RE = re.compile(
    r"^cloudinary://(?P<key>[^:]+):(?P<secret>[^@]+)@(?P<cloud>[^/?#]+)"
)


def _parse_cloudinary_url(url: str) -> Optional[Tuple[str, str, str]]:
    """Parse CLOUDINARY_URL=cloudinary://KEY:SECRET@CLOUD_NAME menjadi triple."""
    if not url:
        return None
    m = _CLOUDINARY_URL_RE.match(url.strip())
    if not m:
        return None
    return m.group("cloud"), m.group("key"), m.group("secret")


def _current_creds() -> Tuple[str, str, str]:
    """Ambil kredensial: prioritas CLOUDINARY_URL, fallback ke 3 env var terpisah."""
    parsed = _parse_cloudinary_url(_env("CLOUDINARY_URL"))
    if parsed:
        return parsed
    return (
        _env("CLOUDINARY_CLOUD_NAME"),
        _env("CLOUDINARY_API_KEY"),
        _env("CLOUDINARY_API_SECRET"),
    )


_configured_for: Optional[tuple] = None


def configure() -> None:
    """Inisialisasi konfigurasi Cloudinary. Re-init kalau env berubah."""
    global _configured_for
    creds = _current_creds()
    cloud_name, api_key, api_secret = creds
    if not (cloud_name and api_key and api_secret):
        _configured_for = None
        return

    if _configured_for == creds:
        return

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    _configured_for = creds


def is_configured() -> bool:
    """Cek apakah Cloudinary env sudah diisi."""
    cloud_name, api_key, api_secret = _current_creds()
    return bool(cloud_name and api_key and api_secret)


def get_folder() -> str:
    return _env("CLOUDINARY_FOLDER", "inventaris")


def upload_image(
    file_obj: Any,
    *,
    folder: Optional[str] = None,
    public_id: Optional[str] = None,
    overwrite: bool = True,
) -> dict:
    """Upload gambar ke Cloudinary dan kembalikan respons."""
    return upload_file(file_obj, folder=folder, public_id=public_id, overwrite=overwrite, resource_type="image")


def upload_file(
    file_obj: Any,
    *,
    folder: Optional[str] = None,
    public_id: Optional[str] = None,
    overwrite: bool = True,
    resource_type: str = "image",
) -> dict:
    """Upload file (image/raw) ke Cloudinary dan kembalikan respons."""
    configure()
    options: dict = {
        "folder": folder or get_folder(),
        "overwrite": overwrite,
        "resource_type": resource_type,
    }
    if public_id:
        options["public_id"] = public_id
    return cloudinary.uploader.upload(file_obj, **options)


def delete_image(public_id: str) -> dict:
    """Hapus gambar di Cloudinary berdasarkan public_id."""
    configure()
    return cloudinary.uploader.destroy(public_id, resource_type="image")
