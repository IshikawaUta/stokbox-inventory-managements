"""Test untuk services/kategori_service.py."""
from __future__ import annotations

from bson import ObjectId

from services import kategori_service


class TestListKategori:
    def test_empty(self, db):
        result = kategori_service.list_kategori()
        assert result == []

    def test_returns_all(self, sample_kategori):
        result = kategori_service.list_kategori()
        assert len(result) == 1
        assert result[0]["nama_kategori"] == "Elektronik"

    def test_keyword_filter(self, sample_kategori):
        result = kategori_service.list_kategori("Elek")
        assert len(result) == 1

    def test_keyword_no_match(self, sample_kategori):
        result = kategori_service.list_kategori("Makanan")
        assert len(result) == 0


class TestGetKategori:
    def test_valid_id(self, sample_kategori):
        result = kategori_service.get_kategori(str(sample_kategori["_id"]))
        assert result is not None
        assert result["nama_kategori"] == "Elektronik"

    def test_invalid_id(self):
        result = kategori_service.get_kategori("invalid")
        assert result is None

    def test_nonexistent_id(self):
        result = kategori_service.get_kategori(str(ObjectId()))
        assert result is None


class TestCreateKategori:
    def test_create_success(self, db, mock_session):
        result = kategori_service.create_kategori({"nama_kategori": "Makanan"})
        assert result["nama_kategori"] == "Makanan"
        assert result["icon_kategori"] == "bi-box"

    def test_create_with_icon(self, db, mock_session):
        result = kategori_service.create_kategori({
            "nama_kategori": "Minuman",
            "icon_kategori": "bi-cup",
        })
        assert result["icon_kategori"] == "bi-cup"

    def test_empty_name_raises(self, db):
        try:
            kategori_service.create_kategori({"nama_kategori": ""})
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Nama kategori wajib diisi" in str(e)

    def test_duplicate_name_raises(self, sample_kategori):
        try:
            kategori_service.create_kategori({"nama_kategori": "Elektronik"})
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "sudah digunakan" in str(e)

    def test_strips_whitespace(self, db, mock_session):
        result = kategori_service.create_kategori({"nama_kategori": "  ATK  "})
        assert result["nama_kategori"] == "ATK"


class TestUpdateKategori:
    def test_update_name(self, sample_kategori, mock_session):
        result = kategori_service.update_kategori(
            str(sample_kategori["_id"]),
            {"nama_kategori": "Gadget"},
        )
        assert result["nama_kategori"] == "Gadget"

    def test_update_icon(self, sample_kategori, mock_session):
        result = kategori_service.update_kategori(
            str(sample_kategori["_id"]),
            {"icon_kategori": "bi-phone"},
        )
        assert result["icon_kategori"] == "bi-phone"

    def test_nonexistent_returns_none(self):
        result = kategori_service.update_kategori(
            str(ObjectId()), {"nama_kategori": "X"}
        )
        assert result is None

    def test_empty_name_raises(self, sample_kategori):
        try:
            kategori_service.update_kategori(
                str(sample_kategori["_id"]),
                {"nama_kategori": ""},
            )
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Nama kategori wajib diisi" in str(e)


class TestDeleteKategori:
    def test_delete_success(self, sample_kategori, mock_session):
        result = kategori_service.delete_kategori(str(sample_kategori["_id"]))
        assert result is True

    def test_delete_used_by_barang_raises(self, sample_kategori, sample_barang):
        try:
            kategori_service.delete_kategori(str(sample_kategori["_id"]))
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "masih digunakan" in str(e)

    def test_delete_nonexistent(self):
        result = kategori_service.delete_kategori(str(ObjectId()))
        assert result is False
