"""Tambahan test untuk services/barang_service.py - menutupi semua branch."""
from __future__ import annotations

import pytest
from bson import ObjectId
from datetime import date

from services import barang_service
from models import barang, kategori, barang_masuk, barang_keluar, riwayat_stok, stok_penyesuaian, suplier


class TestListBarangNoKategori:
    def test_barang_without_kategori(self, db):
        db["barang"].insert_one({
            "kode_barang": "NO-KAT",
            "nama_barang": "Tanpa Kategori",
            "kategori_id": None,
            "satuan": "pcs",
            "stok_awal": 5,
            "stok_minimum": 1,
            "stok": 5,
            "harga_satuan": 10000,
            "created_at": None,
            "updated_at": None,
        })
        result = barang_service.list_barang()
        assert len(result) == 1
        assert result[0]["nama_kategori"] is None
        assert result[0]["icon_kategori"] is None


class TestValidateCommon:
    def test_empty_satuan_raises(self, sample_kategori):
        from services.barang_service import _validate_common
        try:
            _validate_common({
                "kode_barang": "BRG-X",
                "nama_barang": "Test",
                "kategori_id": str(sample_kategori["_id"]),
                "satuan": "",
            }, is_update=False)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Satuan wajib diisi" in str(e)

    def test_negative_stok_awal_raises(self, sample_kategori):
        from services.barang_service import _validate_common
        try:
            _validate_common({
                "kode_barang": "BRG-X",
                "nama_barang": "Test",
                "kategori_id": str(sample_kategori["_id"]),
                "satuan": "pcs",
                "stok_awal": -1,
            }, is_update=False)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "tidak boleh negatif" in str(e)

    def test_negative_stok_minimum_raises(self, sample_kategori):
        from services.barang_service import _validate_common
        try:
            _validate_common({
                "kode_barang": "BRG-X",
                "nama_barang": "Test",
                "kategori_id": str(sample_kategori["_id"]),
                "satuan": "pcs",
                "stok_awal": 0,
                "stok_minimum": -1,
            }, is_update=False)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "tidak boleh negatif" in str(e)


class TestUpdateBarangInvalidId:
    def test_invalid_id_returns_none(self, sample_kategori):
        payload = {
            "kode_barang": "X",
            "nama_barang": "X",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "pcs",
        }
        assert barang_service.update_barang("invalid", payload) is None


class TestDeleteBarangInvalidId:
    def test_invalid_id_returns_false(self):
        assert barang_service.delete_barang("invalid") is False


class TestDeleteBarangWithPhoto:
    def test_deletes_cloudinary_photo(self, sample_barang, mock_session):
        from unittest.mock import patch
        sample_barang["foto"] = {"public_id": "test_public_id", "url": "http://example.com/photo.jpg"}
        barang().update_one({"_id": sample_barang["_id"]}, {"$set": {"foto": sample_barang["foto"]}})
        with patch("services.barang_service.cloudinary_service.remove_photo") as mock_rm:
            result = barang_service.delete_barang(str(sample_barang["_id"]))
            assert result is True
            mock_rm.assert_called_once_with("test_public_id")


class TestUpdateBarangWithPhotoRemoval:
    def test_removes_old_photo(self, sample_barang, sample_kategori, mock_session):
        from unittest.mock import patch
        old_photo = {"public_id": "old_photo_id", "url": "http://example.com/old.jpg"}
        barang().update_one({"_id": sample_barang["_id"]}, {"$set": {"foto": old_photo}})
        payload = {
            "kode_barang": "BRG-001",
            "nama_barang": "Laptop Updated",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "unit",
            "stok_awal": 10,
            "stok_minimum": 2,
            "foto": {"public_id": "new_photo_id", "url": "http://example.com/new.jpg"},
        }
        with patch("services.barang_service.cloudinary_service.remove_photo") as mock_rm:
            result = barang_service.update_barang(str(sample_barang["_id"]), payload)
            assert result is not None
            mock_rm.assert_called_once_with("old_photo_id")


