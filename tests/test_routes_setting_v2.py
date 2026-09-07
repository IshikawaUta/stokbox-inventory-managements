"""Test tambahan untuk routes/api_setting.py — get, update, upload_asset."""
from __future__ import annotations

import io
from unittest.mock import patch

from tests.conftest import login_as


class TestSettingGet:
    def test_get_settings(self, client, sample_user, sample_setting):
        login_as(client, sample_user)
        resp = client.get("/api/setting/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "nama_aplikasi" in data
        assert "nama_perusahaan" in data

    def test_get_settings_no_data(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.get("/api/setting/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["nama_aplikasi"] == "InventarisKu"

    def test_get_settings_requires_login(self, client):
        resp = client.get("/api/setting/")
        assert resp.status_code == 401


class TestSettingUpdate:
    def test_update_settings(self, client, sample_user, sample_setting):
        login_as(client, sample_user)
        resp = client.put("/api/setting/", json={
            "nama_aplikasi": "New App Name",
            "tagline": "New Tagline",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["nama_aplikasi"] == "New App Name"
        assert resp.json()["data"]["tagline"] == "New Tagline"

    def test_update_settings_ignores_unknown_keys(self, client, sample_user, sample_setting):
        login_as(client, sample_user)
        resp = client.put("/api/setting/", json={
            "nama_aplikasi": "Updated",
            "unknown_key": "should be ignored",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["nama_aplikasi"] == "Updated"

    def test_update_settings_requires_admin(self, client, sample_staff_user, sample_setting):
        login_as(client, sample_staff_user)
        resp = client.put("/api/setting/", json={"nama_aplikasi": "Should Fail"})
        assert resp.status_code == 403

    def test_update_settings_requires_login(self, client):
        resp = client.put("/api/setting/", json={"nama_aplikasi": "Test"})
        assert resp.status_code == 401


class TestSettingUploadAsset:
    def test_upload_logo(self, client, sample_user):
        login_as(client, sample_user)
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        with patch("config.cloudinary_client.upload_file") as mock_upload:
            mock_upload.return_value = {"secure_url": "https://res.cloudinary.com/test/logo.png"}
            resp = client.post(
                "/api/setting/upload-asset?kind=logo",
                files={"file": ("logo.png", fake_img, "image/png")},
            )
            assert resp.status_code == 200

    def test_upload_favicon(self, client, sample_user):
        login_as(client, sample_user)
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        with patch("config.cloudinary_client.upload_file") as mock_upload:
            mock_upload.return_value = {"secure_url": "https://res.cloudinary.com/test/favicon.png"}
            resp = client.post(
                "/api/setting/upload-asset?kind=favicon",
                files={"file": ("favicon.png", fake_img, "image/png")},
            )
            assert resp.status_code == 200

    def test_upload_asset_invalid_kind(self, client, sample_user):
        login_as(client, sample_user)
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        resp = client.post(
            "/api/setting/upload-asset?kind=invalid",
            files={"file": ("icon.png", fake_img, "image/png")},
        )
        assert resp.status_code == 400

    def test_upload_asset_no_file(self, client, sample_user):
        login_as(client, sample_user)
        resp = client.post("/api/setting/upload-asset?kind=logo")
        assert resp.status_code in (400, 422)

    def test_upload_asset_requires_admin(self, client, sample_staff_user):
        login_as(client, sample_staff_user)
        resp = client.post(
            "/api/setting/upload-asset?kind=logo",
            files={"file": ("logo.png", io.BytesIO(b"data"), "image/png")},
        )
        assert resp.status_code == 403

    def test_upload_asset_requires_login(self, client):
        resp = client.post(
            "/api/setting/upload-asset?kind=logo",
            files={"file": ("logo.png", io.BytesIO(b"data"), "image/png")},
        )
        assert resp.status_code == 401

    def test_upload_asset_with_logo_fallback_local(self, client, sample_user):
        login_as(client, sample_user)
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        with patch("config.cloudinary_client.upload_file", side_effect=Exception("Cloudinary error")):
            resp = client.post(
                "/api/setting/upload-asset?kind=logo",
                files={"file": ("logo.png", fake_img, "image/png")},
            )
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert "logo" in data
