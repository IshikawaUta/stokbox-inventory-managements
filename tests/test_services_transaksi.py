"""Test untuk services barang masuk, barang keluar, dan stok penyesuaian."""
from __future__ import annotations

from datetime import datetime, timezone
from bson import ObjectId

from services import barang_masuk_service, barang_keluar_service, stok_penyesuaian_service


# ── Barang Masuk ──────────────────────────────────────────────────────


class TestListBarangMasuk:
    def test_empty(self, db):
        assert barang_masuk_service.list_barang_masuk() == []

    def test_returns_all(self, sample_suplier, sample_barang, db):
        db["barang_masuk"].insert_one({
            "no_transaksi": "BM-001",
            "tanggal_masuk": "2025-01-15",
            "suplier_id": sample_suplier["_id"],
            "user_id": None,
            "detail": [{"kode_barang": "X", "nama_barang": "Y", "jumlah": 5}],
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        })
        result = barang_masuk_service.list_barang_masuk()
        assert len(result) == 1


class TestGetBarangMasuk:
    def test_valid_id(self, sample_suplier, db):
        doc = {
            "no_transaksi": "BM-GET",
            "tanggal_masuk": "2025-01-15",
            "suplier_id": sample_suplier["_id"],
            "user_id": None,
            "detail": [],
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        }
        result = db["barang_masuk"].insert_one(doc)
        got = barang_masuk_service.get_barang_masuk(str(result.inserted_id))
        assert got is not None
        assert got["no_transaksi"] == "BM-GET"

    def test_nonexistent(self):
        assert barang_masuk_service.get_barang_masuk(str(ObjectId())) is None

    def test_invalid_id(self):
        assert barang_masuk_service.get_barang_masuk("invalid") is None


class TestCreateBarangMasuk:
    def test_create_success(self, sample_barang, sample_suplier, mock_session):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "user_id": str(sample_barang["_id"]),
            "detail": [{
                "barang_id": str(sample_barang["_id"]),
                "jumlah": 5,
            }],
        }
        result = barang_masuk_service.create_barang_masuk(payload)
        assert result["no_transaksi"].startswith("BM-")

    def test_stok_increased(self, sample_barang, sample_suplier, db, mock_session):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "user_id": str(sample_barang["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        }
        barang_masuk_service.create_barang_masuk(payload)
        updated = db["barang"].find_one({"_id": sample_barang["_id"]})
        assert updated["stok"] == 15

    def test_invalid_suplier_raises(self, sample_barang):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(ObjectId()),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        }
        try:
            barang_masuk_service.create_barang_masuk(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Suplier tidak valid" in str(e)

    def test_empty_tanggal_raises(self, sample_barang, sample_suplier):
        payload = {
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        }
        try:
            barang_masuk_service.create_barang_masuk(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Tanggal masuk wajib diisi" in str(e)

    def test_empty_detail_raises(self, sample_suplier):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [],
        }
        try:
            barang_masuk_service.create_barang_masuk(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Detail barang wajib diisi" in str(e)

    def test_jumlah_nol_raises(self, sample_barang, sample_suplier):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 0}],
        }
        try:
            barang_masuk_service.create_barang_masuk(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "lebih dari 0" in str(e)


class TestDeleteBarangMasuk:
    def test_delete_success(self, sample_barang, sample_suplier, db, mock_session):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "user_id": str(sample_barang["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        }
        result = barang_masuk_service.create_barang_masuk(payload)
        deleted = barang_masuk_service.delete_barang_masuk(result["id"])
        assert deleted is True

    def test_stok_decreased_on_delete(self, sample_barang, sample_suplier, db, mock_session):
        payload = {
            "tanggal_masuk": "2025-01-15",
            "suplier_id": str(sample_suplier["_id"]),
            "user_id": str(sample_barang["_id"]),
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 5}],
        }
        result = barang_masuk_service.create_barang_masuk(payload)
        barang_masuk_service.delete_barang_masuk(result["id"])
        updated = db["barang"].find_one({"_id": sample_barang["_id"]})
        assert updated["stok"] == 10

    def test_nonexistent(self):
        assert barang_masuk_service.delete_barang_masuk(str(ObjectId())) is False


# ── Barang Keluar ─────────────────────────────────────────────────────


class TestListBarangKeluar:
    def test_empty(self, db):
        assert barang_keluar_service.list_barang_keluar() == []


class TestGetBarangKeluar:
    def test_nonexistent(self):
        assert barang_keluar_service.get_barang_keluar(str(ObjectId())) is None


class TestCreateBarangKeluar:
    def test_create_success(self, sample_barang, mock_session):
        payload = {
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        }
        result = barang_keluar_service.create_barang_keluar(payload)
        assert result["no_transaksi"].startswith("BK-")

    def test_stok_decreased(self, sample_barang, db, mock_session):
        payload = {
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        }
        barang_keluar_service.create_barang_keluar(payload)
        updated = db["barang"].find_one({"_id": sample_barang["_id"]})
        assert updated["stok"] == 7

    def test_stok_tidak_cukup_raises(self, sample_barang):
        payload = {
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 100}],
        }
        try:
            barang_keluar_service.create_barang_keluar(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "tidak cukup" in str(e)

    def test_empty_tujuan_raises(self, sample_barang):
        payload = {
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 1}],
        }
        try:
            barang_keluar_service.create_barang_keluar(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Tujuan penerima wajib diisi" in str(e)


class TestDeleteBarangKeluar:
    def test_stok_restored_on_delete(self, sample_barang, db, mock_session):
        payload = {
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"barang_id": str(sample_barang["_id"]), "jumlah": 3}],
        }
        result = barang_keluar_service.create_barang_keluar(payload)
        barang_keluar_service.delete_barang_keluar(result["id"])
        updated = db["barang"].find_one({"_id": sample_barang["_id"]})
        assert updated["stok"] == 10


