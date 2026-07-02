"""Test untuk services/barang_service.py."""
from __future__ import annotations

from bson import ObjectId

from services import barang_service


class TestListBarang:
    def test_empty(self, db):
        assert barang_service.list_barang() == []

    def test_returns_all(self, sample_barang):
        result = barang_service.list_barang()
        assert len(result) == 1
        assert result[0]["kode_barang"] == "BRG-001"

    def test_keyword_filter(self, sample_barang):
        assert len(barang_service.list_barang(keyword="Laptop")) == 1
        assert len(barang_service.list_barang(keyword="XYZ")) == 0

    def test_kategori_filter(self, sample_barang, sample_kategori):
        result = barang_service.list_barang(kategori_id=str(sample_kategori["_id"]))
        assert len(result) == 1

    def test_stok_filter_habis(self, sample_barang, sample_barang_stok_zero):
        result = barang_service.list_barang(stok_filter="habis")
        assert len(result) == 1
        assert result[0]["kode_barang"] == "BRG-002"

    def test_stok_filter_tersedia(self, sample_barang, sample_barang_stok_zero):
        result = barang_service.list_barang(stok_filter="tersedia")
        assert len(result) == 1
        assert result[0]["kode_barang"] == "BRG-001"

    def test_stok_filter_hampir_habis(self, db, sample_kategori):
        bid = ObjectId()
        db["barang"].insert_one({
            "_id": bid,
            "kode_barang": "BRG-003",
            "nama_barang": "Stok Tipis",
            "kategori_id": sample_kategori["_id"],
            "satuan": "pcs",
            "stok_awal": 2,
            "stok_minimum": 5,
            "stok": 2,
            "created_at": None,
            "updated_at": None,
        })
        result = barang_service.list_barang(stok_filter="hampir-habis")
        assert len(result) == 1
        assert result[0]["kode_barang"] == "BRG-003"


class TestGetBarang:
    def test_valid_id(self, sample_barang):
        result = barang_service.get_barang(str(sample_barang["_id"]))
        assert result is not None
        assert result["kode_barang"] == "BRG-001"

    def test_includes_kategori(self, sample_barang):
        result = barang_service.get_barang(str(sample_barang["_id"]))
        assert result["nama_kategori"] == "Elektronik"

    def test_invalid_id(self):
        assert barang_service.get_barang("invalid") is None

    def test_nonexistent(self):
        assert barang_service.get_barang(str(ObjectId())) is None


