"""API laporan, backup, dan barcode."""

import asyncio
import html as _html
import io
import json
import zipfile
from datetime import datetime

from fenrir import Blueprint, Body, Query, Response, session
from fenrir.background import BackgroundTasks

from services import (
    aktivitas_service,
    barang_masuk_service,
    barang_keluar_service,
    barang_service,
    kategori_service,
    setting_service,
    stok_penyesuaian_service,
    suplier_service,
)
from models import (
    aktivitas, barang, barang_masuk, barang_keluar, kategori,
    riwayat_stok, stok_penyesuaian, suplier, users,
)
from utils.decorators import api_login_required, role_required
from utils.helpers import parse_date, parse_object_id, serialize_doc, serialize_docs

laporan_bp = Blueprint("api-laporan", url_prefix="/api/laporan")
backup_bp = Blueprint("api-backup", url_prefix="/api/backup")
barcode_bp = Blueprint("api-barcode", url_prefix="/api/barcode")
transaksi_bp = Blueprint("api-transaksi", url_prefix="/api/transaksi")


def _esc(val) -> str:
    """Escape HTML untuk mencegah XSS."""
    if val is None:
        return ""
    return _html.escape(str(val))


# ============== LAPORAN LIST ==============

@laporan_bp.get("/stok")
@api_login_required
async def laporan_stok(
    kategori_id: str = Query(""),
    status: str = Query(""),
):
    items = await asyncio.to_thread(barang_service.list_barang, kategori_id=kategori_id)
    if status:
        result = []
        for it in items:
            stok = int(it.get("stok", 0))
            minstok = int(it.get("stok_minimum", 0))
            if status == "habis" and stok == 0:
                result.append(it)
            elif status == "hampir-habis" and 0 < stok <= minstok:
                result.append(it)
            elif status == "tersedia" and stok > minstok:
                result.append(it)
        items = result
    return {"data": items}


@laporan_bp.get("/barang-masuk")
@api_login_required
async def laporan_barang_masuk(
    tanggal_awal: str = Query(""),
    tanggal_akhir: str = Query(""),
    suplier_id: str = Query(""),
):
    items = await asyncio.to_thread(
        barang_masuk_service.list_barang_masuk,
        tanggal_awal=tanggal_awal, tanggal_akhir=tanggal_akhir, suplier_id=suplier_id
    )
    flat = []
    for t in items:
        for d in t.get("detail", []):
            flat.append({
                "tanggal_masuk": t.get("tanggal_masuk"),
                "no_transaksi": t.get("no_transaksi"),
                "nama_suplier": t.get("nama_suplier"),
                "kode_barang": d.get("kode_barang"),
                "nama_barang": d.get("nama_barang"),
                "satuan": d.get("satuan"),
                "jumlah": d.get("jumlah"),
            })
    return {"data": flat}


@laporan_bp.get("/barang-keluar")
@api_login_required
async def laporan_barang_keluar(
    tanggal_awal: str = Query(""),
    tanggal_akhir: str = Query(""),
    tujuan: str = Query(""),
):
    items = await asyncio.to_thread(
        barang_keluar_service.list_barang_keluar,
        tanggal_awal=tanggal_awal, tanggal_akhir=tanggal_akhir, tujuan=tujuan
    )
    flat = []
    for t in items:
        for d in t.get("detail", []):
            flat.append({
                "tanggal_keluar": t.get("tanggal_keluar"),
                "no_transaksi": t.get("no_transaksi"),
                "tujuan_penerima": t.get("tujuan_penerima"),
                "keperluan": t.get("keperluan"),
                "kode_barang": d.get("kode_barang"),
                "nama_barang": d.get("nama_barang"),
                "satuan": d.get("satuan"),
                "jumlah": d.get("jumlah"),
            })
    return {"data": flat}


