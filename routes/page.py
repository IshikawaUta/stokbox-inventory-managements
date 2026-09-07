"""Route halaman (HTML) menggunakan Jinja2 templates."""
from __future__ import annotations

import asyncio

from fenrir import Blueprint, render_template, session, redirect

from services import auth_service, barang_service, setting_service
from utils.decorators import login_required

page_bp = Blueprint("page", url_prefix="")


async def _common_context(active_menu: str = "", page_title: str | None = None,
                    page_subtitle: str | None = None) -> dict:
    user_role = session.get("userRole", "")
    settings = await asyncio.to_thread(setting_service.get_settings)
    logo = settings.get("logo")
    favicon = settings.get("favicon")
    low_stock_count = 0
    low_stock_items = []
    if user_role == "admin":
        try:
            low_stock_items = await asyncio.to_thread(barang_service.list_low_stock, limit=20)
            low_stock_count = len(low_stock_items)
        except Exception:
            low_stock_items = []
            low_stock_count = 0

    return {
        "active_menu": active_menu,
        "page_title": page_title or "Dashboard",
        "page_subtitle": page_subtitle,
        "app_name": settings.get("nama_aplikasi") or "InventarisKu",
        "app_tagline": settings.get("tagline") or "Admin Panel",
        "app_logo": logo if (logo and logo.startswith("/")) else None,
        "app_favicon": favicon if (favicon and (favicon.startswith("/") or favicon.startswith("http"))) else "/favicon.ico",
        "user_id": session.get("userId", ""),
        "user_name": session.get("userName", ""),
        "user_email": session.get("userEmail", ""),
        "user_role": user_role,
        "user_role_label": "Administrator" if user_role == "admin" else (user_role.capitalize() if user_role else "-"),
        "user_photo": session.get("userPhoto"),
        "is_admin": user_role == "admin",
        "is_inventory_role": user_role in ("admin", "staff"),
        "low_stock_count": low_stock_count,
        "low_stock_items": low_stock_items,
    }


# ============== ROOT & AUTH ==============

@page_bp.get("/")
async def home():
    if not session.get("isLoggedIn"):
        return redirect("/login")
    return redirect("/dashboard")


@page_bp.get("/login")
async def login_page():
    if session.get("isLoggedIn"):
        return redirect("/dashboard")
    ctx = await _common_context("login")
    ctx["app_logo"] = ctx["app_logo"] or "/logo.png"
    return render_template("login.html", **ctx)


# ============== DASHBOARD ==============

@page_bp.get("/dashboard")
@login_required
async def dashboard():
    ctx = await _common_context("dashboard", "Dashboard", "Ringkasan inventaris barang Anda")
    ctx["stats"] = await asyncio.to_thread(barang_service.dashboard_stats)
    ctx["recent_masuk"] = await asyncio.to_thread(barang_service.recent_barang_masuk, 5)
    ctx["recent_keluar"] = await asyncio.to_thread(barang_service.recent_barang_keluar, 5)
    ctx["recent_penyesuaian"] = await asyncio.to_thread(barang_service.recent_penyesuaian, 5)
    ctx["top_outgoing"] = await asyncio.to_thread(barang_service.top_outgoing_items, 5)
    ctx["trend_data"] = await asyncio.to_thread(barang_service.monthly_trend)
    ctx["kategori_dist"] = await asyncio.to_thread(barang_service.kategori_distribution)
    return render_template("dashboard.html", **ctx)


# ============== BARANG (literal routes dulu) ==============

@page_bp.get("/barang")
@login_required
async def barang_page():
    return render_template("barang/index.html", **(await _common_context("barang", "Data Barang", "Kelola data barang inventaris")))


@page_bp.get("/barang/create")
@login_required
async def barang_create_page():
    ctx = await _common_context("barang", "Tambah Barang")
    ctx["mode"] = "create"
    ctx["barang_id"] = ""
    return render_template("barang/form.html", **ctx)


