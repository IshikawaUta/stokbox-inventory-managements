"""Test untuk routes/auth.py."""
from __future__ import annotations

from tests.conftest import login_as


class TestLogin:
    def test_login_success(self, client, sample_user):
        resp = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "Login berhasil" in data["message"]
        assert data["user"]["email"] == "admin@test.com"

    def test_login_wrong_password(self, client, sample_user):
        resp = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "wrong",
        })
        assert resp.status_code == 401

    def test_login_nonexistent(self, client, sample_user):
        resp = client.post("/auth/login", json={
            "email": "wrong@test.com",
            "password": "admin123",
        })
        assert resp.status_code == 401

    def test_login_empty_fields(self, client, sample_user):
        resp = client.post("/auth/login", json={
            "email": "",
            "password": "",
        })
        assert resp.status_code == 400

    def test_login_inactive_user(self, client, db, sample_user):
        db["users"].update_one(
            {"_id": sample_user["_id"]},
            {"$set": {"is_active": False}},
        )
        resp = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123",
        })
        assert resp.status_code == 401


class TestLogout:
    def test_logout_post(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/auth/logout")
        assert resp.status_code == 200

    def test_logout_get(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/auth/logout")
        assert resp.status_code in (200, 302)


class TestMe:
    def test_me_logged_in(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == "admin@test.com"

    def test_me_not_logged_in(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401