# ── Stok Penyesuaian ─────────────────────────────────────────────────


class TestListPenyesuaian:
    def test_empty(self, db):
        assert stok_penyesuaian_service.list_penyesuaian() == []


class TestGetPenyesuaian:
    def test_nonexistent(self):
        assert stok_penyesuaian_service.get_penyesuaian(str(ObjectId())) is None


class TestCreatePenyesuaian:
    def test_create_success(self, sample_barang, mock_session):
        payload = {
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 15,
            "alasan": "Koreksi stok",
        }
        result = stok_penyesuaian_service.create_penyesuaian(payload)
        assert result["no_penyesuaian"].startswith("SP-")
        assert result["selisih"] == 5

    def test_stok_updated(self, sample_barang, db, mock_session):
        payload = {
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 8,
            "alasan": "Koreksi",
        }
        stok_penyesuaian_service.create_penyesuaian(payload)
        updated = db["barang"].find_one({"_id": sample_barang["_id"]})
        assert updated["stok"] == 8

    def test_invalid_barang_raises(self):
        payload = {
            "barang_id": str(ObjectId()),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 5,
        }
        try:
            stok_penyesuaian_service.create_penyesuaian(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Barang tidak ditemukan" in str(e)

    def test_negative_stok_fisik_raises(self, sample_barang):
        payload = {
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": -1,
        }
        try:
            stok_penyesuaian_service.create_penyesuaian(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "negatif" in str(e)


class TestBatalPenyesuaian:
    def test_batal_success(self, sample_barang, mock_session):
        payload = {
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 15,
            "alasan": "Koreksi",
        }
        result = stok_penyesuaian_service.create_penyesuaian(payload)
        batal = stok_penyesuaian_service.batal_penyesuaian(
            result["id"],
            {"catatan_pembatalan": "Salah input"},
        )
        assert batal["status"] == "dibatalkan"

    def test_stok_restored_on_batal(self, sample_barang, db, mock_session):
        payload = {
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 15,
            "alasan": "Koreksi",
        }
        result = stok_penyesuaian_service.create_penyesuaian(payload)
        stok_penyesuaian_service.batal_penyesuaian(
            result["id"], {"catatan_pembatalan": "Salah"}
        )
        updated = db["barang"].find_one({"_id": sample_barang["_id"]})
        assert updated["stok"] == 10

    def test_double_batal_raises(self, sample_barang, mock_session):
        payload = {
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 15,
            "alasan": "Koreksi",
        }
        result = stok_penyesuaian_service.create_penyesuaian(payload)
        stok_penyesuaian_service.batal_penyesuaian(
            result["id"], {"catatan_pembatalan": "Salah"}
        )
        try:
            stok_penyesuaian_service.batal_penyesuaian(
                result["id"], {"catatan_pembatalan": "Lagi"}
            )
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "sudah pernah dibatalkan" in str(e)


class TestDeletePenyesuaian:
    def test_delete_dibatalkan(self, sample_barang, mock_session):
        payload = {
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 15,
            "alasan": "Koreksi",
        }
        result = stok_penyesuaian_service.create_penyesuaian(payload)
        stok_penyesuaian_service.batal_penyesuaian(
            result["id"], {"catatan_pembatalan": "Salah"}
        )
        deleted = stok_penyesuaian_service.delete_penyesuaian(result["id"])
        assert deleted is True

    def test_delete_selesai_raises(self, sample_barang, mock_session):
        payload = {
            "barang_id": str(sample_barang["_id"]),
            "tanggal_penyesuaian": "2025-01-25",
            "stok_fisik": 15,
            "alasan": "Koreksi",
        }
        result = stok_penyesuaian_service.create_penyesuaian(payload)
        try:
            stok_penyesuaian_service.delete_penyesuaian(result["id"])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "dibatalkan" in str(e)