@page_bp.get("/barang/import")
@login_required
async def barang_import_page():
    return render_template("barang/import.html", **(await _common_context("barang", "Import Barang", "Import data barang dari Excel")))


@page_bp.get("/barang/print-qrcode")
@login_required
async def barang_print_qrcode_page():
    from models import barang
    from utils.helpers import serialize_docs
    items = serialize_docs(await asyncio.to_thread(lambda: list(barang().find().limit(50))))
    return render_template(
        "barang/print_qrcode.html",
        items=items,
        **(await _common_context("barang", "Cetak QR Code", "Pilih barang lalu cetak QR Code")),
    )


@page_bp.get("/barang/print-barcode")
@login_required
async def barang_print_barcode_page():
    from models import barang
    from utils.helpers import serialize_docs
    items = serialize_docs(await asyncio.to_thread(lambda: list(barang().find().limit(50))))
    return render_template(
        "barang/print_barcode.html",
        items=items,
        **(await _common_context("barang", "Cetak Barcode", "Pilih barang lalu cetak barcode")),
    )


# Param routes setelah literal
@page_bp.get("/barang/<barang_id>")
@login_required
async def barang_detail_page(barang_id: str):
    ctx = await _common_context("barang", "Detail Barang")
    ctx["barang_id"] = barang_id
    return render_template("barang/detail.html", **ctx)


@page_bp.get("/barang/<barang_id>/edit")
@login_required
async def barang_edit_page(barang_id: str):
    ctx = await _common_context("barang", "Edit Barang")
    ctx["barang_id"] = barang_id
    ctx["mode"] = "edit"
    return render_template("barang/form.html", **ctx)


# ============== KATEGORI & SUPLIER ==============

@page_bp.get("/kategori")
@login_required
async def kategori_page():
    return render_template("kategori/index.html", **(await _common_context("kategori", "Data Kategori", "Kelola kategori barang")))


@page_bp.get("/suplier")
@login_required
async def suplier_page():
    return render_template("suplier/index.html", **(await _common_context("suplier", "Data Suplier", "Kelola data suplier / pemasok")))


# ============== BARANG MASUK ==============

@page_bp.get("/barang-masuk")
@login_required
async def barang_masuk_page():
    return render_template("barang_masuk/index.html", **(await _common_context("barang-masuk", "Barang Masuk", "Catatan transaksi barang masuk")))


@page_bp.get("/barang-masuk/create")
@login_required
async def barang_masuk_create_page():
    ctx = await _common_context("barang-masuk", "Tambah Barang Masuk")
    ctx["mode"] = "create"
    ctx["transaksi_id"] = ""
    return render_template("barang_masuk/create.html", **ctx)


@page_bp.get("/barang-masuk/<transaksi_id>/edit")
@login_required
async def barang_masuk_edit_page(transaksi_id: str):
    ctx = await _common_context("barang-masuk", "Edit Barang Masuk")
    ctx["transaksi_id"] = transaksi_id
    ctx["mode"] = "edit"
    return render_template("barang_masuk/create.html", **ctx)


@page_bp.get("/barang-masuk/<transaksi_id>")
@login_required
async def barang_masuk_detail_page(transaksi_id: str):
    ctx = await _common_context("barang-masuk", "Detail Barang Masuk")
    ctx["transaksi_id"] = transaksi_id
    return render_template("barang_masuk/detail.html", **ctx)


# ============== BARANG KELUAR ==============

@page_bp.get("/barang-keluar")
@login_required
async def barang_keluar_page():
    return render_template("barang_keluar/index.html", **(await _common_context("barang-keluar", "Barang Keluar", "Catatan transaksi barang keluar")))


@page_bp.get("/barang-keluar/create")
@login_required
async def barang_keluar_create_page():
    ctx = await _common_context("barang-keluar", "Tambah Barang Keluar")
    ctx["mode"] = "create"
    ctx["transaksi_id"] = ""
    return render_template("barang_keluar/create.html", **ctx)


