"""Test tambahan untuk routes/api_barang.py — import, upload foto, QR/barcode, filters."""
from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

from bson import ObjectId
from openpyxl import Workbook

from tests.conftest import login_as


class TestBarangImportXlsx:
    def test_import_template(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/barang/import-template")
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers.get("content-type", "") or "octet" in resp.headers.get("content-type", "")

    def test_import_requires_admin(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        resp = client.get("/api/barang/import-template")
        assert resp.status_code == 403

    def test_import_xlsx_valid(self, client, sample_user, sample_kategori):
        login_as(client, sample_user)
        wb = Workbook()
        ws = wb.active
        ws.append(["kode_barang", "nama_barang", "nama_kategori", "satuan", "stok_awal", "stok_minimum", "lokasi_barang", "deskripsi_barang"])
        ws.append(["BRG-IMP-001", "Barang Import", "Elektronik", "pcs", 10, 2, "Gudang", "Deskripsi"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        resp = client.post(
            "/api/barang/import",
            files={"file": ("test.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200

    def test_import_xlsx_no_file(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/barang/import")
        assert resp.status_code in (400, 422)

    def test_import_xlsx_wrong_ext(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post(
            "/api/barang/import",
            files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert resp.status_code == 400

    def test_import_xlsx_empty_file(self, client, sample_user):
        login_as(client, sample_user)
        wb = Workbook()
        ws = wb.active
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        resp = client.post(
            "/api/barang/import",
            files={"file": ("empty.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 400

    def test_import_requires_admin_role(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        wb = Workbook()
        ws = wb.active
        ws.append(["kode_barang", "nama_barang"])
        ws.append(["BRG-001", "Test"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        resp = client.post(
            "/api/barang/import",
            files={"file": ("test.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 403


class TestBarangUploadFoto:
    def test_upload_foto_requires_admin(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        resp = client.post(
            "/api/barang/upload-foto?kode=BRG-001",
            files={"file": ("photo.png", fake_img, "image/png")},
        )
        assert resp.status_code == 403

    def test_upload_foto_no_kode(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/barang/upload-foto")
        assert resp.status_code in (400, 422)

    def test_upload_foto_no_file(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/barang/upload-foto?kode=BRG-001")
        assert resp.status_code in (400, 422)

    def test_upload_foto_with_file(self, client, sample_user):
        login_as(client, sample_user)
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        with patch("services.cloudinary_service.upload_barang_photo") as mock_upload:
            mock_upload.return_value = {"public_id": "test", "url": "http://example.com/test.jpg"}
            resp = client.post(
                "/api/barang/upload-foto?kode=BRG-001",
                files={"file": ("photo.png", fake_img, "image/png")},
            )
            assert resp.status_code == 200

    def test_upload_foto_base64_no_kode(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/barang/upload-foto-base64", json={"data": "aGVsbG8="})
        assert resp.status_code in (400, 422)

    def test_upload_foto_base64_no_data(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/barang/upload-foto-base64?kode=BRG-001", json={"data": ""})
        assert resp.status_code == 400

    def test_upload_foto_base64_valid(self, client, sample_user):
        login_as(client, sample_user)
        import base64
        fake_data = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100).decode()
        with patch("services.cloudinary_service.upload_barang_photo") as mock_upload:
            mock_upload.return_value = {"public_id": "test", "url": "http://example.com/test.jpg"}
            resp = client.post(
                "/api/barang/upload-foto-base64?kode=BRG-001",
                json={"data": fake_data, "filename": "photo.png"},
            )
            assert resp.status_code == 200

    def test_upload_foto_base64_invalid_b64(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post(
            "/api/barang/upload-foto-base64?kode=BRG-001",
            json={"data": "not-valid-base64!!!"},
        )
        assert resp.status_code == 400

    def test_upload_foto_raw_no_data(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/barang/upload-foto-raw?kode=BRG-001", content=b"")
        assert resp.status_code == 400

    def test_upload_foto_raw_with_data(self, client, sample_user):
        login_as(client, sample_user)
        with patch("services.cloudinary_service.upload_barang_photo") as mock_upload:
            mock_upload.return_value = {"public_id": "test", "url": "http://example.com/test.jpg"}
            resp = client.post(
                "/api/barang/upload-foto-raw?kode=BRG-001",
                content=b"\x89PNG\r\n\x1a\n" + b"\x00" * 50,
                headers={"Content-Type": "image/png"},
            )
            assert resp.status_code == 200


class TestBarangListFilters:
    def test_list_keyword(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barang/?keyword=Laptop")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_list_keyword_no_match(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barang/?keyword=XYZNOTEXIST")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 0

    def test_list_kategori_filter(self, client, sample_user, sample_barang, sample_kategori):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang/?kategori_id={sample_kategori['_id']}")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_list_stok_filter_habis(self, client, sample_user, sample_barang_stok_zero):
        login_as(client, sample_user)
        resp = client.get("/api/barang/?stok=habis")
        assert resp.status_code == 200

    def test_list_stok_filter_hampir_habis(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barang/?stok=hampir-habis")
        assert resp.status_code == 200

    def test_list_stok_filter_tersedia(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barang/?stok=tersedia")
        assert resp.status_code == 200

    def test_lookup_empty_keyword(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barang/lookup")
        assert resp.status_code == 200

    def test_lookup_with_limit(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barang/lookup?limit=1")
        assert resp.status_code == 200


class TestBarangCheckKode:
    def test_check_kode_with_exclude_id(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang/check-kode?kode=BRG-001&exclude_id={sample_barang['_id']}")
        assert resp.status_code == 200
        assert resp.json()["available"] is True

    def test_check_kode_with_invalid_exclude_id(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang/check-kode?kode=BRG-001&exclude_id={ObjectId()}")
        assert resp.status_code == 200
        assert resp.json()["available"] is False

    def test_check_kode_available(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/barang/check-kode?kode=BRG-UNIQUE")
        assert resp.status_code == 200
        assert resp.json()["available"] is True
        assert "tersedia" in resp.json()["message"]


class TestBarangRiwayatStok:
    def test_riwayat_stok_empty(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang/{sample_barang['_id']}/riwayat-stok")
        assert resp.status_code == 200

    def test_riwayat_stok_with_keyword(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang/{sample_barang['_id']}/riwayat-stok?keyword=test")
        assert resp.status_code == 200

    def test_riwayat_stok_with_tipe(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang/{sample_barang['_id']}/riwayat-stok?tipe=masuk")
        assert resp.status_code == 200

    def test_riwayat_stok_requires_login(self, client, sample_barang):
        resp = client.get(f"/api/barang/{sample_barang['_id']}/riwayat-stok")
        assert resp.status_code == 401