class TestRecentBarangMasuk:
    def test_empty(self, db):
        result = barang_service.recent_barang_masuk()
        assert result == []

    def test_with_data(self, sample_suplier, sample_barang, db):
        db["barang_masuk"].insert_one({
            "no_transaksi": "BM-R001",
            "tanggal_masuk": "2025-01-15",
            "suplier_id": sample_suplier["_id"],
            "user_id": None,
            "detail": [{"kode_barang": "X", "nama_barang": "Y", "jumlah": 5}],
        })
        result = barang_service.recent_barang_masuk()
        assert len(result) == 1
        assert result[0]["total_jumlah"] == 5
        assert result[0]["item_count"] == 1
        assert result[0]["nama_suplier"] == "Suplier A"

    def test_limit(self, db):
        for i in range(5):
            db["barang_masuk"].insert_one({
                "no_transaksi": f"BM-L{i:03d}",
                "tanggal_masuk": "2025-01-15",
                "suplier_id": None,
                "user_id": None,
                "detail": [],
            })
        result = barang_service.recent_barang_masuk(limit=3)
        assert len(result) == 3


class TestRecentBarangKeluar:
    def test_empty(self, db):
        result = barang_service.recent_barang_keluar()
        assert result == []

    def test_with_data(self, sample_barang, db):
        db["barang_keluar"].insert_one({
            "no_transaksi": "BK-R001",
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"kode_barang": "X", "nama_barang": "Y", "jumlah": 3}],
        })
        result = barang_service.recent_barang_keluar()
        assert len(result) == 1
        assert result[0]["total_jumlah"] == 3
        assert result[0]["item_count"] == 1
        assert result[0]["tujuan_penerima"] == "User A"

    def test_limit(self, db):
        for i in range(5):
            db["barang_keluar"].insert_one({
                "no_transaksi": f"BK-L{i:03d}",
                "tanggal_keluar": "2025-01-20",
                "tujuan_penerima": "User",
                "detail": [],
            })
        result = barang_service.recent_barang_keluar(limit=2)
        assert len(result) == 2


class TestMonthlyTrendWithData:
    def test_with_masuk_data(self, db):
        from unittest.mock import patch, MagicMock
        from datetime import date
        today = date.today()
        current_key = today.strftime("%Y-%m")
        mock_bm_coll = MagicMock()
        mock_bm_coll.aggregate.return_value = [{"_id": current_key, "total": 10}]
        mock_bk_coll = MagicMock()
        mock_bk_coll.aggregate.return_value = []
        with patch("models.barang_masuk", return_value=mock_bm_coll), \
             patch("models.barang_keluar", return_value=mock_bk_coll):
            result = barang_service.monthly_trend(months=3)
            assert len(result["labels"]) == 3
            assert result["masuk"][-1] == 10
            assert result["keluar"][-1] == 0

    def test_with_keluar_data(self, db):
        from unittest.mock import patch, MagicMock
        from datetime import date
        today = date.today()
        current_key = today.strftime("%Y-%m")
        mock_bm_coll = MagicMock()
        mock_bm_coll.aggregate.return_value = []
        mock_bk_coll = MagicMock()
        mock_bk_coll.aggregate.return_value = [{"_id": current_key, "total": 7}]
        with patch("models.barang_masuk", return_value=mock_bm_coll), \
             patch("models.barang_keluar", return_value=mock_bk_coll):
            result = barang_service.monthly_trend(months=3)
            assert result["masuk"][-1] == 0
            assert result["keluar"][-1] == 7

    def test_with_keluar_data(self, db):
        from unittest.mock import patch, MagicMock
        from datetime import date
        today = date.today()
        current_key = today.strftime("%Y-%m")
        mock_bm_coll = MagicMock()
        mock_bm_coll.aggregate.return_value = []
        mock_bk_coll = MagicMock()
        mock_bk_coll.aggregate.return_value = [{"_id": current_key, "total": 7}]
        with patch("models.barang_masuk", return_value=mock_bm_coll), \
             patch("models.barang_keluar", return_value=mock_bk_coll):
            result = barang_service.monthly_trend(months=3)
            assert result["masuk"][-1] == 0
            assert result["keluar"][-1] == 7