@page_bp.get("/barang-keluar/<transaksi_id>/edit")
@login_required
async def barang_keluar_edit_page(transaksi_id: str):
    ctx = await _common_context("barang-keluar", "Edit Barang Keluar")
    ctx["transaksi_id"] = transaksi_id
    ctx["mode"] = "edit"
    return render_template("barang_keluar/create.html", **ctx)


@page_bp.get("/barang-keluar/<transaksi_id>")
@login_required
async def barang_keluar_detail_page(transaksi_id: str):
    ctx = await _common_context("barang-keluar", "Detail Barang Keluar")
    ctx["transaksi_id"] = transaksi_id
    return render_template("barang_keluar/detail.html", **ctx)


# ============== STOK PENYESUAIAN ==============

@page_bp.get("/stok-penyesuaian")
@login_required
async def stok_penyesuaian_page():
    return render_template("stok_penyesuaian/index.html", **(await _common_context("stok-penyesuaian", "Penyesuaian Stok", "Koreksi stok opname")))


@page_bp.get("/stok-penyesuaian/create")
@login_required
async def stok_penyesuaian_create_page():
    return render_template("stok_penyesuaian/create.html", **(await _common_context("stok-penyesuaian", "Tambah Penyesuaian Stok")))


@page_bp.get("/stok-penyesuaian/<penyesuaian_id>")
@login_required
async def stok_penyesuaian_detail_page(penyesuaian_id: str):
    ctx = await _common_context("stok-penyesuaian", "Detail Penyesuaian Stok")
    ctx["penyesuaian_id"] = penyesuaian_id
    return render_template("stok_penyesuaian/detail.html", **ctx)


# ============== USER & PROFILE ==============

@page_bp.get("/user")
@login_required
async def user_page():
    return render_template("user/index.html", **(await _common_context("users", "Data User", "Kelola pengguna aplikasi")))


@page_bp.get("/profile")
@login_required
async def profile_page():
    return render_template("user/profile.html", **(await _common_context("profile", "Profil Saya")))


@page_bp.get("/change-password")
@login_required
async def change_password_page():
    return render_template("user/change_password.html", **(await _common_context("change-password", "Ganti Password")))


# ============== SETTING ==============

@page_bp.get("/setting")
@login_required
async def setting_page():
    return render_template("setting/index.html", **(await _common_context("setting", "Pengaturan Aplikasi", "Konfigurasi identitas dan preferensi aplikasi")))


# ============== LAPORAN ==============

@page_bp.get("/laporan/stok")
@login_required
async def laporan_stok_page():
    return render_template("laporan/stok.html", **(await _common_context("laporan-stok", "Laporan Stok Barang", "Rekap stok seluruh barang")))


@page_bp.get("/laporan/barang-masuk")
@login_required
async def laporan_barang_masuk_page():
    return render_template("laporan/barang_masuk.html", **(await _common_context("laporan-barang-masuk", "Laporan Barang Masuk", "Rekap transaksi barang masuk")))


@page_bp.get("/laporan/barang-keluar")
@login_required
async def laporan_barang_keluar_page():
    return render_template("laporan/barang_keluar.html", **(await _common_context("laporan-barang-keluar", "Laporan Barang Keluar", "Rekap transaksi barang keluar")))


@page_bp.get("/laporan/penyesuaian-stok")
@login_required
async def laporan_penyesuaian_page():
    return render_template("laporan/penyesuaian_stok.html", **(await _common_context("laporan-penyesuaian-stok", "Laporan Penyesuaian Stok", "Rekap penyesuaian / koreksi stok")))


# ============== AKTIVITAS ==============

@page_bp.get("/aktivitas")
@login_required
async def aktivitas_page():
    return render_template("aktivitas/index.html", **(await _common_context("aktivitas", "Catatan Aktivitas", "Audit trail aktivitas pengguna")))


# ============== BACKUP ==============

@page_bp.get("/backup")
@login_required
async def backup_page():
    return render_template("backup/index.html", **(await _common_context("backup", "Backup Database", "Unduh salinan basis data")))
