"""Tambahan test untuk services barang_masuk, barang_keluar, setting, stok_penyesuaian, auth, cloudinary."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from bson import ObjectId
import io

from services import (
    barang_masuk_service, barang_keluar_service, setting_service,
    stok_penyesuaian_service, auth_service, cloudinary_service,
)


# ── Barang Masuk Service ──────────────────────────────────────────────


class TestListBarangMasukFilters:
    def test_keyword_filter(self, sample_suplier, sample_barang, db):
        db["barang_masuk"].insert_one({
            "no_transaksi": "BM-F001",
            "tanggal_masuk": "2025-01-15",
            "suplier_id": sample_suplier["_id"],
            "user_id": None,
            "detail": [],
        })
        result = barang_masuk_service.list_barang_masuk(keyword="BM-F001")
        assert len(result) == 1

    def test_keyword_no_match(self, sample_suplier, db):
        db["barang_masuk"].insert_one({
            "no_transaksi": "BM-F002",
            "tanggal_masuk": "2025-01-15",
            "suplier_id": sample_suplier["_id"],
            "user_id": None,
            "detail": [],
        })
        result = barang_masuk_service.list_barang_masuk(keyword="XYZ")
        assert len(result) == 0

    def test_tanggal_filter(self, sample_suplier, db):
        db["barang_masuk"].insert_one({
            "no_transaksi": "BM-F003",
            "tanggal_masuk": "2025-01-15",
            "suplier_id": sample_suplier["_id"],
            "user_id": None,
            "detail": [],
        })
        result = barang_masuk_service.list_barang_masuk(
            tanggal_awal="2025-01-01", tanggal_akhir="2025-12-31"
        )
        assert len(result) == 1

    def test_suplier_filter(self, sample_suplier, db):
        db["barang_masuk"].insert_one({
            "no_transaksi": "BM-F004",
            "tanggal_masuk": "2025-01-15",
            "suplier_id": sample_suplier["_id"],
            "user_id": None,
            "detail": [],
        })
        result = barang_masuk_service.list_barang_masuk(suplier_id=str(sample_suplier["_id"]))
        assert len(result) == 1

    def test_invalid_suplier_filter(self, sample_suplier, db):
        db["barang_masuk"].insert_one({
            "no_transaksi": "BM-F005",
            "tanggal_masuk": "2025-01-15",
            "suplier_id": sample_suplier["_id"],
            "user_id": None,
            "detail": [],
        })
        result = barang_masuk_service.list_barang_masuk(suplier_id="invalid")
        assert len(result) == 1


class TestValidateItems:
    def test_empty_items_raises(self):
        try:
            barang_masuk_service._validate_items([])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Detail barang wajib diisi" in str(e)

    def test_invalid_barang_id_raises(self):
        try:
            barang_masuk_service._validate_items([{"barang_id": "invalid", "jumlah": 5}])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "tidak valid" in str(e)

    def test_jumlah_nol_raises(self, sample_barang):
        try:
            barang_masuk_service._validate_items([{
                "barang_id": str(sample_barang["_id"]),
                "jumlah": 0,
            }])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "lebih dari 0" in str(e)

    def test_barang_not_found_raises(self):
        try:
            barang_masuk_service._validate_items([{
                "barang_id": str(ObjectId()),
                "jumlah": 5,
            }])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Barang tidak ditemukan" in str(e)


class TestUpdateBarangMasuk:
    def test_update_success(self, sample_barang, sample_suplier, db, mock_session):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        }
        result = barang_masuk_service.create_barang_masuk(payload)
        update_payload = {
            "tanggal_masuk": "2025-01-16",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 8}],
        }
        updated = barang_masuk_service.update_barang_masuk(result["id"], update_payload)
        assert updated is not None
        assert updated["tanggal_masuk"] == "2025-01-16"

    def test_invalid_id_returns_none(self):
        assert barang_masuk_service.update_barang_masuk("invalid", {}) is None

    def test_nonexistent_returns_none(self, sample_suplier):
        assert barang_masuk_service.update_barang_masuk(
            str(ObjectId()),
            {"tanggal_masuk": "2025-01-15", "suplier_id": str(sample_suplier["_id"]),
             "detail": []}
        ) is None

    def test_empty_detail_raises(self, sample_barang, sample_suplier, db, mock_session):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        }
        result = barang_masuk_service.create_barang_masuk(payload)
        try:
            barang_masuk_service.update_barang_masuk(result["id"], {
                "tanggal_masuk": "2025-01-16",
                "suplier_id": str(sample_suplier["_id"]),
                "detail": [],
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Detail barang wajib diisi" in str(e)

    def test_invalid_suplier_raises(self, sample_barang, sample_suplier, db, mock_session):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        }
        result = barang_masuk_service.create_barang_masuk(payload)
        try:
            barang_masuk_service.update_barang_masuk(result["id"], {
                "tanggal_masuk": "2025-01-16",
                "suplier_id": str(ObjectId()),
                "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Suplier tidak valid" in str(e)

    def test_empty_tanggal_raises(self, sample_barang, sample_suplier, db, mock_session):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        }
        result = barang_masuk_service.create_barang_masuk(payload)
        try:
            barang_masuk_service.update_barang_masuk(result["id"], {
                "suplier_id": str(sample_suplier["_id"]),
                "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Tanggal masuk wajib diisi" in str(e)


class TestDeleteBarangMasukInvalidId:
    def test_invalid_id(self):
        assert barang_masuk_service.delete_barang_masuk("invalid") is False

    def test_nonexistent(self):
        assert barang_masuk_service.delete_barang_masuk(str(ObjectId())) is False


# ── Barang Keluar Service ─────────────────────────────────────────────


class TestListBarangKeluarFilters:
    def test_keyword_filter(self, sample_barang, db):
        db["barang_keluar"].insert_one({
            "no_transaksi": "BK-F001",
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [],
        })
        result = barang_keluar_service.list_barang_keluar(keyword="BK-F001")
        assert len(result) == 1

    def test_tujuan_filter(self, sample_barang, db):
        db["barang_keluar"].insert_one({
            "no_transaksi": "BK-F002",
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User B",
            "detail": [],
        })
        result = barang_keluar_service.list_barang_keluar(tujuan="User B")
        assert len(result) == 1

    def test_tanggal_filter(self, sample_barang, db):
        db["barang_keluar"].insert_one({
            "no_transaksi": "BK-F003",
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User C",
            "detail": [],
        })
        result = barang_keluar_service.list_barang_keluar(
            tanggal_awal="2025-01-01", tanggal_akhir="2025-12-31"
        )
        assert len(result) == 1


class TestGetBarangKeluarInvalidId:
    def test_invalid_id(self):
        assert barang_keluar_service.get_barang_keluar("invalid") is None


class TestValidateItemsBarangKeluar:
    def test_empty_raises(self):
        try:
            barang_keluar_service._validate_items([])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Detail barang wajib diisi" in str(e)

    def test_invalid_barang_id_raises(self):
        try:
            barang_keluar_service._validate_items([{"barang_id": "invalid", "jumlah": 5}])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "tidak valid" in str(e)

    def test_jumlah_nol_raises(self, sample_barang):
        try:
            barang_keluar_service._validate_items([{
                "barang_id": str(sample_barang["_id"]),
                "jumlah": 0,
            }])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "lebih dari 0" in str(e)

    def test_barang_not_found_raises(self):
        try:
            barang_keluar_service._validate_items([{
                "barang_id": str(ObjectId()),
                "jumlah": 5,
            }])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Barang tidak ditemukan" in str(e)

    def test_stok_tidak_cukup_raises(self, sample_barang):
        try:
            barang_keluar_service._validate_items([{
                "barang_id": str(sample_barang["_id"]),
                "jumlah": 100,
            }])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "tidak cukup" in str(e)


class TestCreateBarangKeluarValidation:
    def test_empty_tanggal_raises(self, sample_barang):
        try:
            barang_keluar_service.create_barang_keluar({
                "tujuan_penerima": "User",
                "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 1}],
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Tanggal keluar wajib diisi" in str(e)

    def test_empty_tujuan_raises(self, sample_barang):
        try:
            barang_keluar_service.create_barang_keluar({
                "tanggal_keluar": "2025-01-20",
                "tujuan_penerima": "",
                "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 1}],
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Tujuan penerima wajib diisi" in str(e)

    def test_empty_detail_raises(self):
        try:
            barang_keluar_service.create_barang_keluar({
                "tanggal_keluar": "2025-01-20",
                "tujuan_penerima": "User",
                "detail": [],
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Detail barang wajib diisi" in str(e)


class TestUpdateBarangKeluar:
    def test_update_success(self, sample_barang, db, mock_session):
        payload = {
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        }
        result = barang_keluar_service.create_barang_keluar(payload)
        updated = barang_keluar_service.update_barang_keluar(result["id"], {
            "tanggal_keluar": "2025-01-21",
            "tujuan_penerima": "User B",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 2}],
        })
        assert updated is not None
        assert updated["tujuan_penerima"] == "User B"

    def test_invalid_id_returns_none(self):
        assert barang_keluar_service.update_barang_keluar("invalid", {}) is None

    def test_nonexistent_returns_none(self):
        assert barang_keluar_service.update_barang_keluar(
            str(ObjectId()),
            {"tanggal_keluar": "2025-01-20", "tujuan_penerima": "X", "detail": []}
        ) is None

    def test_empty_tanggal_raises(self, sample_barang, db, mock_session):
        payload = {
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        }
        result = barang_keluar_service.create_barang_keluar(payload)
        try:
            barang_keluar_service.update_barang_keluar(result["id"], {
                "tujuan_penerima": "User B",
                "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 2}],
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Tanggal keluar wajib diisi" in str(e)

    def test_empty_tujuan_raises(self, sample_barang, db, mock_session):
        payload = {
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        }
        result = barang_keluar_service.create_barang_keluar(payload)
        try:
            barang_keluar_service.update_barang_keluar(result["id"], {
                "tanggal_keluar": "2025-01-21",
                "tujuan_penerima": "",
                "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 2}],
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Tujuan penerima wajib diisi" in str(e)

    def test_stok_tidak_cukup_raises(self, sample_barang, db, mock_session):
        payload = {
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        }
        result = barang_keluar_service.create_barang_keluar(payload)
        try:
            barang_keluar_service.update_barang_keluar(result["id"], {
                "tanggal_keluar": "2025-01-21",
                "tujuan_penerima": "User B",
                "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 100}],
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "tidak cukup" in str(e)


class TestDeleteBarangKeluarInvalidId:
    def test_invalid_id(self):
        assert barang_keluar_service.delete_barang_keluar("invalid") is False

    def test_nonexistent(self):
        assert barang_keluar_service.delete_barang_keluar(str(ObjectId())) is False


# ── Setting Service ───────────────────────────────────────────────────


class TestUploadAssetSetting:
    def test_upload_logo_fallback_local(self, db):
        raw = b"fake image data"
        result = setting_service.upload_asset("logo", raw, "logo.png", "image/png")
        assert "logo" in result
        assert result["logo"].startswith("/static/uploads/settings/")

    def test_upload_favicon_fallback_local(self, db):
        raw = b"fake image data"
        result = setting_service.upload_asset("favicon", raw, "favicon.ico", "image/x-icon")
        assert "favicon" in result

    def test_invalid_kind_raises(self, db):
        try:
            setting_service.upload_asset("invalid", b"data", "f.png", "image/png")
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Kind harus" in str(e)

    def test_upload_logo_with_cloudinary(self, db):
        raw = b"fake image data"
        with patch("config.cloudinary_client.upload_file") as mock_upload:
            mock_upload.return_value = {"secure_url": "https://res.cloudinary.com/test/image/upload/logo.png"}
            result = setting_service.upload_asset("logo", raw, "logo.png", "image/png")
            assert result["logo"] == "https://res.cloudinary.com/test/image/upload/logo.png"


# ── Stok Penyesuaian Service ─────────────────────────────────────────


class TestListPenyesuaianFilters:
    def test_barang_id_filter(self, sample_barang, db):
        db["stok_penyesuaian"].insert_one({
            "no_penyesuaian": "SP-F001",
            "barang_id": sample_barang["_id"],
            "kode_barang": "BRG-001",
            "nama_barang": "Laptop",
            "stok_sistem": 10,
            "stok_fisik": 15,
            "selisih": 5,
            "jenis": "tambah",
            "status": "selesai",
            "tanggal_penyesuaian": "2025-01-25",
            "created_at": None,
        })
        result = stok_penyesuaian_service.list_penyesuaian(barang_id=str(sample_barang["_id"]))
        assert len(result) == 1

    def test_status_filter(self, sample_barang, db):
        db["stok_penyesuaian"].insert_one({
            "no_penyesuaian": "SP-F002",
            "barang_id": sample_barang["_id"],
            "kode_barang": "BRG-001",
            "nama_barang": "Laptop",
            "stok_sistem": 10,
            "stok_fisik": 15,
            "selisih": 5,
            "jenis": "tambah",
            "status": "selesai",
            "tanggal_penyesuaian": "2025-01-25",
            "created_at": None,
        })
        result = stok_penyesuaian_service.list_penyesuaian(status="selesai")
        assert len(result) == 1

    def test_invalid_barang_id_filter(self, sample_barang, db):
        db["stok_penyesuaian"].insert_one({
            "no_penyesuaian": "SP-F003",
            "barang_id": sample_barang["_id"],
            "kode_barang": "BRG-001",
            "nama_barang": "Laptop",
            "stok_sistem": 10,
            "stok_fisik": 15,
            "selisih": 5,
            "jenis": "tambah",
            "status": "selesai",
            "tanggal_penyesuaian": "2025-01-25",
            "created_at": None,
        })
        result = stok_penyesuaian_service.list_penyesuaian(barang_id="invalid")
        assert len(result) == 1


class TestCreatePenyesuaianValidation:
    def test_invalid_barang_id(self):
        try:
            stok_penyesuaian_service.create_penyesuaian({
                "barang_id": "invalid",
                "tanggal_penyesuaian": "2025-01-25",
                "stok_fisik": 5,
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Barang wajib dipilih" in str(e)

    def test_empty_tanggal_raises(self, sample_barang):
        try:
            stok_penyesuaian_service.create_penyesuaian({
                "barang_id": str(sample_barang["_id"]),
                "stok_fisik": 5,
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Tanggal penyesuaian wajib diisi" in str(e)


class TestGetPenyesuaianInvalidId:
    def test_invalid_id(self):
        assert stok_penyesuaian_service.get_penyesuaian("invalid") is None


class TestBatalPenyesuaianInvalidId:
    def test_invalid_id(self):
        assert stok_penyesuaian_service.batal_penyesuaian("invalid", {}) is None

    def test_nonexistent(self):
        assert stok_penyesuaian_service.batal_penyesuaian(
            str(ObjectId()), {"catatan_pembatalan": "Test"}
        ) is None


class TestDeletePenyesuaianInvalidId:
    def test_invalid_id(self):
        assert stok_penyesuaian_service.delete_penyesuaian("invalid") is False

    def test_nonexistent(self):
        assert stok_penyesuaian_service.delete_penyesuaian(str(ObjectId())) is False


# ── Auth Service ──────────────────────────────────────────────────────


class TestUpdateUserValidation:
    def test_empty_name_raises(self, sample_user, mock_session):
        try:
            auth_service.update_user(str(sample_user["_id"]), {"name": ""})
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Nama wajib diisi" in str(e)

    def test_invalid_role_raises(self, sample_user, mock_session):
        try:
            auth_service.update_user(str(sample_user["_id"]), {"role": "superadmin"})
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Role harus admin atau staff" in str(e)

    def test_short_password_raises(self, sample_user, mock_session):
        try:
            auth_service.update_user(str(sample_user["_id"]), {"password": "12345"})
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "minimal 6 karakter" in str(e)

    def test_update_photo(self, sample_user, mock_session):
        result = auth_service.update_user(
            str(sample_user["_id"]),
            {"photo": "http://example.com/photo.jpg"},
        )
        assert result["photo"] == "http://example.com/photo.jpg"

    def test_update_is_active(self, sample_user, mock_session):
        result = auth_service.update_user(
            str(sample_user["_id"]),
            {"is_active": False},
        )
        assert result["is_active"] is False

    def test_update_with_password(self, sample_user, mock_session):
        result = auth_service.update_user(
            str(sample_user["_id"]),
            {"password": "newpassword123"},
        )
        assert result is not None


class TestUpdateProfileValidation:
    def test_empty_name_raises(self, sample_user):
        try:
            auth_service.update_profile(str(sample_user["_id"]), {"name": ""})
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Nama wajib diisi" in str(e)

    def test_update_email(self, sample_user):
        result = auth_service.update_profile(
            str(sample_user["_id"]), {"email": "newemail@test.com"}
        )
        assert result["email"] == "newemail@test.com"

    def test_update_photo(self, sample_user):
        result = auth_service.update_profile(
            str(sample_user["_id"]), {"photo": "http://example.com/p.jpg"}
        )
        assert result["photo"] == "http://example.com/p.jpg"


class TestChangePasswordInvalidId:
    def test_invalid_id(self):
        assert auth_service.change_password("invalid", {}) is None

    def test_nonexistent(self):
        assert auth_service.change_password(str(ObjectId()), {
            "old_password": "admin123",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        }) is None

    def test_empty_new_password(self, sample_user):
        try:
            auth_service.change_password(str(sample_user["_id"]), {
                "old_password": "admin123",
                "new_password": "",
                "confirm_password": "",
            })
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "minimal 6 karakter" in str(e)


class TestUploadPhoto:
    def test_upload_fallback_local(self, sample_user):
        result = auth_service.upload_photo(
            str(sample_user["_id"]),
            b"fake photo data",
            "photo.jpg",
            "image/jpeg",
        )
        assert result is not None
        assert result["photo"] is not None

    def test_invalid_user_id(self):
        result = auth_service.upload_photo("invalid", b"data", "f.jpg", "image/jpeg")
        assert result is None

    def test_nonexistent_user(self):
        result = auth_service.upload_photo(
            str(ObjectId()), b"data", "f.jpg", "image/jpeg"
        )
        assert result is None

    def test_upload_with_cloudinary(self, sample_user):
        with patch("config.cloudinary_client.upload_file") as mock_upload:
            mock_upload.return_value = {
                "secure_url": "https://res.cloudinary.com/test/image/upload/user.jpg",
                "public_id": "user_test",
            }
            result = auth_service.upload_photo(
                str(sample_user["_id"]),
                b"fake data",
                "photo.jpg",
                "image/jpeg",
            )
            assert result["photo"] == "https://res.cloudinary.com/test/image/upload/user.jpg"


# ── Cloudinary Service ────────────────────────────────────────────────


class TestSaveLocal:
    def test_save_local(self, db):
        file_obj = io.BytesIO(b"test content")
        result = cloudinary_service._save_local(file_obj, "test_folder", "test_file", ext="jpg")
        assert result["url"].startswith("/static/uploads/test_folder/")
        assert result["public_id"] is None

    def test_save_local_with_fileobj(self, db):
        file_obj = io.BytesIO(b"test content")
        result = cloudinary_service._save_local(file_obj, "test2", "file2", ext="png")
        assert "png" in result["url"]


class TestVerifyUrlAccessible:
    def test_empty_url(self):
        assert cloudinary_service._verify_url_accessible("") is False

    def test_non_http_url(self):
        assert cloudinary_service._verify_url_accessible("ftp://example.com") is False

    def test_invalid_url(self):
        assert cloudinary_service._verify_url_accessible("not-a-url") is False


class TestUploadBarangPhoto:
    def test_not_configured_local_fallback(self, db):
        file_obj = io.BytesIO(b"fake photo")
        with patch("services.cloudinary_service.is_configured", return_value=False):
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001", filename="photo.jpg")
            assert "url" in result

    def test_configured_upload_success(self, db):
        file_obj = io.BytesIO(b"fake photo")
        with patch("services.cloudinary_service.is_configured", return_value=True), \
             patch("services.cloudinary_service.configure"), \
             patch("services.cloudinary_service.upload_image") as mock_upload, \
             patch("services.cloudinary_service._verify_url_accessible", return_value=True):
            mock_upload.return_value = {
                "secure_url": "https://res.cloudinary.com/test/image/upload/barang.jpg",
                "public_id": "barang_brg-001",
                "width": 100,
                "height": 100,
            }
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001")
            assert result["url"] == "https://res.cloudinary.com/test/image/upload/barang.jpg"

    def test_configured_ghost_upload_fallback(self, db):
        file_obj = io.BytesIO(b"fake photo")
        with patch("services.cloudinary_service.is_configured", return_value=True), \
             patch("services.cloudinary_service.configure"), \
             patch("services.cloudinary_service.upload_image") as mock_upload, \
             patch("services.cloudinary_service._verify_url_accessible", return_value=False):
            mock_upload.return_value = {
                "secure_url": "https://res.cloudinary.com/test/image/upload/ghost.jpg",
                "public_id": "ghost",
            }
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001")
            assert result["public_id"] is None

    def test_cloudinary_error_fallback(self, db):
        file_obj = io.BytesIO(b"fake photo")
        with patch("services.cloudinary_service.is_configured", return_value=True), \
             patch("services.cloudinary_service.configure"), \
             patch("services.cloudinary_service.upload_image", side_effect=Exception("Cloudinary error")):
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001")
            assert result["public_id"] is None

    def test_ext_from_filename(self, db):
        file_obj = io.BytesIO(b"fake photo")
        with patch("services.cloudinary_service.is_configured", return_value=False):
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001", filename="photo.png")
            assert "png" in result["url"]

    def test_ext_from_fileobj_name(self, db):
        file_obj = io.BytesIO(b"fake photo")
        file_obj.name = "photo.webp"
        with patch("services.cloudinary_service.is_configured", return_value=False):
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001")
            assert "webp" in result["url"]


class TestUploadUserPhoto:
    def test_not_configured_local_fallback(self, db):
        file_obj = io.BytesIO(b"fake photo")
        with patch("services.cloudinary_service.is_configured", return_value=False):
            result = cloudinary_service.upload_user_photo(file_obj, "user@test.com")
            assert "url" in result

    def test_configured_success(self, db):
        file_obj = io.BytesIO(b"fake photo")
        with patch("services.cloudinary_service.is_configured", return_value=True), \
             patch("services.cloudinary_service.configure"), \
             patch("services.cloudinary_service.upload_image") as mock_upload:
            mock_upload.return_value = {
                "secure_url": "https://res.cloudinary.com/test/image/upload/user.jpg",
                "public_id": "user_test",
            }
            result = cloudinary_service.upload_user_photo(file_obj, "user@test.com")
            assert result["url"] == "https://res.cloudinary.com/test/image/upload/user.jpg"

    def test_configured_error_fallback(self, db):
        file_obj = io.BytesIO(b"fake photo")
        with patch("services.cloudinary_service.is_configured", return_value=True), \
             patch("services.cloudinary_service.configure"), \
             patch("services.cloudinary_service.upload_image", side_effect=Exception("Error")):
            result = cloudinary_service.upload_user_photo(file_obj, "user@test.com")
            assert "url" in result


class TestUploadAppLogo:
    def test_not_configured_local_fallback(self, db):
        file_obj = io.BytesIO(b"fake logo")
        with patch("services.cloudinary_service.is_configured", return_value=False):
            result = cloudinary_service.upload_app_logo(file_obj)
            assert "url" in result

    def test_configured_success(self, db):
        file_obj = io.BytesIO(b"fake logo")
        with patch("services.cloudinary_service.is_configured", return_value=True), \
             patch("services.cloudinary_service.configure"), \
             patch("services.cloudinary_service.upload_image") as mock_upload:
            mock_upload.return_value = {
                "secure_url": "https://res.cloudinary.com/test/image/upload/logo.png",
                "public_id": "app_logo",
            }
            result = cloudinary_service.upload_app_logo(file_obj)
            assert result["url"] == "https://res.cloudinary.com/test/image/upload/logo.png"

    def test_configured_error_fallback(self, db):
        file_obj = io.BytesIO(b"fake logo")
        with patch("services.cloudinary_service.is_configured", return_value=True), \
             patch("services.cloudinary_service.configure"), \
             patch("services.cloudinary_service.upload_image", side_effect=Exception("Error")):
            result = cloudinary_service.upload_app_logo(file_obj)
            assert "url" in result


class TestRemovePhoto:
    def test_empty_public_id(self):
        cloudinary_service.remove_photo(None)
        cloudinary_service.remove_photo("")

    def test_not_configured(self):
        with patch("services.cloudinary_service.is_configured", return_value=False):
            cloudinary_service.remove_photo("some_id")

    def test删除成功(self):
        with patch("services.cloudinary_service.is_configured", return_value=True), \
             patch("services.cloudinary_service.configure"), \
             patch("services.cloudinary_service.delete_image") as mock_del:
            cloudinary_service.remove_photo("some_id")
            mock_del.assert_called_once_with("some_id")

    def test_delete_error_ignored(self):
        with patch("services.cloudinary_service.is_configured", return_value=True), \
             patch("services.cloudinary_service.configure"), \
             patch("services.cloudinary_service.delete_image", side_effect=Exception("Error")):
            cloudinary_service.remove_photo("some_id")
