"""Test untuk routes transaksi (barang masuk, barang keluar, stok penyesuaian)."""
from __future__ import annotations

from bson import ObjectId

from tests.conftest import login_as


# ── Barang Masuk Routes ─────────────────────────────────────────────


class TestBarangMasukRoutes:
    def test_list(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        resp = client.get("/api/barang-masuk/")
        assert resp.status_code == 200

    def test_create(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        resp = client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        })
        assert resp.status_code == 200
        assert resp.json()["no_transaksi"].startswith("BM-")

    def test_show(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        create_resp = client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        })
        tid = create_resp.json()["id"]
        resp = client.get(f"/api/barang-masuk/{tid}")
        assert resp.status_code == 200

    def test_delete(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        create_resp = client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        })
        tid = create_resp.json()["id"]
        resp = client.delete(f"/api/barang-masuk/{tid}")
        assert resp.status_code == 200

    def test_generate_number(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/barang-masuk/generate-number")
        assert resp.status_code == 200
        assert "BM-" in resp.json()["no_transaksi"]

    def test_create_staff_allowed(self, client, sample_staff_user, sample_barang, sample_suplier):
        login_as(client, sample_staff_user)
        resp = client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 2}],
        })
        assert resp.status_code == 200


# ── Barang Keluar Routes ────────────────────────────────────────────


class TestBarangKeluarRoutes:
    def test_list(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/barang-keluar/")
        assert resp.status_code == 200

    def test_create(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.post("/api/barang-keluar/", json={
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        })
        assert resp.status_code == 200
        assert resp.json()["no_transaksi"].startswith("BK-")

    def test_stok_tidak_cukup(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.post("/api/barang-keluar/", json={
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 100}],
        })
        assert resp.status_code == 400

    def test_generate_number(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/barang-keluar/generate-number")
        assert resp.status_code == 200
        assert "BK-" in resp.json()["no_transaksi"]


# ── Stok Penyesuaian Routes ────────────────────────────────────────


class TestStokPenyesuaianRoutes:
    def test_list(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/stok-penyesuaian/")
        assert resp.status_code == 200

    def test_create(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.post("/api/stok-penyesuaian/", json={
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 15,
            "alasan": "Koreksi",
        })
        assert resp.status_code == 200
        assert resp.json()["no_penyesuaian"].startswith("SP-")

    def test_batal(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        create_resp = client.post("/api/stok-penyesuaian/", json={
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 15,
            "alasan": "Koreksi",
        })
        tid = create_resp.json()["id"]
        resp = client.post(f"/api/stok-penyesuaian/{tid}/batal", json={
            "catatan_pembatalan": "Salah",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "dibatalkan"

    def test_generate_number(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/stok-penyesuaian/generate-number")
        assert resp.status_code == 200
        assert "SP-" in resp.json()["no_penyesuaian"]


# ── Setting Routes ──────────────────────────────────────────────────


class TestSettingRoutes:
    def test_get_settings(self, client, sample_user, sample_setting):
        login_as(client, sample_user)
        resp = client.get("/api/setting/")
        assert resp.status_code == 200

    def test_update_settings(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.put("/api/setting/", json={"nama_aplikasi": "New App"})
        assert resp.status_code == 200
        assert resp.json()["data"]["nama_aplikasi"] == "New App"


# ── Aktivitas Routes ────────────────────────────────────────────────


class TestAktivitasRoutes:
    def test_list(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/aktivitas/")
        assert resp.status_code == 200
        assert "data" in resp.json()


# ── Health Check ────────────────────────────────────────────────────


class TestHealth:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ── Backup Routes ──────────────────────────────────────────────────


class TestBackupRoutes:
    def test_stats(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/backup/stats")
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_download(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/backup/download")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"

    def test_restore(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/backup/restore", json={
            "data": {"kategori": [], "suplier": [], "barang": []}
        })
        assert resp.status_code == 200
        assert "Restore berhasil" in resp.json()["message"]