class TestKategoriDistributionMoreThan6:
    def test_with_many_kategori(self, db):
        kat_ids = []
        for i in range(8):
            kid = ObjectId()
            db["kategori"].insert_one({
                "_id": kid,
                "nama_kategori": f"Kat {i}",
                "icon_kategori": "bi-box",
            })
            db["barang"].insert_one({
                "kode_barang": f"BRG-K{i:02d}",
                "nama_barang": f"Barang K{i}",
                "kategori_id": kid,
                "satuan": "pcs",
                "stok_awal": i + 1,
                "stok_minimum": 1,
                "stok": i + 1,
            })
            kat_ids.append(kid)
        result = barang_service.kategori_distribution()
        assert "Lainnya" in result["labels"]
        assert len(result["labels"]) == 7


class TestListLookup:
    def test_empty(self, db):
        assert barang_service.list_lookup() == []

    def test_with_keyword(self, sample_barang):
        result = barang_service.list_lookup(keyword="Laptop")
        assert len(result) == 1
        assert result[0]["kode_barang"] == "BRG-001"

    def test_no_match(self, sample_barang):
        assert barang_service.list_lookup(keyword="XYZ") == []

    def test_limit(self, db, sample_kategori):
        for i in range(10):
            db["barang"].insert_one({
                "kode_barang": f"LK-{i:02d}",
                "nama_barang": f"Lookup {i}",
                "kategori_id": sample_kategori["_id"],
                "satuan": "pcs",
                "stok_awal": 1,
                "stok_minimum": 0,
                "stok": 1,
            })
        result = barang_service.list_lookup(limit=5)
        assert len(result) == 5


class TestImportXlsx:
    def test_success(self, sample_kategori):
        headers = ["kode_barang", "nama_barang", "nama_kategori", "satuan",
                    "stok_awal", "stok_minimum", "lokasi_barang", "deskripsi_barang"]
        rows = [
            ["IMP-001", "Item Import", "Elektronik", "pcs", 10, 2, "Gudang", "Deskripsi"],
        ]
        result = barang_service.import_xlsx(headers, rows)
        assert result["success_count"] == 1
        assert result["failed_count"] == 0

    def test_auto_create_kategori(self, db):
        headers = ["kode_barang", "nama_barang", "nama_kategori", "satuan"]
        rows = [["IMP-002", "Item Baru", "Kategori Baru", "pcs"]]
        result = barang_service.import_xlsx(headers, rows)
        assert result["success_count"] == 1
        assert db["kategori"].count_documents({"nama_kategori": "Kategori Baru"}) == 1

    def test_empty_row_skipped(self, sample_kategori):
        headers = ["kode_barang", "nama_barang", "nama_kategori", "satuan"]
        rows = [[None, None, None, None]]
        result = barang_service.import_xlsx(headers, rows)
        assert result["success_count"] == 0

    def test_missing_header_raises(self):
        try:
            barang_service.import_xlsx(["only_one_col"], [])
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Header minimal" in str(e)

    def test_empty_field_raises(self, sample_kategori):
        headers = ["kode_barang", "nama_barang", "nama_kategori", "satuan"]
        rows = [["", "Item", "Elektronik", "pcs"]]
        result = barang_service.import_xlsx(headers, rows)
        assert result["failed_count"] == 1

    def test_optional_columns_missing(self, sample_kategori):
        headers = ["kode_barang", "nama_barang", "nama_kategori", "satuan"]
        rows = [["IMP-003", "Minimal", "Elektronik", "pcs"]]
        result = barang_service.import_xlsx(headers, rows)
        assert result["success_count"] == 1


class TestTopOutgoingItemsWithData:
    def test_with_data(self, sample_barang, db):
        db["barang_keluar"].insert_one({
            "no_transaksi": "BK-TO1",
            "tanggal_keluar": "2025-01-20",
            "tujuan_penerima": "User A",
            "detail": [{"kode_barang": "BRG-001", "nama_barang": "Laptop", "jumlah": 5}],
        })
        result = barang_service.top_outgoing_items(limit=5)
        assert len(result["labels"]) == 1
        assert result["values"][0] == 5
        assert len(result["table"]) == 1


