"""Aplikasi InventarisKu - Sistem Manajemen Inventaris berbasis Fenrir v4.1.2 + MongoDB Atlas + Cloudinary."""
from __future__ import annotations

import os
import sys
from datetime import date, datetime

from dotenv import load_dotenv
load_dotenv()

from fenrir import (
    Fenrir, HTTPException, JSONResponse, render_template, send_file, send_from_directory,
    CORSMiddleware, GZipMiddleware, RequestIDMiddleware, RateLimitMiddleware, session,
)
from fenrir.templating import Jinja2Renderer
from fenrir.features import init_fenrir_monitoring

from config.database import ping as mongo_ping

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Fenrir(
    title="InventarisKu API",
    version="4.1.2",
    template_folder="templates",
    dev_mode=os.getenv("FENRIR_DEV_MODE", "0") == "1",
)

# ── Performance Middleware (Fenrir v4.1.2) ─────────────────────────────
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=200, window_seconds=60)
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)


# ── Monitoring (Fenrir v4.1.2) ──────────────────────────────────────────
init_fenrir_monitoring(app)


# ── Template Helpers ─────────────────────────────────────────────────────
def _format_number(value, default="0"):
    try:
        if value is None: return default
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return default


def _format_rupiah(value, default="Rp 0"):
    try:
        if value is None: return default
        return "Rp " + f"{int(value):,}".replace(",", ".")
    except Exception:
        return default


def _format_date(value, default="-"):
    if not value: return default
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    s = str(value)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:len(fmt)+2 if fmt.endswith("%f") else len(fmt)], fmt).strftime("%d/%m/%Y")
        except Exception:
            continue
    return s


def _format_datetime(value, default="-"):
    if not value: return default
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y %H:%M")
    s = str(value)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:len(fmt)+2 if fmt.endswith("%f") else len(fmt)], fmt).strftime("%d/%m/%Y %H:%M")
        except Exception:
            continue
    return s


# Configure renderer dengan globals & filters
_renderer = Jinja2Renderer(os.path.join(BASE_DIR, "templates"))
_renderer.env.globals["APP"] = {
    "name": os.getenv("APP_NAME", "InventarisKu"),
    "version": "4.1.2",
}
_renderer.env.filters["formatNumber"] = _format_number
_renderer.env.filters["formatRupiah"] = _format_rupiah
_renderer.env.filters["formatDate"] = _format_date
_renderer.env.filters["formatDateTime"] = _format_datetime
_renderer.env.globals["formatNumber"] = _format_number
_renderer.env.globals["formatRupiah"] = _format_rupiah
_renderer.env.globals["formatDate"] = _format_date
_renderer.env.globals["formatDateTime"] = _format_datetime


class _SessionProxy:
    """Proxy ke fenrir.session (request-bound)."""

    def get(self, key, default=None):
        return session.get(key, default)

    def __getitem__(self, key):
        return session[key]

    def __contains__(self, key):
        return key in session

    def keys(self):
        return list(session.keys())


_renderer.env.globals["session"] = _SessionProxy()
app.renderer = _renderer


app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY", "inventaris-dev-secret-change-me")
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# Daftarkan seluruh blueprint
from routes.auth import auth_bp
from routes.page import page_bp
from routes.api_kategori import kategori_bp
from routes.api_barang import barang_bp
from routes.api_suplier import suplier_bp
from routes.api_barang_masuk import bm_bp
from routes.api_barang_keluar import bk_bp
from routes.api_stok_penyesuaian import sp_bp
from routes.api_user import user_bp
from routes.api_setting import setting_bp
from routes.api_laporan_backup import laporan_bp, backup_bp, barcode_bp, transaksi_bp
from routes.api_aktivitas import aktivitas_bp

app.register_blueprint(page_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(kategori_bp)
app.register_blueprint(barang_bp)
app.register_blueprint(suplier_bp)
app.register_blueprint(bm_bp)
app.register_blueprint(bk_bp)
app.register_blueprint(sp_bp)
app.register_blueprint(user_bp)
app.register_blueprint(setting_bp)
app.register_blueprint(laporan_bp)
app.register_blueprint(backup_bp)
app.register_blueprint(barcode_bp)
app.register_blueprint(transaksi_bp)
app.register_blueprint(aktivitas_bp)


@app.get("/health")
async def health():
    """Health check: cek koneksi MongoDB."""
    return {
        "status": "ok",
        "mongo": "connected" if mongo_ping() else "disconnected",
    }


async def _error_context(detail: str = "") -> dict:
    """Build minimal context for error pages."""
    from services import setting_service
    settings = setting_service.get_settings()
    logo = settings.get("logo")
    favicon = settings.get("favicon")
    return {
        "detail": detail,
        "app_name": settings.get("nama_aplikasi") or "InventarisKu",
        "app_tagline": settings.get("tagline") or "Admin Panel",
        "app_logo": logo if (logo and logo.startswith("/")) else None,
        "app_favicon": favicon if (favicon and (favicon.startswith("/") or favicon.startswith("http"))) else "/favicon.ico",
        "APP": {
            "name": os.getenv("APP_NAME", "InventarisKu"),
            "version": "4.1.2",
        },
    }


@app.exception(404)
async def page_not_found(request, exc):
    """Handle 404 errors with custom HTML page."""
    ctx = await _error_context(exc.detail)
    return render_template("404.html", **ctx), 404


@app.exception(500)
async def server_error(request, exc):
    """Handle 500 errors with custom HTML page."""
    ctx = await _error_context("Terjadi kesalahan pada server")
    return render_template("500.html", **ctx), 500


@app.exception(HTTPException)
async def handle_http_exception(request, exc: HTTPException):
    detail = getattr(exc, "detail", None) or str(exc)
    status = getattr(exc, "status_code", 500)
    if status in (404, 500):
        ctx = await _error_context(detail)
        return render_template(f"{status}.html", **ctx), status
    return JSONResponse({"error": detail}, status=status)


def _register_multipart_error_handler():
    from python_multipart.exceptions import MultipartParseError
    async def handler(request, exc):
        return JSONResponse(
            {"error": "Upload gagal: format request tidak valid. Silakan refresh halaman dan coba lagi."},
            status=400,
        )
    app.exception_handlers[MultipartParseError] = handler


_register_multipart_error_handler()


@app.get("/static/<path:filepath>")
async def serve_static(filepath: str):
    """Serve file statis dari direktori static/."""
    return send_from_directory(STATIC_DIR, filepath)


@app.get("/logo.png")
async def get_logo():
    return send_file(os.path.join(BASE_DIR, "logo.png"))


@app.get("/favicon.ico")
async def get_favicon():
    return send_file(os.path.join(BASE_DIR, "favicon.ico"))


if __name__ == "__main__":
    print(f"\n  InventarisKu v{app.version} - Fenrir Web Framework")
    print(f"  Python {sys.version.split()[0]}\n")
    app.run()