@laporan_bp.get("/penyesuaian-stok")
@api_login_required
async def laporan_penyesuaian(
    tanggal_awal: str = Query(""),
    tanggal_akhir: str = Query(""),
    jenis: str = Query(""),
    status: str = Query(""),
):
    items = await asyncio.to_thread(stok_penyesuaian_service.list_penyesuaian)
    if tanggal_awal or tanggal_akhir:
        aw = parse_date(tanggal_awal) if tanggal_awal else None
        ak = parse_date(tanggal_akhir) if tanggal_akhir else None
        items = [x for x in items if _date_in_range(x.get("tanggal_penyesuaian"), aw, ak)]
    if jenis:
        items = [x for x in items if x.get("jenis") == jenis]
    if status:
        items = [x for x in items if x.get("status") == status]
    return {"data": items}


def _date_in_range(value, awal, akhir):
    if not value: return False
    if isinstance(value, str):
        try: d = datetime.fromisoformat(value).date()
        except: return False
    else:
        d = value
    if awal and d < awal: return False
    if akhir and d > akhir: return False
    return True


# ============== LAPORAN HTML (print ke PDF) ==============

def _html_response(html: str):
    return Response(body=html, content_type="text/html; charset=utf-8")


async def _settings():
    return await asyncio.to_thread(setting_service.get_settings)


@laporan_bp.get("/stok/print")
@api_login_required
async def laporan_stok_print(background_tasks: BackgroundTasks):
    items = await asyncio.to_thread(barang_service.list_barang)
    s = await _settings()
    rows = "".join(
        f"<tr><td class='mono'>{_esc(it.get('kode_barang',''))}</td>"
        f"<td>{_esc(it.get('nama_barang',''))}</td><td>{_esc(it.get('nama_kategori',''))}</td>"
        f"<td class='r'>{_esc(it.get('stok',0))} {_esc(it.get('satuan',''))}</td>"
        f"<td class='r'>{_esc(it.get('stok_minimum',0))}</td></tr>"
        for it in items
    )
    body = f"<table><thead><tr><th>Kode</th><th>Nama</th><th>Kategori</th><th class='r'>Stok</th><th class='r'>Min</th></tr></thead><tbody>{rows}</tbody></table>"
    background_tasks.add_task(
        aktivitas_service.log,
        session.get("userId", ""),
        session.get("userName", ""),
        session.get("userRole", ""),
        "view", "laporan", "",
        f"Cetak laporan stok: {len(items)} barang",
    )
    return _html_response(_pdf_html_template(s, "Laporan Stok Barang", f"Total {len(items)} barang", body))


@laporan_bp.get("/barang-masuk/print")
@api_login_required
async def laporan_masuk_print(
    background_tasks: BackgroundTasks,
    keyword: str = Query(""),
    tanggal_awal: str = Query(""),
    tanggal_akhir: str = Query(""),
    suplier_id: str = Query(""),
):
    items = await asyncio.to_thread(
        barang_masuk_service.list_barang_masuk,
        keyword=keyword, tanggal_awal=tanggal_awal, tanggal_akhir=tanggal_akhir, suplier_id=suplier_id
    )
    s = await _settings()
    body = ""
    for t in items:
        body += f"<tr class='grp'><td><b>{_esc(t.get('tanggal_masuk'))}</b></td><td class='mono'>{_esc(t.get('no_transaksi'))}</td><td>{_esc(t.get('nama_suplier',''))}</td><td></td><td></td><td></td></tr>"
        for d in t.get("detail", []):
            body += f"<tr><td></td><td class='mono'>{_esc(d.get('kode_barang',''))}</td><td>{_esc(d.get('nama_barang',''))}</td><td>{_esc(d.get('satuan',''))}</td><td class='r'>{_esc(d.get('jumlah',0))}</td><td></td></tr>"
    if not body: body = "<tr><td colspan='6' class='empty'>Belum ada data barang masuk.</td></tr>"
    background_tasks.add_task(
        aktivitas_service.log,
        session.get("userId", ""),
        session.get("userName", ""),
        session.get("userRole", ""),
        "view", "laporan", "",
        f"Cetak laporan barang masuk: {len(items)} transaksi",
    )
    return _html_response(_pdf_html_template(s, "Laporan Barang Masuk", f"Total {len(items)} transaksi", f"<table><thead><tr><th>Tanggal</th><th>Kode</th><th>Nama</th><th>Satuan</th><th class='r'>Jumlah</th><th></th></tr></thead><tbody>{body}</tbody></table>"))