class TestCatatRiwayatStok:
    def test_creates_record(self, db):
        barang_service.catat_riwayat_stok(
            "brg123", "BRG-001", "Laptop", 10, 15, 5, "masuk",
            ref_id="ref123", ref_no="BM-001", keterangan="Test",
        )
        assert riwayat_stok().count_documents({}) == 1


class TestGetRiwayatStok:
    def test_empty(self, db):
        result = barang_service.get_riwayat_stok(str(ObjectId()))
        assert result["data"] == []
        assert result["total"] == 0

    def test_with_data(self, db):
        barang_service.catat_riwayat_stok(
            str(ObjectId()), "BRG-001", "Laptop", 10, 15, 5, "masuk",
        )
        all_docs = list(riwayat_stok().find({}))
        result = barang_service.get_riwayat_stok(str(all_docs[0]["barang_id"]))
        assert len(result["data"]) == 1
        assert result["total"] == 1

    def test_invalid_id(self):
        result = barang_service.get_riwayat_stok("invalid")
        assert result["data"] == []

    def test_pagination(self, db):
        bid = str(ObjectId())
        for i in range(10):
            barang_service.catat_riwayat_stok(
                bid, "BRG-001", "Laptop", i, i + 1, 1, "masuk",
                ref_no=f"BM-{i:03d}",
            )
        result = barang_service.get_riwayat_stok(bid, page=1, per_page=5)
        assert len(result["data"]) == 5
        assert result["total"] == 10
        assert result["total_pages"] == 2

    def test_filter_tipe(self, db):
        bid = str(ObjectId())
        barang_service.catat_riwayat_stok(bid, "BRG-001", "Laptop", 10, 15, 5, "masuk")
        barang_service.catat_riwayat_stok(bid, "BRG-001", "Laptop", 15, 12, -3, "keluar")
        result = barang_service.get_riwayat_stok(bid, tipe="masuk")
        assert len(result["data"]) == 1
        assert result["data"][0]["tipe"] == "masuk"

    def test_keyword_search(self, db):
        bid = str(ObjectId())
        barang_service.catat_riwayat_stok(bid, "BRG-001", "Laptop", 10, 15, 5, "masuk", ref_no="BM-001")
        barang_service.catat_riwayat_stok(bid, "BRG-001", "Laptop", 15, 12, -3, "keluar", ref_no="BK-001")
        result = barang_service.get_riwayat_stok(bid, keyword="BM")
        assert len(result["data"]) == 1
        assert result["data"][0]["ref_no"] == "BM-001"


class TestRecentPenyesuaian:
    def test_empty(self, db):
        assert barang_service.recent_penyesuaian() == []

    def test_with_data(self, sample_barang, db):
        db["stok_penyesuaian"].insert_one({
            "no_penyesuaian": "SP-R001",
            "tanggal_penyesuaian": "2025-01-25",
            "barang_id": sample_barang["_id"],
            "kode_barang": "BRG-001",
            "nama_barang": "Laptop",
            "stok_sistem": 10,
            "stok_fisik": 15,
            "selisih": 5,
            "jenis": "tambah",
            "status": "selesai",
            "alasan": "Koreksi",
            "created_at": None,
        })
        result = barang_service.recent_penyesuaian()
        assert len(result) == 1
        assert result[0]["selisih"] == 5

    def test_limit(self, db):
        for i in range(5):
            db["stok_penyesuaian"].insert_one({
                "no_penyesuaian": f"SP-L{i:03d}",
                "tanggal_penyesuaian": "2025-01-25",
                "kode_barang": f"BRG-{i:03d}",
                "nama_barang": f"Item {i}",
                "stok_sistem": 10,
                "stok_fisik": 15,
                "selisih": 5,
                "jenis": "tambah",
                "status": "selesai",
            })
        result = barang_service.recent_penyesuaian(limit=2)
        assert len(result) == 2
