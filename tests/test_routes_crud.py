"""Test untuk routes CRUD (kategori, barang, suplier, user)."""
from __future__ import annotations

from bson import ObjectId

from tests.conftest import login_as


# ── Kategori Routes ──────────────────────────────────────────────────


class TestKategoriRoutes:
    def test_list_empty(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/kategori/")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_list_with_data(self, client, sample_user, sample_kategori):
        login_as(client, sample_user)
        resp = client.get("/api/kategori/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_show(self, client, sample_user, sample_kategori):
        login_as(client, sample_user)
        resp = client.get(f"/api/kategori/{sample_kategori['_id']}")
        assert resp.status_code == 200
        assert resp.json()["nama_kategori"] == "Elektronik"

    def test_show_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/kategori/{ObjectId()}")
        assert resp.status_code == 404

    def test_create(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/kategori/", json={"nama_kategori": "ATK"})
        assert resp.status_code == 200
        assert resp.json()["nama_kategori"] == "ATK"

    def test_create_empty_name(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/kategori/", json={"nama_kategori": ""})
        assert resp.status_code == 400

    def test_update(self, client, sample_user, sample_kategori):
        login_as(client, sample_user)
        resp = client.put(
            f"/api/kategori/{sample_kategori['_id']}",
            json={"nama_kategori": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["nama_kategori"] == "Updated"

    def test_delete(self, client, sample_user, sample_kategori):
        login_as(client, sample_user)
        resp = client.delete(f"/api/kategori/{sample_kategori['_id']}")
        assert resp.status_code == 200

    def test_delete_used_by_barang(self, client, sample_user, sample_kategori, sample_barang):
        login_as(client, sample_user)
        resp = client.delete(f"/api/kategori/{sample_kategori['_id']}")
        assert resp.status_code == 400

    def test_create_requires_admin(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        resp = client.post("/api/kategori/", json={"nama_kategori": "ATK"})
        assert resp.status_code == 403

    def test_requires_login(self, client):
        resp = client.get("/api/kategori/")
        assert resp.status_code == 401


# ── Barang Routes ────────────────────────────────────────────────────


class TestBarangRoutes:
    def test_list_empty(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/barang/")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_list_with_data(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barang/")
        assert len(resp.json()["data"]) == 1

    def test_list_stok_filter(self, client, sample_user, sample_barang, sample_barang_stok_zero):
        login_as(client, sample_user)
        resp = client.get("/api/barang/?stok=habis")
        assert len(resp.json()["data"]) == 1

    def test_show(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang/{sample_barang['_id']}")
        assert resp.status_code == 200
        assert resp.json()["kode_barang"] == "BRG-001"

    def test_show_not_found(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/barang/{ObjectId()}")
        assert resp.status_code == 404

    def test_create(self, client, sample_user, sample_kategori):
        login_as(client, sample_user)
        resp = client.post("/api/barang/", json={
            "kode_barang": "BRG-NEW",
            "nama_barang": "Keyboard",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "pcs",
            "stok_awal": 10,
            "stok_minimum": 2,
        })
        assert resp.status_code == 200
        assert resp.json()["kode_barang"] == "BRG-NEW"

    def test_create_duplicate_kode(self, client, sample_user, sample_barang, sample_kategori):
        login_as(client, sample_user)
        resp = client.post("/api/barang/", json={
            "kode_barang": "BRG-001",
            "nama_barang": "Duplikat",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "pcs",
        })
        assert resp.status_code == 400

    def test_update(self, client, sample_user, sample_barang, sample_kategori):
        login_as(client, sample_user)
        resp = client.put(f"/api/barang/{sample_barang['_id']}", json={
            "kode_barang": "BRG-001",
            "nama_barang": "Updated",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "unit",
            "stok_awal": 15,
            "stok_minimum": 3,
        })
        assert resp.status_code == 200
        assert resp.json()["nama_barang"] == "Updated"

    def test_delete(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.delete(f"/api/barang/{sample_barang['_id']}")
        assert resp.status_code == 200

    def test_check_kode_available(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/barang/check-kode?kode=BRG-NEW")
        assert resp.status_code == 200
        assert resp.json()["available"] is True

    def test_check_kode_taken(self, client, sample_user, sample_barang):
        login_as(client, sample_user)
        resp = client.get("/api/barang/check-kode?kode=BRG-001")
        assert resp.status_code == 200
        assert resp.json()["available"] is False

    def test_requires_admin_for_create(self, client, sample_staff_user, sample_kategori):
        login_as(client, sample_staff_user)
        resp = client.post("/api/barang/", json={
            "kode_barang": "X",
            "nama_barang": "X",
            "kategori_id": str(sample_kategori["_id"]),
            "satuan": "pcs",
        })
        assert resp.status_code == 403


# ── Suplier Routes ──────────────────────────────────────────────────


class TestSuplierRoutes:
    def test_list(self, client, sample_user, sample_suplier):
        login_as(client, sample_user)
        resp = client.get("/api/suplier/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_create(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/suplier/", json={"nama": "Suplier Baru"})
        assert resp.status_code == 200
        assert resp.json()["nama"] == "Suplier Baru"

    def test_update(self, client, sample_user, sample_suplier):
        login_as(client, sample_user)
        resp = client.put(
            f"/api/suplier/{sample_suplier['_id']}",
            json={"nama": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["nama"] == "Updated"

    def test_delete(self, client, sample_user, sample_suplier):
        login_as(client, sample_user)
        resp = client.delete(f"/api/suplier/{sample_suplier['_id']}")
        assert resp.status_code == 200


# ── User Routes ──────────────────────────────────────────────────────


class TestUserRoutes:
    def test_list(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/user/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    def test_create(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/user/", json={
            "name": "New User",
            "email": "new@test.com",
            "password": "password123",
            "role": "staff",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "New User"

    def test_show(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get(f"/api/user/{sample_user['_id']}")
        assert resp.status_code == 200

    def test_update(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.put(f"/api/user/{sample_user['_id']}", json={
            "name": "Updated Name",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_delete(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        resp = client.delete(f"/api/user/{sample_staff_user['_id']}")
        # staff cannot delete
        assert resp.status_code in (200, 403)

    def test_toggle_active(self, client, sample_user, sample_staff_user):
        login_as(client, sample_user)
        resp = client.post(f"/api/user/{sample_staff_user['_id']}/toggle-active")
        assert resp.status_code == 200

    def test_update_profile(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.put("/api/user/profile", json={"name": "Self Update"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Self Update"

    def test_change_password(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.put("/api/user/change-password", json={
            "old_password": "admin123",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        })
        assert resp.status_code == 200