@laporan_bp.get("/barang-keluar/print")
@api_login_required
async def laporan_keluar_print(
    background_tasks: BackgroundTasks,
    keyword: str = Query(""),
    tanggal_awal: str = Query(""),
    tanggal_akhir: str = Query(""),
    tujuan: str = Query(""),
):
    items = await asyncio.to_thread(
        barang_keluar_service.list_barang_keluar,
        keyword=keyword, tanggal_awal=tanggal_awal, tanggal_akhir=tanggal_akhir, tujuan=tujuan
    )
    s = await _settings()
    body = ""
    for t in items:
        body += f"<tr class='grp'><td><b>{_esc(t.get('tanggal_keluar'))}</b></td><td></td><td class='mono'>{_esc(t.get('no_transaksi'))}</td><td>{_esc(t.get('tujuan_penerima',''))}</td><td></td><td></td><td></td></tr>"
        for d in t.get("detail", []):
            body += f"<tr><td></td><td></td><td class='mono'>{_esc(d.get('kode_barang',''))}</td><td>{_esc(d.get('nama_barang',''))}</td><td>{_esc(d.get('satuan',''))}</td><td class='r'>{_esc(d.get('jumlah',0))}</td><td></td></tr>"
    if not body: body = "<tr><td colspan='7' class='empty'>Belum ada data barang keluar.</td></tr>"
    background_tasks.add_task(
        aktivitas_service.log,
        session.get("userId", ""),
        session.get("userName", ""),
        session.get("userRole", ""),
        "view", "laporan", "",
        f"Cetak laporan barang keluar: {len(items)} transaksi",
    )
    return _html_response(_pdf_html_template(s, "Laporan Barang Keluar", f"Total {len(items)} transaksi", f"<table><thead><tr><th>Tanggal</th><th></th><th>Kode</th><th>Nama</th><th>Satuan</th><th class='r'>Jumlah</th><th></th></tr></thead><tbody>{body}</tbody></table>"))


@laporan_bp.get("/penyesuaian-stok/print")
@api_login_required
async def laporan_penyesuaian_print(background_tasks: BackgroundTasks):
    items = await asyncio.to_thread(stok_penyesuaian_service.list_penyesuaian)
    s = await _settings()
    rows = "".join(
        f"<tr><td>{_esc(it.get('tanggal_penyesuaian'))}</td>"
        f"<td class='mono'>{_esc(it.get('no_penyesuaian',''))}</td>"
        f"<td>{_esc(it.get('nama_barang',''))}</td>"
        f"<td class='r'>{_esc(it.get('stok_sistem',0))}</td>"
        f"<td class='r'>{_esc(it.get('stok_fisik',0))}</td>"
        f"<td class='r'>{_esc(it.get('selisih',0))}</td>"
        f"<td>{_esc(it.get('jenis',''))}</td>"
        f"<td>{_esc(it.get('status',''))}</td></tr>"
        for it in items
    )
    if not rows: rows = "<tr><td colspan='8' class='empty'>Belum ada data penyesuaian.</td></tr>"
    background_tasks.add_task(
        aktivitas_service.log,
        session.get("userId", ""),
        session.get("userName", ""),
        session.get("userRole", ""),
        "view", "laporan", "",
        f"Cetak laporan penyesuaian stok: {len(items)} penyesuaian",
    )
    return _html_response(_pdf_html_template(s, "Laporan Penyesuaian Stok", f"Total {len(items)} penyesuaian", f"<table><thead><tr><th>Tanggal</th><th>No</th><th>Barang</th><th class='r'>Sistem</th><th class='r'>Fisik</th><th class='r'>Selisih</th><th>Jenis</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>"))