class TestCreateBarang:
    def test_create_success(self, sample_kategori, mock_session):
        payload = {
            "kode_barang": "BRG-NEW",
            "nama_barang": "Keyboard",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "pcs",
            "stok_awal": 20,
            "stok_minimum": 5,
        }
        result = barang_service.create_barang(payload)
        assert result["kode_barang"] == "BRG-NEW"
        assert result["stok"] == 20

    def test_duplicate_kode_raises(self, sample_barang, sample_kategori):
        payload = {
            "kode_barang": "BRG-001",
            "nama_barang": "Duplikat",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "pcs",
        }
        try:
            barang_service.create_barang(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "sudah digunakan" in str(e)

    def test_empty_kode_raises(self, sample_kategori):
        payload = {
            "kode_barang": "",
            "nama_barang": "Test",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "pcs",
        }
        try:
            barang_service.create_barang(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Kode barang wajib diisi" in str(e)

    def test_empty_nama_raises(self, sample_kategori):
        payload = {
            "kode_barang": "BRG-X",
            "nama_barang": "",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "pcs",
        }
        try:
            barang_service.create_barang(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Nama barang wajib diisi" in str(e)

    def test_invalid_kategori_raises(self):
        payload = {
            "kode_barang": "BRG-X",
            "nama_barang": "Test",
            "kategori_id": str(ObjectId()),
            "satuan": "pcs",
        }
        try:
            barang_service.create_barang(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Kategori tidak valid" in str(e)


class TestUpdateBarang:
    def test_update_success(self, sample_barang, sample_kategori, mock_session):
        payload = {
            "kode_barang": "BRG-001",
            "nama_barang": "Laptop Updated",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "unit",
            "stok_awal": 15,
            "stok_minimum": 3,
        }
        result = barang_service.update_barang(str(sample_barang["_id"]), payload)
        assert result["nama_barang"] == "Laptop Updated"
        assert result["stok_awal"] == 15

    def test_nonexistent_returns_none(self, sample_kategori):
        payload = {
            "kode_barang": "X",
            "nama_barang": "X",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "pcs",
        }
        assert barang_service.update_barang(str(ObjectId()), payload) is None


class TestDeleteBarang:
    def test_delete_success(self, sample_barang, mock_session):
        assert barang_service.delete_barang(str(sample_barang["_id"])) is True

    def test_delete_with_transaksi_raises(self, sample_barang, db):
        db["barang_masuk"].insert_one({
            "no_transaksi": "BM-TEST",
            "detail": [{"barang_id": sample_barang["_id"], "jumlah": 1}],
        })
        try:
            barang_service.delete_barang(str(sample_barang["_id"]))
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "sudah memiliki transaksi" in str(e)

    def test_delete_nonexistent(self):
        assert barang_service.delete_barang(str(ObjectId())) is False


class TestCheckKode:
    def test_available(self, sample_barang):
        assert barang_service.check_kode("BRG-NEW") is True

    def test_taken(self, sample_barang):
        assert barang_service.check_kode("BRG-001") is False

    def test_exclude_self(self, sample_barang):
        assert barang_service.check_kode("BRG-001", str(sample_barang["_id"])) is True

    def test_empty_kode(self):
        assert barang_service.check_kode("") is False


class TestDashboardStats:
    def test_empty_db(self, db):
        result = barang_service.dashboard_stats()
        assert result["total_barang"] == 0
        assert result["total_stok"] == 0

    def test_with_data(self, sample_barang):
        result = barang_service.dashboard_stats()
        assert result["total_barang"] == 1
        assert result["total_stok"] == 10
        assert result["total_nilai"] == 10 * 10000000

    def test_stok_kosong(self, sample_barang_stok_zero):
        result = barang_service.dashboard_stats()
        assert result["stok_kosong"] == 1

    def test_hampir_habis(self, db, sample_kategori):
        bid = ObjectId()
        db["barang"].insert_one({
            "_id": bid,
            "kode_barang": "BRG-MIN",
            "nama_barang": "Stok Min",
            "kategori_id": sample_kategori["_id"],
            "satuan": "pcs",
            "stok_awal": 1,
            "stok_minimum": 5,
            "stok": 1,
            "harga_satuan": 10000,
        })
        result = barang_service.dashboard_stats()
        assert result["hampir_habis"] == 1


class TestListLowStock:
    def test_empty(self, db):
        assert barang_service.list_low_stock() == []

    def test_returns_low_stock(self, sample_barang_stok_zero):
        result = barang_service.list_low_stock()
        assert len(result) == 1

    def test_limit(self, db, sample_kategori):
        for i in range(5):
            db["barang"].insert_one({
                "kode_barang": f"LOW-{i}",
                "nama_barang": f"Low {i}",
                "kategori_id": sample_kategori["_id"],
                "satuan": "pcs",
                "stok_awal": 0,
                "stok_minimum": 10,
                "stok": 0,
            })
        result = barang_service.list_low_stock(limit=3)
        assert len(result) == 3


class TestKategoriDistribution:
    def test_empty(self, db):
        result = barang_service.kategori_distribution()
        assert result["labels"] == []

    def test_with_data(self, sample_barang, sample_kategori):
        result = barang_service.kategori_distribution()
        assert "Elektronik" in result["labels"]
        assert 10 in result["values"]


class TestMonthlyTrend:
    def test_empty(self, db):
        result = barang_service.monthly_trend(months=3)
        assert len(result["labels"]) == 3
        assert all(v == 0 for v in result["masuk"])


class TestTopOutgoingItems:
    def test_empty(self, db):
        result = barang_service.top_outgoing_items()
        assert result["labels"] == []
