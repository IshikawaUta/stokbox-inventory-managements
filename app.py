"""Aplikasi InventarisKu - Sistem Manajemen Inventaris berbasis Fenrir v4.1.2 + MongoDB Atlas + Cloudinary."""
from __future__ import annotations

import hashlib
import json as _json
import os
import sys
from datetime import date, datetime

from dotenv import load_dotenv
load_dotenv()

from fenrir import (
    Fenrir, HTTPException, JSONResponse, render_template, send_file, send_from_directory,
    CORSMiddleware, GZipMiddleware, RequestIDMiddleware, RateLimitMiddleware, session,
)
from fenrir.middleware import CSRFMiddleware, SecurityHeadersMiddleware
from fenrir.templating import Jinja2Renderer
from fenrir.features import init_fenrir_monitoring
from fenrir.hooks import HookRegistry

from config.database import ping as mongo_ping
from config.cache import cache
from config.queue import get_queue, get_worker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Fenrir(
    title="InventarisKu API",
    version="4.1.2",
    template_folder="templates",
    dev_mode=os.getenv("FENRIR_DEV_MODE", "0") == "1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Secret Key Validation ──────────────────────────────────────────────
_secret_key = os.getenv("APP_SECRET_KEY")
if not _secret_key or _secret_key == "inventaris-dev-secret-change-me":
    _is_production = os.getenv("APP_ENV", "development") == "production"
    if _is_production:
        raise RuntimeError(
            "APP_SECRET_KEY wajib diatur ke random string yang aman di production! "
            "Atur pada file .env"
        )
    _secret_key = _secret_key or "inventaris-dev-secret-change-me"

# ── In-Memory Cache (sync, untuk service layer) ────────────────────────
# cache di-import dari config.cache

# ── Security + Performance Middleware (Fenrir) ─────────────────────────
_origins = os.getenv("CORS_ORIGINS", "*").split(",")
_is_production = os.getenv("APP_ENV", "development") == "production"
app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_credentials=True)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=500, window_seconds=60)
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)
if _is_production:
    app.add_middleware(CSRFMiddleware, secret_key=_secret_key)
app.add_middleware(SecurityHeadersMiddleware, csp="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; img-src 'self' data: https:; connect-src 'self' ws: wss: https://cdn.jsdelivr.net; frame-src 'none'; object-src 'none'; base-uri 'self'")


# ── ETag Middleware ──────────────────────────────────────────────────────
class ETagMiddleware:
    """Middleware yang menambahkan ETag header untuk caching dinamis."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        if method != "GET":
            await self.app(scope, receive, send)
            return

        # Buffer response untuk generate ETag
        response_start = None
        response_body = b""

        async def send_buffered(message):
            nonlocal response_start, response_body
            if message["type"] == "http.response.start":
                response_start = message
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
                if not message.get("more_body", False):
                    # Kirim response dengan ETag
                    if response_start and response_body:
                        content_type = ""
                        for k, v in response_start.get("headers", []):
                            if k == b"content-type":
                                content_type = v.decode("latin-1")
                                break

                        if "application/json" in content_type:
                            etag = hashlib.md5(response_body).hexdigest()
                            headers = list(response_start.get("headers", []))
                            headers.append((b"etag", f'"{etag}"'.encode("latin-1")))
                            response_start["headers"] = headers

                            # Cek If-None-Match
                            if_none_match = None
                            for k, v in scope.get("headers", []):
                                if k == b"if-none-match":
                                    if_none_match = v.decode("latin-1").strip('"')
                                    break

                            if if_none_match == etag:
                                # 304 Not Modified
                                await send({
                                    "type": "http.response.start",
                                    "status": 304,
                                    "headers": [(b"etag", f'"{etag}"'.encode("latin-1"))],
                                })
                                await send({"type": "http.response.body", "body": b""})
                                return

                    await send(response_start)
                    await send({"type": "http.response.body", "body": response_body})
            else:
                await send(message)

        await self.app(scope, receive, send_buffered)


app.add_middleware(ETagMiddleware)

# ── Monitoring (Fenrir) ────────────────────────────────────────────────
init_fenrir_monitoring(app)

# ── Hook Registry (Fenrir) — lifecycle hooks ───────────────────────────
hooks = HookRegistry()


@hooks.register("on_request")
async def _log_request_hook(**kwargs):
    """Log setiap request yang masuk."""
    pass


@hooks.register("on_exception")
async def _log_exception_hook(**kwargs):
    """Log exception yang terjadi."""
    pass

hooks.apply(app)


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


app.config["SECRET_KEY"] = _secret_key
_use_https = os.getenv("SESSION_COOKIE_SECURE", "").lower() in ("1", "true")
app.config["SESSION_COOKIE_SECURE"] = _use_https
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ── Signals: Auto Request Logging ──────────────────────────────────────
from fenrir.signals import request_started, request_finished

_request_count = {"total": 0, "errors": 0}


@request_started.connect
async def _on_request_started(sender, **kwargs):
    _request_count["total"] += 1


@request_finished.connect
async def _on_request_finished(sender, **kwargs):
    status = kwargs.get("status_code", 200)
    if status >= 400:
        _request_count["errors"] += 1


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
from routes.websocket import ws_bp
from routes.sse import sse_bp

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
app.register_blueprint(ws_bp)
app.register_blueprint(sse_bp)


@app.get("/health")
async def health():
    """Health check: cek koneksi MongoDB + request stats."""
    q = get_queue()
    return {
        "status": "ok",
        "mongo": "connected" if mongo_ping() else "disconnected",
        "requests_total": _request_count["total"],
        "requests_errors": _request_count["errors"],
        "queue": {
            "pending_jobs": len(q._pending) if hasattr(q, '_pending') else 0,
        },
        "features": {
            "di": True,
            "response_model": True,
            "background_tasks": True,
            "pagination": True,
            "openapi": True,
            "cache": True,
            "hooks": True,
            "signals": True,
            "websocket": True,
            "sse": True,
            "queue_worker": True,
            "csrf": True,
            "security_headers": True,
            "rate_limiting": True,
            "gzip": True,
            "request_id": True,
            "monitoring": True,
        },
    }


async def _error_context(detail: str = "") -> dict:
    """Build minimal context for error pages (cached)."""
    cached = cache.get("error_context")
    if cached is not None:
        return {**cached, "detail": detail}
    from services import setting_service
    settings = setting_service.get_settings()
    logo = settings.get("logo")
    favicon = settings.get("favicon")
    ctx = {
        "app_name": settings.get("nama_aplikasi") or "InventarisKu",
        "app_tagline": settings.get("tagline") or "Admin Panel",
        "app_logo": logo if (logo and logo.startswith("/")) else None,
        "app_favicon": favicon if (favicon and (favicon.startswith("/") or favicon.startswith("http"))) else "/favicon.ico",
        "APP": {
            "name": os.getenv("APP_NAME", "InventarisKu"),
            "version": "4.1.2",
        },
    }
    cache.set("error_context", ctx, ttl=300)
    return {**ctx, "detail": detail}


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
    """Serve file statis dari direktori static/ dengan cache headers."""
    resp = send_from_directory(STATIC_DIR, filepath)
    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".js", ".css"):
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"):
        resp.headers["Cache-Control"] = "public, max-age=86400"
    elif ext in (".woff", ".woff2", ".ttf", ".eot"):
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp


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