def _pdf_html_template(settings, title, subtitle, table):
    company = settings.get("nama_perusahaan") or settings.get("nama_aplikasi") or "Aplikasi Inventaris"
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
  body {{ font-family: 'Inter', Arial, sans-serif; font-size: 12px; color: #101828; margin: 28px; }}
  h1 {{ font-size: 18px; margin: 0; }}
  .meta {{ color: #667085; margin: 2px 0 16px; }}
  .head {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #101828; padding-bottom: 10px; margin-bottom: 16px; }}
  .right {{ text-align: right; font-size: 11px; color: #667085; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #f7f9fc; text-align: left; padding: 8px; border-bottom: 1px solid #e4e7ec; font-size: 11px; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #e4e7ec; }}
  .r {{ text-align: right; }}
  .mono {{ font-family: ui-monospace, monospace; font-size: 11px; }}
  .grp td {{ background: #f8fafc; font-weight: 600; }}
  .empty {{ text-align: center; color: #98a2b3; padding: 30px; }}
  @media print {{ body {{ margin: 14mm; }} .no-print {{ display: none; }} }}
  .no-print {{ margin: 12px 0; }}
</style></head>
<body>
<div class="no-print">
  <button onclick="window.print()" style="padding:6px 14px;background:#2563eb;color:#fff;border:0;border-radius:4px;cursor:pointer">Cetak / Print</button>
  <a href="/barang" onclick="if(history.length>1){{event.preventDefault();history.back()}}" style="margin-left:8px">Kembali</a>
</div>
<div class="head">
  <div>
    <h1>{company}</h1>
    <div class="meta">{title}</div>
  </div>
  <div class="right">
    <div>Tanggal cetak: {today}</div>
    <div>{subtitle}</div>
  </div>
</div>
{table}
<div style="margin-top:30px; display:flex; justify-content:space-between; font-size:11px;">
  <div style="text-align:center; width:200px;">Penerima<br><br><br><br>( _________________ )</div>
  <div style="text-align:center; width:200px;">Pengirim<br><br><br><br>( _________________ )</div>
</div>
</body></html>"""


# ============== TRANSAKSI HTML PRINT ==============

@transaksi_bp.get("/barang-masuk/<transaksi_id>/print")
@api_login_required
async def transaksi_masuk_print(transaksi_id: str):
    t = await asyncio.to_thread(barang_masuk_service.get_barang_masuk, transaksi_id)
    if not t:
        return Response(body="<h1>Transaksi tidak ditemukan</h1>", content_type="text/html", status=404)
    s = await _settings()
    return _html_response(_render_transaksi_html("masuk", t, s))


@transaksi_bp.get("/barang-keluar/<transaksi_id>/print")
@api_login_required
async def transaksi_keluar_print(transaksi_id: str):
    t = await asyncio.to_thread(barang_keluar_service.get_barang_keluar, transaksi_id)
    if not t:
        return Response(body="<h1>Transaksi tidak ditemukan</h1>", content_type="text/html", status=404)
    s = await _settings()
    return _html_response(_render_transaksi_html("keluar", t, s))


def _render_transaksi_html(kind, t, s):
    company = _esc(s.get("nama_perusahaan") or s.get("nama_aplikasi") or "Aplikasi Inventaris")
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    if kind == "masuk":
        title = "Bukti Barang Masuk"
        info_rows = f"""
            <tr><th>No. Transaksi</th><td class='mono'>{_esc(t.get('no_transaksi',''))}</td></tr>
            <tr><th>Tanggal</th><td>{_esc(t.get('tanggal_masuk'))}</td></tr>
            <tr><th>Suplier</th><td>{_esc(t.get('nama_suplier','-'))}</td></tr>
            <tr><th>Nomor Dokumen</th><td>{_esc(t.get('nomor_dokumen','-'))}</td></tr>
        """
    else:
        title = "Bukti Barang Keluar"
        info_rows = f"""
            <tr><th>No. Transaksi</th><td class='mono'>{_esc(t.get('no_transaksi',''))}</td></tr>
            <tr><th>Tanggal</th><td>{_esc(t.get('tanggal_keluar'))}</td></tr>
            <tr><th>Tujuan</th><td>{_esc(t.get('tujuan_penerima','-'))}</td></tr>
            <tr><th>Keperluan</th><td>{_esc(t.get('keperluan','-'))}</td></tr>
        """
    rows = "".join(
        f"<tr><td>{i+1}</td><td class='mono'>{_esc(d.get('kode_barang',''))}</td>"
        f"<td>{_esc(d.get('nama_barang',''))}</td><td>{_esc(d.get('satuan',''))}</td>"
        f"<td class='r'>{_esc(d.get('jumlah',0))}</td></tr>"
        for i, d in enumerate(t.get("detail", []))
    )
    if not rows: rows = "<tr><td colspan='5' class='empty'>Tidak ada item.</td></tr>"
    table = f"<table><thead><tr><th>#</th><th>Kode</th><th>Nama</th><th>Satuan</th><th class='r'>Jumlah</th></tr></thead><tbody>{rows}</tbody></table>"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{_esc(title)}</title>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 12px; color: #101828; margin: 28px; }}
  .head {{ border-bottom: 2px solid #101828; padding-bottom: 8px; margin-bottom: 16px; display:flex; justify-content:space-between; align-items:flex-end; }}
  h1 {{ margin: 0; font-size: 18px; }}
  .meta {{ color: #667085; font-size: 12px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
  th, td {{ padding: 6px 8px; border-bottom: 1px solid #e4e7ec; text-align: left; }}
  th {{ background: #f7f9fc; font-size: 11px; }}
  .r {{ text-align: right; }}
  .mono {{ font-family: ui-monospace, monospace; }}
  .info {{ width: 100%; margin-bottom: 12px; }}
  .info th {{ width: 130px; text-align: left; background: transparent; border: 0; padding: 4px 8px; }}
  .info td {{ border: 0; padding: 4px 8px; }}
  .right {{ text-align: right; font-size: 11px; color: #667085; }}
  .empty {{ text-align: center; color: #98a2b3; padding: 20px; }}
  @media print {{ body {{ margin: 14mm; }} .no-print {{ display: none; }} }}
  .no-print {{ margin: 12px 0; }}
</style></head>
<body>
<div class="no-print">
  <button onclick="window.print()" style="padding:6px 14px;background:#2563eb;color:#fff;border:0;border-radius:4px;cursor:pointer">Cetak</button>
  <a href="/barang" onclick="if(history.length>1){{event.preventDefault();history.back()}}" style="margin-left:8px">Kembali</a>
</div>
<div class="head">
  <div>
    <h1>{company}</h1>
    <div class="meta">{_esc(title)}</div>
  </div>
  <div class="right">Tanggal cetak: {today}</div>
</div>
<table class="info">{info_rows}<tr><th>Catatan</th><td>{_esc(t.get('catatan','-'))}</td></tr></table>
{table}
<div style="margin-top:30px; display:flex; justify-content:space-between; font-size:11px;">
  <div style="text-align:center; width:200px;">Penerima<br><br><br><br>( _________________ )</div>
  <div style="text-align:center; width:200px;">Pengirim<br><br><br><br>( _________________ )</div>
</div>
</body></html>"""


@backup_bp.post("/restore")
@role_required("admin")
async def backup_restore(payload: dict = Body(...)):
    data = payload.get("data", {})
    if not data:
        return {"error": "Data kosong"},  400

    # Whitelist koleksi yang diizinkan
    ALLOWED_COLLECTIONS = {"kategori", "suplier", "barang", "barang_masuk", "barang_keluar"}
    # Whitelist fields per koleksi
    ALLOWED_FIELDS = {
        "kategori": {"_id", "nama_kategori", "icon_kategori", "created_at", "updated_at"},
        "suplier": {"_id", "nama", "no_hp", "email", "alamat", "perusahaan", "created_at", "updated_at"},
        "barang": {"_id", "kode_barang", "nama_barang", "deskripsi_barang", "kategori_id", "satuan",
                    "lokasi_barang", "stok_awal", "stok_minimum", "stok", "harga_satuan",
                    "qrcode", "barcode", "foto", "created_at", "updated_at"},
        "barang_masuk": {"_id", "no_transaksi", "tanggal_masuk", "suplier_id", "nomor_dokumen",
                         "user_id", "catatan", "detail", "created_at", "updated_at"},
        "barang_keluar": {"_id", "no_transaksi", "tanggal_keluar", "tujuan_penerima", "keperluan",
                          "nomor_dokumen", "user_id", "catatan", "detail", "created_at", "updated_at"},
    }

    collection_map = {
        "kategori": kategori,
        "suplier": suplier,
        "barang": barang,
        "barang_masuk": barang_masuk,
        "barang_keluar": barang_keluar,
    }
    counts = {}
    for key, col_fn in collection_map.items():
        if key not in ALLOWED_COLLECTIONS:
            continue
        docs = data.get(key, [])
        if not docs:
            counts[key] = 0
            continue
        col = col_fn()
        existing_ids = set()
        for d in await asyncio.to_thread(lambda: list(col.find({}, {"_id": 1}))):
            existing_ids.add(str(d["_id"]))
        inserted = 0
        allowed = ALLOWED_FIELDS.get(key, set())
        for doc in docs:
            doc_id = str(doc.get("_id", ""))
            if doc_id and doc_id in existing_ids:
                continue
            # Sanitize: hanya ambil field yang diizinkan
            sanitized = {k: v for k, v in doc.items() if k in allowed}
            await asyncio.to_thread(col.insert_one, sanitized)
            inserted += 1
        counts[key] = inserted

    total = sum(counts.values())
    userId = session.get("userId", "")
    userName = session.get("userName", "")
    userRole = session.get("userRole", "")
    await asyncio.to_thread(
        aktivitas_service.log,
        userId, userName, userRole,
        "import", "backup", "",
        f"Restore database: {total} dokumen dari {len(data)} koleksi",
        detail={"counts": counts},
    )

    return {"message": f"Restore berhasil: {total} dokumen baru", "counts": counts}


# ============== BARCODE / QRCODE ==============

@barcode_bp.get("/barang/<barang_id>/qrcode")
@api_login_required
async def barang_qrcode(barang_id: str):
    """Return QR Code PNG image untuk barang."""
    from models import barang
    oid = parse_object_id(barang_id)
    if oid is None:
        return Response(body="Invalid id", content_type="text/plain", status=400)
    doc = await asyncio.to_thread(lambda: barang().find_one({"_id": oid}))
    if not doc:
        return Response(body="Not found", content_type="text/plain", status=404)
    import qrcode
    payload = json.dumps({
        "id": str(doc["_id"]),
        "kode": doc.get("kode_barang"),
        "nama": doc.get("nama_barang"),
    })
    def _make_qr():
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#101828", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    img_bytes = await asyncio.to_thread(_make_qr)
    return Response(body=img_bytes, content_type="image/png")


@barcode_bp.get("/barang/<barang_id>/barcode")
@api_login_required
async def barang_barcode(barang_id: str):
    """Return Code-128 barcode PNG image untuk barang."""
    from models import barang
    oid = parse_object_id(barang_id)
    if oid is None:
        return Response(body="Invalid id", content_type="text/plain", status=400)
    doc = await asyncio.to_thread(lambda: barang().find_one({"_id": oid}))
    if not doc:
        return Response(body="Not found", content_type="text/plain", status=404)
    import barcode
    from barcode.writer import ImageWriter
    def _make_barcode():
        code128 = barcode.get("code128", doc.get("kode_barang", str(doc["_id"])), writer=ImageWriter())
        buf = io.BytesIO()
        code128.write(buf, options={"write_text": True, "font_size": 12, "text_distance": 4, "module_height": 12.0, "module_width": 0.4})
        return buf.getvalue()
    img_bytes = await asyncio.to_thread(_make_barcode)
    return Response(body=img_bytes, content_type="image/png")


@barcode_bp.get("/barang/print-qrcode")
@api_login_required
async def barang_print_qrcode(ids: str = Query("")):
    """Print QR code untuk banyak barang."""
    from models import barang
    id_list = [x for x in ids.split(",") if x]
    oids = []
    for x in id_list:
        oid = parse_object_id(x)
        if oid is not None: oids.append(oid)
    def _fetch_docs():
        if not oids:
            return list(barang().find({}).limit(20))
        return list(barang().find({"_id": {"$in": oids}}).limit(20))
    docs = await asyncio.to_thread(_fetch_docs)
    import base64
    import qrcode
    def _make_cards():
        cards = ""
        for d in docs:
            payload = json.dumps({"id": str(d["_id"]), "kode": d.get("kode_barang"), "nama": d.get("nama_barang")})
            img = qrcode.make(payload, box_size=6, border=1)
            b = io.BytesIO(); img.save(b, format="PNG")
            b64 = base64.b64encode(b.getvalue()).decode()
            cards += f"""
        <div class='card'>
          <img src='data:image/png;base64,{b64}' alt='QR' />
          <div class='info'>
            <div class='kode'>{_esc(d.get('kode_barang',''))}</div>
            <div class='nama'>{_esc(d.get('nama_barang',''))}</div>
          </div>
        </div>"""
        return cards
    cards = await asyncio.to_thread(_make_cards)
    s = await _settings()
    company = _esc(s.get("nama_perusahaan") or s.get("nama_aplikasi") or "Aplikasi Inventaris")
    return _html_response(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Cetak QR Code</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 18px; }}
  h1 {{ font-size: 16px; margin: 0 0 6px; }}
  .meta {{ color: #667085; font-size: 11px; margin-bottom: 14px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }}
  .card {{ border: 1px dashed #cbd5e1; padding: 8px; text-align: center; page-break-inside: avoid; }}
  .card img {{ width: 140px; height: 140px; }}
  .info {{ margin-top: 6px; font-size: 11px; }}
  .kode {{ font-family: ui-monospace, monospace; font-weight: 600; }}
  .nama {{ color: #475467; }}
  .no-print {{ margin-bottom: 12px; }}
  @media print {{ body {{ margin: 8mm; }} .no-print {{ display: none; }} }}
</style></head><body>
<div class="no-print">
  <button onclick="window.print()" style="padding:6px 14px;background:#2563eb;color:#fff;border:0;border-radius:4px;cursor:pointer">Cetak</button>
  <a href="/barang" onclick="if(history.length>1){{event.preventDefault();history.back()}}" style="margin-left:8px">Kembali</a>
</div>
<h1>{company}</h1>
<div class="meta">Cetak QR Code Barang &mdash; {len(docs)} item</div>
<div class='grid'>{cards}</div>
</body></html>""")


@barcode_bp.get("/barang/print-barcode")
@api_login_required
async def barang_print_barcode(ids: str = Query("")):
    """Print barcode Code-128 untuk banyak barang."""
    from models import barang
    import base64
    import barcode
    from barcode.writer import ImageWriter
    id_list = [x for x in ids.split(",") if x]
    oids = []
    for x in id_list:
        oid = parse_object_id(x)
        if oid is not None: oids.append(oid)
    def _fetch_docs():
        if not oids:
            return list(barang().find({}).limit(20))
        return list(barang().find({"_id": {"$in": oids}}).limit(20))
    docs = await asyncio.to_thread(_fetch_docs)
    def _make_cards():
        cards = ""
        for d in docs:
            code = d.get("kode_barang", str(d["_id"]))
            code128 = barcode.get("code128", code, writer=ImageWriter())
            b = io.BytesIO()
            code128.write(b, options={"write_text": False, "module_height": 12.0, "module_width": 0.3})
            b64 = base64.b64encode(b.getvalue()).decode()
            cards += f"""
        <div class='card'>
          <img src='data:image/png;base64,{b64}' alt='barcode' />
          <div class='info'>
            <div class='kode'>{_esc(code)}</div>
            <div class='nama'>{_esc(d.get('nama_barang',''))}</div>
          </div>
        </div>"""
        return cards
    cards = await asyncio.to_thread(_make_cards)
    s = await _settings()
    company = _esc(s.get("nama_perusahaan") or s.get("nama_aplikasi") or "Aplikasi Inventaris")
    return _html_response(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Cetak Barcode</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 18px; }}
  h1 {{ font-size: 16px; margin: 0 0 6px; }}
  .meta {{ color: #667085; font-size: 11px; margin-bottom: 14px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }}
  .card {{ border: 1px dashed #cbd5e1; padding: 8px; text-align: center; page-break-inside: avoid; }}
  .card img {{ width: 180px; height: 60px; }}
  .info {{ margin-top: 6px; font-size: 11px; }}
  .kode {{ font-family: ui-monospace, monospace; font-weight: 600; }}
  .nama {{ color: #475467; }}
  .no-print {{ margin-bottom: 12px; }}
  @media print {{ body {{ margin: 8mm; }} .no-print {{ display: none; }} }}
</style></head><body>
<div class="no-print">
  <button onclick="window.print()" style="padding:6px 14px;background:#2563eb;color:#fff;border:0;border-radius:4px;cursor:pointer">Cetak</button>
  <a href="/barang" onclick="if(history.length>1){{event.preventDefault();history.back()}}" style="margin-left:8px">Kembali</a>
</div>
<h1>{company}</h1>
<div class="meta">Cetak Barcode Barang &mdash; {len(docs)} item</div>
<div class='grid'>{cards}</div>
</body></html>""")


# ============== BACKUP ==============

@backup_bp.get("/stats")
@role_required("admin")
async def backup_stats():
    def _counts():
        return {
            "users": users().count_documents({}),
            "kategori": kategori().count_documents({}),
            "suplier": suplier().count_documents({}),
            "barang": barang().count_documents({}),
            "barang_masuk": barang_masuk().count_documents({}),
            "barang_keluar": barang_keluar().count_documents({}),
            "penyesuaian": stok_penyesuaian().count_documents({}),
        }
    return {
        "data": await asyncio.to_thread(_counts)
    }


@backup_bp.get("/download")
@role_required("admin")
async def backup_download():
    def _fetch_all():
        return {
            "users": serialize_docs(list(users().find({}))),
            "kategori": serialize_docs(list(kategori().find({}))),
            "suplier": serialize_docs(list(suplier().find({}))),
            "barang": serialize_docs(list(barang().find({}))),
            "barang_masuk": serialize_docs(list(barang_masuk().find({}))),
            "barang_keluar": serialize_docs(list(barang_keluar().find({}))),
        }
    payload = {
        "meta": {
            "app": "Aplikasi Inventaris",
            "exported_at": datetime.now().isoformat(),
            "exported_by": session.get("userId"),
        },
        "data": await asyncio.to_thread(_fetch_all)
    }
    body = json.dumps(payload, default=str, indent=2, ensure_ascii=False)
    fname = f"backup-inventaris-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    return Response(
        body=body,
        content_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
