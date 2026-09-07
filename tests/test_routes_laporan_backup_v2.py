"""Test tambahan untuk routes/api_laporan_backup.py — barcode, QR, backup, laporan filters."""
from __future__ import annotations

import json
from unittest.mock import patch

from bson import ObjectId

from tests.conftest import login_as


class TestLaporanStokFilters:
    def test_laporan_stok_with_kategori_filter(self, client, sample_user, sample_barang, sample_kategori):
        login_as(client, sample_user)
        resp = client.get(f"/api/laporan/stok?kategori_id={sample_kategori['_id']}")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_laporan_stok_status_habis(self, client, sample_user, sample_barang_stok_zero):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/stok?status=habis")
        assert resp.status_code == 200

    def test_laporan_stok_status_tersedia(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/stok?status=tersedia")
        assert resp.status_code == 200

    def test_laporan_stok_invalid_status(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/stok?status=unknown")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_laporan_stok_requires_login(self, client):
        resp = client.get("/api/laporan/stok")
        assert resp.status_code == 401


class TestLaporanBarangMasukFilters:
    def test_laporan_barang_masuk_with_date_filter(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-03-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        })
        resp = client.get("/api/laporan/barang-masuk?tanggal_awal=2025-03-01&tanggal_akhir=2025-03-31")
        assert resp.status_code == 200

    def test_laporan_barang_masuk_with_suplier_filter(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-03-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        })
        resp = client.get(f"/api/laporan/barang-masuk?suplier_id={sample_suplier['_id']}")
        assert resp.status_code == 200

    def test_laporan_barang_masuk_empty(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/barang-masuk")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestLaporanBarangKeluarFilters:
    def test_laporan_barang_keluar_with_date_filter(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        client.post("/api/barang-keluar/", json={
            "tanggal_keluar": "2025-04-10",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 2}],
        })
        resp = client.get("/api/laporan/barang-keluar?tanggal_awal=2025-04-01&tanggal_akhir=2025-04-30")
        assert resp.status_code == 200

    def test_laporan_barang_keluar_with_tujuan_filter(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        client.post("/api/barang-keluar/", json={
            "tanggal_keluar": "2025-04-10",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 2}],
        })
        resp = client.get("/api/laporan/barang-keluar?tujuan=User")
        assert resp.status_code == 200

    def test_laporan_barang_keluar_empty(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/barang-keluar")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestLaporanPenyesuaianFilters:
    def test_laporan_penyesuaian_with_jenis_filter(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/penyesuaian-stok?jenis=tambah")
        assert resp.status_code == 200

    def test_laporan_penyesuaian_with_status_filter(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/penyesuaian-stok?status=selesai")
        assert resp.status_code == 200

    def test_laporan_penyesuaian_with_all_filters(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/penyesuaian-stok?tanggal_awal=2025-01-01&tanggal_akhir=2025-12-31&jenis=kurang&status=batal")
        assert resp.status_code == 200


class TestPrintLaporan:
    def test_print_stok_with_data(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/stok/print")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_print_masuk_with_data(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-05-01",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        })
        resp = client.get("/api/laporan/barang-masuk/print")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_print_keluar_with_data(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        client.post("/api/barang-keluar/", json={
            "tanggal_keluar": "2025-05-02",
            "tujuan_penerima": "User B",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 1}],
        })
        resp = client.get("/api/laporan/barang-keluar/print")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_print_penyesuaian(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/laporan/penyesuaian-stok/print")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_print_stok_requires_login(self, client):
        resp = client.get("/api/laporan/stok/print")
        assert resp.status_code == 401


class TestBackupStats:
    def test_backup_stats(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/backup/stats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "users" in data
        assert "kategori" in data
        assert "barang" in data

    def test_backup_stats_requires_admin(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        resp = client.get("/api/backup/stats")
        assert resp.status_code == 403

    def test_backup_stats_requires_login(self, client):
        resp = client.get("/api/backup/stats")
        assert resp.status_code == 401


class TestBackupDownload:
    def test_backup_download(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/backup/download")
        assert resp.status_code == 200
        assert "json" in resp.headers.get("content-type", "")
        data = json.loads(resp.body if hasattr(resp, 'body') else resp.text)
        assert "meta" in data
        assert "data" in data
        assert "barang" in data["data"]

    def test_backup_download_with_transactions(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-06-01",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        })
        resp = client.get("/api/backup/download")
        assert resp.status_code == 200

    def test_backup_download_requires_admin(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        resp = client.get("/api/backup/download")
        assert resp.status_code == 403


class TestBackupRestore:
    def test_restore_with_multiple_collections(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/backup/restore", json={
            "data": {
                "kategori": [{"nama_kategori": "Restored Kategori", "icon_kategori": "bi-box"}],
                "suplier": [{"nama": "Restored Suplier", "no_hp": "081111"}],
                "barang": [],
                "barang_masuk": [],
                "barang_keluar": [],
            }
        })
        assert resp.status_code == 200
        assert resp.json()["counts"]["kategori"] == 1
        assert resp.json()["counts"]["suplier"] == 1

    def test_restore_skips_existing_ids(self, client, sample_user, sample_kategori):
        login_as(client, sample_user)
        resp = client.post("/api/backup/restore", json={
            "data": {
                "kategori": [{"_id": str(sample_kategori["_id"]), "nama_kategori": "Should Skip"}],
                "suplier": [],
                "barang": [],
                "barang_masuk": [],
                "barang_keluar": [],
            }
        })
        assert resp.status_code == 200
        assert resp.json()["counts"]["kategori"] == 0

    def test_restore_empty_data(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/backup/restore", json={"data": {}})
        assert resp.status_code == 400

    def test_restore_requires_admin(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        resp = client.post("/api/backup/restore", json={
            "data": {
                "kategori": [],
                "suplier": [],
                "barang": [],
                "barang_masuk": [],
                "barang_keluar": [],
            }
        })
        assert resp.status_code == 403


class TestBarcodeQRCode:
    def test_qrcode_valid_id(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barcode/barang/{sample_barang['_id']}/qrcode")
        assert resp.status_code == 200
        assert "image/png" in resp.headers.get("content-type", "")

    def test_qrcode_invalid_id(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/barcode/barang/invalid-id/qrcode")
        assert resp.status_code == 400

    def test_qrcode_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/barcode/barang/{ObjectId()}/qrcode")
        assert resp.status_code == 404

    def test_barcode_valid_id(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barcode/barang/{sample_barang['_id']}/barcode")
        assert resp.status_code == 200
        assert "image/png" in resp.headers.get("content-type", "")

    def test_barcode_invalid_id(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/barcode/barang/invalid-id/barcode")
        assert resp.status_code == 400

    def test_barcode_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/barcode/barang/{ObjectId()}/barcode")
        assert resp.status_code == 404

    def test_print_qrcode(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barcode/barang/print-qrcode?ids={sample_barang['_id']}")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_print_qrcode_no_ids(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barcode/barang/print-qrcode")
        assert resp.status_code == 200

    def test_print_barcode(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barcode/barang/print-barcode?ids={sample_barang['_id']}")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_print_barcode_no_ids(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barcode/barang/print-barcode")
        assert resp.status_code == 200

    def test_qrcode_requires_login(self, client, sample_barang):
        resp = client.get(f"/api/barcode/barang/{sample_barang['_id']}/qrcode")
        assert resp.status_code == 401

    def test_barcode_requires_login(self, client, sample_barang):
        resp = client.get(f"/api/barcode/barang/{sample_barang['_id']}/barcode")
        assert resp.status_code == 401


class TestTransaksiPrint:
    def test_transaksi_masuk_print(self, client, sample_user, sample_barang, sample_suplier):
        login_as(client, sample_user)
        create_resp = client.post("/api/barang-masuk/", json={
            "tanggal_masuk": "2025-07-01",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        })
        tid = create_resp.json()["id"]
        resp = client.get(f"/api/transaksi/barang-masuk/{tid}/print")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_transaksi_keluar_print(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        create_resp = client.post("/api/barang-keluar/", json={
            "tanggal_keluar": "2025-07-02",
            "tujuan_penerima": "User C",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 2}],
        })
        tid = create_resp.json()["id"]
        resp = client.get(f"/api/transaksi/barang-keluar/{tid}/print")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_transaksi_masuk_print_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/transaksi/barang-masuk/{ObjectId()}/print")
        assert resp.status_code == 404

    def test_transaksi_keluar_print_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/transaksi/barang-keluar/{ObjectId()}/print")
        assert resp.status_code == 404
