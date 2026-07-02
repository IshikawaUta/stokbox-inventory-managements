"""Test untuk services/suplier_service.py."""
from __future__ import annotations

from bson import ObjectId

from services import suplier_service


class TestListSuplier:
    def test_empty(self, db):
        assert suplier_service.list_suplier() == []

    def test_returns_all(self, sample_suplier):
        result = suplier_service.list_suplier()
        assert len(result) == 1
        assert result[0]["nama"] == "Suplier A"

    def test_keyword_filter(self, sample_suplier):
        assert len(suplier_service.list_suplier("Suplier")) == 1
        assert len(suplier_service.list_suplier("XYZ")) == 0


class TestGetSuplier:
    def test_valid_id(self, sample_suplier):
        result = suplier_service.get_suplier(str(sample_suplier["_id"]))
        assert result is not None
        assert result["nama"] == "Suplier A"

    def test_invalid_id(self):
        assert suplier_service.get_suplier("invalid") is None

    def test_nonexistent(self):
        assert suplier_service.get_suplier(str(ObjectId())) is None


class TestCreateSuplier:
    def test_create_success(self, db, mock_session):
        payload = {
            "nama": "Suplier B",
            "no_hp": "081111111111",
            "email": "b@test.com",
            "alamat": "Bandung",
            "perusahaan": "PT. B",
        }
        result = suplier_service.create_suplier(payload)
        assert result["nama"] == "Suplier B"

    def test_empty_name_raises(self, db):
        try:
            suplier_service.create_suplier({"nama": ""})
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Nama suplier wajib diisi" in str(e)

    def test_strips_whitespace(self, db, mock_session):
        result = suplier_service.create_suplier({"nama": "  Test  "})
        assert result["nama"] == "Test"


class TestUpdateSuplier:
    def test_update_fields(self, sample_suplier, mock_session):
        result = suplier_service.update_suplier(
            str(sample_suplier["_id"]),
            {"nama": "Suplier Updated", "no_hp": "089999999999"},
        )
        assert result["nama"] == "Suplier Updated"
        assert result["no_hp"] == "089999999999"

    def test_nonexistent_returns_none(self):
        result = suplier_service.update_suplier(str(ObjectId()), {"nama": "X"})
        assert result is None

    def test_empty_name_raises(self, sample_suplier):
        try:
            suplier_service.update_suplier(
                str(sample_suplier["_id"]), {"nama": ""}
            )
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Nama suplier wajib diisi" in str(e)


class TestDeleteSuplier:
    def test_delete_success(self, sample_suplier, mock_session):
        result = suplier_service.delete_suplier(str(sample_suplier["_id"]))
        assert result is True

    def test_delete_with_transaksi_raises(self, sample_suplier, sample_barang, db):
        db["barang_masuk"].insert_one({
            "no_transaksi": "BM-TEST",
            "suplier_id": sample_suplier["_id"],
            "detail": [],
        })
        try:
            suplier_service.delete_suplier(str(sample_suplier["_id"]))
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "masih memiliki transaksi" in str(e)

    def test_delete_nonexistent(self):
        assert suplier_service.delete_suplier(str(ObjectId())) is False
