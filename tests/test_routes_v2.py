"""Tambahan test untuk routes - menutupi semua branch missing."""
from __future__ import annotations

from bson import ObjectId

from tests.conftest import login_as


# ── Barang Routes - Additional ─────────────────────────────────────────


class TestBarangRoutesV2:
    def test_low_stock(self, client, sample_user, sample_barang_stok_zero):
        login_as(client, sample_user)
        resp = client.get("/api/barang/low-stock")
        assert resp.status_code == 200

    def test_lookup(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barang/lookup?keyword=Laptop")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_riwayat_stok(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang/{sample_barang['_id']}/riwayat-stok")
        assert resp.status_code == 200

    def test_update_not_found(self, client, sample_user, sample_kategori):
        login_as(client, sample_user)
        resp = client.put(f"/api/barang/{ObjectId()}", json={
            "kode_barang": "X",
            "nama_barang": "X",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "pcs",
        })
        assert resp.status_code == 404

    def test_delete_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.delete(f"/api/barang/{ObjectId()}")
        assert resp.status_code == 404

    def test_requires_login(self, client):
        resp = client.get("/api/barang/")
        assert resp.status_code == 401

    def test_low_stock_requires_admin(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        resp = client.get("/api/barang/low-stock")
        assert resp.status_code == 403


# ── Kategori Routes - Additional ──────────────────────────────────────


class TestKategoriRoutesV2:
    def test_update_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.put(f"/api/kategori/{ObjectId()}", json={"nama_kategori": "X"})
        assert resp.status_code == 404

    def test_delete_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.delete(f"/api/kategori/{ObjectId()}")
        assert resp.status_code == 404

    def test_create_invalid_payload(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/kategori/", json={"nama_kategori": ""})
        assert resp.status_code == 400


# ── Suplier Routes - Additional ───────────────────────────────────────


class TestSuplierRoutesV2:
    def test_show(self, client, sample_user, sample_suplier):
        login_as(client, sample_user)
        resp = client.get(f"/api/suplier/{sample_suplier['_id']}")
        assert resp.status_code == 200

    def test_show_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/suplier/{ObjectId()}")
        assert resp.status_code == 404

    def test_create_empty_name(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/suplier/", json={"nama": ""})
        assert resp.status_code == 400

    def test_update_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.put(f"/api/suplier/{ObjectId()}", json={"nama": "X"})
        assert resp.status_code == 404

    def test_delete_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.delete(f"/api/suplier/{ObjectId()}")
        assert resp.status_code == 404

    def test_requires_admin(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        resp = client.post("/api/suplier/", json={"nama": "Test"})
        assert resp.status_code == 403

    def test_requires_login(self, client):
        resp = client.get("/api/suplier/")
        assert resp.status_code == 401


# ── User Routes - Additional ──────────────────────────────────────────


class TestUserRoutesV2:
    def test_show_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/user/{ObjectId()}")
        assert resp.status_code == 404

    def test_update_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.put(f"/api/user/{ObjectId()}", json={"name": "X"})
        assert resp.status_code == 404

    def test_delete_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.delete(f"/api/user/{ObjectId()}")
        assert resp.status_code == 404

    def test_toggle_active_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post(f"/api/user/{ObjectId()}/toggle-active")
        assert resp.status_code == 404

    def test_create_invalid(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/user/", json={
            "name": "",
            "email": "bad",
            "password": "123",
            "role": "invalid",
        })
        assert resp.status_code == 400

    def test_requires_admin(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        resp = client.get("/api/user/")
        assert resp.status_code == 403

    def test_requires_login(self, client):
        resp = client.get("/api/user/")
        assert resp.status_code == 401

    def test_update_self_session(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.put(f"/api/user/{sample_user['_id']}", json={
            "name": "Updated Self",
            "email": sample_user["email"],
        })
        assert resp.status_code == 200


# ── Barang Masuk Routes - Additional ──────────────────────────────────


class TestBarangMasukRoutesV2:
    def test_show_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang-masuk/{ObjectId()}")
        assert resp.status_code == 404

    def test_delete_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.delete(f"/api/barang-masuk/{ObjectId()}")
        assert resp.status_code == 404

    def test_create_invalid_suplier(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(ObjectId()),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        })
        assert resp.status_code == 400

    def test_update_not_found(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        resp = client.put(f"/api/barang-masuk/{ObjectId()}", json={
            "tanggal_masuk": "2025-01-16",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        })
        assert resp.status_code == 404

    def test_update_success(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        create_resp = client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        })
        tid = create_resp.json()["id"]
        resp = client.put(f"/api/barang-masuk/{tid}", json={
            "tanggal_masuk": "2025-01-16",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 8}],
        })
        assert resp.status_code == 200


# ── Barang Keluar Routes - Additional ─────────────────────────────────


class TestBarangKeluarRoutesV2:
    def test_show_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang-keluar/{ObjectId()}")
        assert resp.status_code == 404

    def test_delete_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.delete(f"/api/barang-keluar/{ObjectId()}")
        assert resp.status_code == 404

    def test_create_empty_tujuan(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.post("/api/barang-keluar/", json={
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 1}],
        })
        assert resp.status_code == 400

    def test_update_not_found(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.put(f"/api/barang-keluar/{ObjectId()}", json={
            "tanggal_keluar": "2025-01-21",
            "tujuan_penerima": "User",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 2}],
        })
        assert resp.status_code == 404

    def test_update_success(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        create_resp = client.post("/api/barang-keluar/", json={
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        })
        tid = create_resp.json()["id"]
        resp = client.put(f"/api/barang-keluar/{tid}", json={
            "tanggal_keluar": "2025-01-21",
            "tujuan_penerima": "User B",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 2}],
        })
        assert resp.status_code == 200

    def test_delete_success(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        create_resp = client.post("/api/barang-keluar/", json={
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        })
        tid = create_resp.json()["id"]
        resp = client.delete(f"/api/barang-keluar/{tid}")
        assert resp.status_code == 200


# ── Stok Penyesuaian Routes - Additional ──────────────────────────────


class TestStokPenyesuaianRoutesV2:
    def test_show_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/stok-penyesuaian/{ObjectId()}")
        assert resp.status_code == 404

    def test_delete_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.delete(f"/api/stok-penyesuaian/{ObjectId()}")
        assert resp.status_code == 404

    def test_batal_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post(f"/api/stok-penyesuaian/{ObjectId()}/batal", json={
            "catatan_pembatalan": "Test",
        })
        assert resp.status_code == 404

    def test_delete_success(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        create_resp = client.post("/api/stok-penyesuaian/", json={
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 15,
            "alasan": "Koreksi",
        })
        tid = create_resp.json()["id"]
        client.post(f"/api/stok-penyesuaian/{tid}/batal", json={
            "catatan_pembatalan": "Salah",
        })
        resp = client.delete(f"/api/stok-penyesuaian/{tid}")
        assert resp.status_code == 200

    def test_delete_selesai_raises(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        create_resp = client.post("/api/stok-penyesuaian/", json={
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 15,
            "alasan": "Koreksi",
        })
        tid = create_resp.json()["id"]
        resp = client.delete(f"/api/stok-penyesuaian/{tid}")
        assert resp.status_code == 400


# ── Setting Routes - Additional ───────────────────────────────────────


class TestSettingRoutesV2:
    def test_upload_asset_invalid_kind(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/setting/upload-asset?kind=invalid", content=b"fake",
                          headers={"Content-Type": "image/png"})
        assert resp.status_code in (400, 422)


# ── Laporan Routes ────────────────────────────────────────────────────


class TestLaporanRoutes:
    def test_laporan_stok(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/stok")
        assert resp.status_code == 200

    def test_laporan_stok_with_status(self, client, sample_user, sample_barang_stok_zero):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/stok?status=habis")
        assert resp.status_code == 200

    def test_laporan_stok_hampir_habis(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/stok?status=hampir-habis")
        assert resp.status_code == 200

    def test_laporan_stok_tersedia(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/stok?status=tersedia")
        assert resp.status_code == 200

    def test_laporan_barang_masuk(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/barang-masuk")
        assert resp.status_code == 200

    def test_laporan_barang_keluar(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/barang-keluar")
        assert resp.status_code == 200

    def test_laporan_penyesuaian(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/penyesuaian-stok")
        assert resp.status_code == 200

    def test_laporan_penyesuaian_with_filters(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/penyesuaian-stok?tanggal_awal=2025-01-01&tanggal_akhir=2025-12-31&jenis=tambah&status=selesai")
        assert resp.status_code == 200

    def test_print_stok(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/stok/print")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_print_masuk(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/barang-masuk/print")
        assert resp.status_code == 200

    def test_print_keluar(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/barang-keluar/print")
        assert resp.status_code == 200

    def test_print_penyesuaian(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/penyesuaian-stok/print")
        assert resp.status_code == 200


# ── Transaksi Print Routes ────────────────────────────────────────────


class TestTransaksiPrintRoutes:
    def test_masuk_print_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/transaksi/barang-masuk/{ObjectId()}/print")
        assert resp.status_code == 404

    def test_keluar_print_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/transaksi/barang-keluar/{ObjectId()}/print")
        assert resp.status_code == 404

    def test_masuk_print_success(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        create_resp = client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        })
        tid = create_resp.json()["id"]
        resp = client.get(f"/api/transaksi/barang-masuk/{tid}/print")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_keluar_print_success(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        create_resp = client.post("/api/barang-keluar/", json={
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        })
        tid = create_resp.json()["id"]
        resp = client.get(f"/api/transaksi/barang-keluar/{tid}/print")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")


# ── Backup Routes - Additional ────────────────────────────────────────


class TestBackupRoutesV2:
    def test_restore_with_data(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/backup/restore", json={
            "data": {
                "kategori": [{"nama_kategori": "Restored", "icon_kategori": "bi-box"}],
                "suplier": [],
                "barang": [],
                "barang_masuk": [],
                "barang_keluar": [],
            }
        })
        assert resp.status_code == 200

    def test_restore_empty_data(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/backup/restore", json={"data": {}})
        assert resp.status_code == 400

    def test_download_returns_json(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/backup/download")
        assert resp.status_code == 200
        assert "content-type" in resp.headers
        assert "json" in resp.headers["content-type"]


# ── Page Routes ───────────────────────────────────────────────────────


class TestPageRoutes:
    def test_home_redirect(self, client):
        resp = client.get("/")
        assert resp.status_code in (302, 200)

    def test_login_page(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_dashboard(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/dashboard")
        assert resp.status_code == 200

    def test_barang_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/barang")
        assert resp.status_code == 200

    def test_barang_create_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/barang/create")
        assert resp.status_code == 200

    def test_barang_import_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/barang/import")
        assert resp.status_code == 200

    def test_kategori_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/kategori")
        assert resp.status_code == 200

    def test_suplier_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/suplier")
        assert resp.status_code == 200

    def test_barang_masuk_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/barang-masuk")
        assert resp.status_code == 200

    def test_barang_masuk_create_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/barang-masuk/create")
        assert resp.status_code == 200

    def test_barang_keluar_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/barang-keluar")
        assert resp.status_code == 200

    def test_barang_keluar_create_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/barang-keluar/create")
        assert resp.status_code == 200

    def test_stok_penyesuaian_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/stok-penyesuaian")
        assert resp.status_code == 200

    def test_stok_penyesuaian_create_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/stok-penyesuaian/create")
        assert resp.status_code == 200

    def test_user_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/user")
        assert resp.status_code == 200

    def test_profile_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/profile")
        assert resp.status_code == 200

    def test_change_password_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/change-password")
        assert resp.status_code == 200

    def test_setting_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/setting")
        assert resp.status_code == 200

    def test_laporan_stok_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/laporan/stok")
        assert resp.status_code == 200

    def test_laporan_barang_masuk_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/laporan/barang-masuk")
        assert resp.status_code == 200

    def test_laporan_barang_keluar_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/laporan/barang-keluar")
        assert resp.status_code == 200

    def test_laporan_penyesuaian_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/laporan/penyesuaian-stok")
        assert resp.status_code == 200

    def test_aktivitas_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/aktivitas")
        assert resp.status_code == 200

    def test_backup_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/backup")
        assert resp.status_code == 200

    def test_requires_login_pages(self, client):
        for path in ["/dashboard", "/barang", "/kategori", "/suplier",
                     "/barang-masuk", "/barang-keluar", "/stok-penyesuaian",
                     "/user", "/profile", "/setting", "/aktivitas", "/backup"]:
            resp = client.get(path)
            assert resp.status_code in (302, 401), f"{path} should require login"

    def test_barang_detail_page(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/barang/{sample_barang['_id']}")
        assert resp.status_code == 200

    def test_barang_edit_page(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/barang/{sample_barang['_id']}/edit")
        assert resp.status_code == 200

    def test_barang_print_qrcode_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/barang/print-qrcode")
        assert resp.status_code == 200

    def test_barang_print_barcode_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/barang/print-barcode")
        assert resp.status_code == 200

    def test_barang_masuk_detail_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/barang-masuk/{ObjectId()}")
        assert resp.status_code == 200

    def test_barang_masuk_edit_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/barang-masuk/{ObjectId()}/edit")
        assert resp.status_code == 200

    def test_barang_keluar_detail_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/barang-keluar/{ObjectId()}")
        assert resp.status_code == 200

    def test_barang_keluar_edit_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/barang-keluar/{ObjectId()}/edit")
        assert resp.status_code == 200

    def test_stok_penyesuaian_detail_page(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/stok-penyesuaian/{ObjectId()}")
        assert resp.status_code == 200
