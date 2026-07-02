"""Unit test untuk utils/helpers.py."""
from __future__ import annotations

from datetime import datetime, date, timezone
from bson import ObjectId

from utils.helpers import (
    parse_object_id,
    serialize_doc,
    serialize_docs,
    utcnow,
    parse_date,
)


class TestParseObjectId:
    def test_valid_string(self):
        oid = ObjectId()
        result = parse_object_id(str(oid))
        assert result == oid

    def test_already_objectid(self):
        oid = ObjectId()
        result = parse_object_id(oid)
        assert result == oid

    def test_none_returns_none(self):
        assert parse_object_id(None) is None

    def test_empty_string_returns_none(self):
        assert parse_object_id("") is None

    def test_invalid_string_returns_none(self):
        assert parse_object_id("bukan-objectid") is None

    def test_non_string_returns_none(self):
        assert parse_object_id(123) is None


class TestSerializeDoc:
    def test_none_returns_none(self):
        assert serialize_doc(None) is None

    def test_converts_id_to_string(self):
        oid = ObjectId()
        doc = {"_id": oid, "nama": "Test"}
        result = serialize_doc(doc)
        assert result["id"] == str(oid)
        assert "_id" not in result
        assert result["nama"] == "Test"

    def test_converts_datetime(self):
        dt = datetime(2025, 1, 15, 10, 30, 0)
        doc = {"created_at": dt}
        result = serialize_doc(doc)
        assert result["created_at"] == "2025-01-15T10:30:00"

    def test_converts_date(self):
        d = date(2025, 1, 15)
        doc = {"tanggal": d}
        result = serialize_doc(doc)
        assert result["tanggal"] == "2025-01-15"

    def test_converts_nested_objectid(self):
        oid = ObjectId()
        doc = {"detail": {"barang_id": oid}}
        result = serialize_doc(doc)
        assert result["detail"]["barang_id"] == str(oid)

    def test_converts_list_of_dicts(self):
        oid = ObjectId()
        doc = {"items": [{"_id": oid, "nama": "A"}]}
        result = serialize_doc(doc)
        assert result["items"][0]["id"] == str(oid)

    def test_preserves_string(self):
        doc = {"nama": "Test"}
        result = serialize_doc(doc)
        assert result["nama"] == "Test"

    def test_preserves_int(self):
        doc = {"stok": 10}
        result = serialize_doc(doc)
        assert result["stok"] == 10

    def test_preserves_none(self):
        doc = {"foto": None}
        result = serialize_doc(doc)
        assert result["foto"] is None


class TestSerializeDocs:
    def test_empty_list(self):
        assert serialize_docs([]) == []

    def test_multiple_docs(self):
        oid1, oid2 = ObjectId(), ObjectId()
        docs = [{"_id": oid1, "a": 1}, {"_id": oid2, "b": 2}]
        result = serialize_docs(docs)
        assert len(result) == 2
        assert result[0]["id"] == str(oid1)
        assert result[1]["id"] == str(oid2)


class TestUtcnow:
    def test_returns_datetime(self):
        result = utcnow()
        assert isinstance(result, datetime)

    def test_is_naive(self):
        result = utcnow()
        assert result.tzinfo is None

    def test_is_utc(self):
        result = utcnow()
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        diff = abs((now_utc - result).total_seconds())
        assert diff < 2


class TestParseDate:
    def test_valid_iso_string(self):
        result = parse_date("2025-01-15")
        assert result == date(2025, 1, 15)

    def test_empty_string_returns_none(self):
        assert parse_date("") is None

    def test_none_returns_none(self):
        assert parse_date(None) is None

    def test_datetime_returns_date(self):
        dt = datetime(2025, 1, 15, 10, 30)
        result = parse_date(dt)
        assert result == date(2025, 1, 15)

    def test_date_object_returns_itself(self):
        d = date(2025, 1, 15)
        result = parse_date(d)
        assert result == d

    def test_invalid_string_returns_none(self):
        assert parse_date("bukan-tanggal") is None

    def test_datetime_string(self):
        result = parse_date("2025-01-15T10:30:00")
        assert result == date(2025, 1, 15)
