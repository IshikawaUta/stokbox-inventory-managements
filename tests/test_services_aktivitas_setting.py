"""Test untuk services/aktivitas_service.py dan services/setting_service.py."""
from __future__ import annotations

from bson import ObjectId

from services import aktivitas_service, setting_service


class TestLogAktivitas:
    def test_log_success(self, db):
        aktivitas_service.log(
            user_id="uid",
            user_name="Admin",
            user_role="admin",
            aksi="create",
            entitas="barang",
            entitas_id="123",
            deskripsi="Membuat barang",
        )
        assert db["aktivitas"].count_documents({}) == 1

    def test_log_with_detail(self, db):
        aktivitas_service.log(
            user_id="uid",
            user_name="Admin",
            user_role="admin",
            aksi="import",
            entitas="backup",
            entitas_id="",
            deskripsi="Import data",
            detail={"count": 10},
        )
        doc = db["aktivitas"].find_one()
        assert doc["detail"] == {"count": 10}


class TestListAktivitas:
    def test_empty(self, db):
        result = aktivitas_service.list_aktivitas()
        assert result["data"] == []
        assert result["total"] == 0

    def test_with_data(self, db):
        aktivitas_service.log("u", "A", "admin", "create", "barang", "1", "Test")
        result = aktivitas_service.list_aktivitas()
        assert len(result["data"]) == 1
        assert result["total"] == 1

    def test_filter_entitas(self, db):
        aktivitas_service.log("u", "A", "admin", "create", "barang", "1", "Test")
        aktivitas_service.log("u", "A", "admin", "create", "kategori", "2", "Test")
        result = aktivitas_service.list_aktivitas(entitas="barang")
        assert len(result["data"]) == 1

    def test_filter_aksi(self, db):
        aktivitas_service.log("u", "A", "admin", "create", "barang", "1", "Test")
        aktivitas_service.log("u", "A", "admin", "delete", "barang", "2", "Test")
        result = aktivitas_service.list_aktivitas(aksi="create")
        assert len(result["data"]) == 1

    def test_pagination(self, db):
        for i in range(10):
            aktivitas_service.log("u", "A", "admin", "create", "barang", str(i), f"Test {i}")
        result = aktivitas_service.list_aktivitas(page=1, per_page=5)
        assert len(result["data"]) == 5
        assert result["total"] == 10
        assert result["total_pages"] == 2

    def test_keyword_search(self, db):
        aktivitas_service.log("u", "Admin", "admin", "create", "barang", "1", "Buat baru")
        aktivitas_service.log("u", "User", "user", "update", "kategori", "2", "Ubah data")
        result = aktivitas_service.list_aktivitas(keyword="Admin")
        assert len(result["data"]) == 1
        assert result["data"][0]["user_name"] == "Admin"


class TestGetAktivitas:
    def test_valid_id(self, db):
        from utils.helpers import utcnow
        result = db["aktivitas"].insert_one({
            "user_id": "u", "user_name": "A", "user_role": "admin",
            "aksi": "create", "entitas": "barang", "entitas_id": "1",
            "deskripsi": "Test", "detail": None, "ip_address": "",
            "created_at": utcnow().isoformat(),
        })
        got = aktivitas_service.get_aktivitas(str(result.inserted_id))
        assert got is not None

    def test_nonexistent(self):
        assert aktivitas_service.get_aktivitas(str(ObjectId())) is None

    def test_invalid_id(self):
        assert aktivitas_service.get_aktivitas("invalid") is None


# ── Setting Service ──────────────────────────────────────────────────


class TestGetSettings:
    def test_returns_defaults(self, db):
        result = setting_service.get_settings()
        assert result["nama_aplikasi"] == "InventarisKu"

    def test_with_db_data(self, sample_setting):
        result = setting_service.get_settings()
        assert result["nama_aplikasi"] == "InventarisKu"
        assert result["nama_perusahaan"] == "PT. Test"


class TestGetSetting:
    def test_existing_key(self, sample_setting):
        result = setting_service.get_setting("nama_aplikasi")
        assert result == "InventarisKu"

    def test_nonexistent_key(self, db):
        result = setting_service.get_setting("nonexistent", default="fallback")
        assert result == "fallback"


class TestUpdateSettings:
    def test_update_success(self, db):
        result = setting_service.update_settings({
            "nama_aplikasi": "New App",
            "tagline": "New Tagline",
        })
        assert result["nama_aplikasi"] == "New App"
        assert result["tagline"] == "New Tagline"

    def test_ignores_unknown_keys(self, db):
        result = setting_service.update_settings({"unknown_key": "value"})
        assert "unknown_key" not in result
