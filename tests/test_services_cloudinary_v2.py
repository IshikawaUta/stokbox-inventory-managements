"""Test tambahan untuk services/cloudinary_service.py."""
from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services import cloudinary_service


class TestSaveLocal:
    def test_save_local_with_file_obj(self, tmp_path):
        upload_dir = tmp_path / "static" / "uploads" / "barang"
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_obj = io.BytesIO(b"test content")
        result = cloudinary_service._save_local(file_obj, "barang", "test_item", ext="png")
        assert "url" in result
        assert result["public_id"] is None

    def test_save_local_with_bytes(self, tmp_path):
        upload_dir = tmp_path / "static" / "uploads" / "users"
        upload_dir.mkdir(parents=True, exist_ok=True)
        result = cloudinary_service._save_local(b"test content", "users", "user_test", ext="jpg")
        assert "url" in result


class TestVerifyUrlAccessible:
    def test_verify_url_empty(self):
        assert cloudinary_service._verify_url_accessible("") is False

    def test_verify_url_not_http(self):
        assert cloudinary_service._verify_url_accessible("ftp://example.com") is False

    def test_verify_url_none(self):
        assert cloudinary_service._verify_url_accessible(None) is False

    @patch("urllib.request.urlopen")
    def test_verify_url_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        assert cloudinary_service._verify_url_accessible("https://example.com/test.jpg") is True

    @patch("urllib.request.urlopen")
    def test_verify_url_failure(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection failed")
        assert cloudinary_service._verify_url_accessible("https://example.com/test.jpg") is False

    @patch("urllib.request.urlopen")
    def test_verify_url_redirect(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 301
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        assert cloudinary_service._verify_url_accessible("https://example.com/test.jpg") is False


class TestIsConfigured:
    def test_is_configured_not_set(self):
        with patch("config.cloudinary_client._current_creds", return_value=("", "", "")):
            from config.cloudinary_client import is_configured
            assert is_configured() is False

    def test_is_configured_partial(self):
        with patch("config.cloudinary_client._current_creds", return_value=("cloud", "", "")):
            from config.cloudinary_client import is_configured
            assert is_configured() is False

    def test_is_configured_full(self):
        with patch("config.cloudinary_client._current_creds", return_value=("cloud", "key", "secret")):
            from config.cloudinary_client import is_configured
            assert is_configured() is True


class TestUploadBarangPhoto:
    def test_upload_not_configured(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=False), \
             patch.object(cloudinary_service, "_save_local") as mock_save:
            mock_save.return_value = {"url": "/static/uploads/barang/test.jpg", "public_id": None}
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001")
            assert result["url"] == "/static/uploads/barang/test.jpg"

    def test_upload_configured_success(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=True), \
             patch.object(cloudinary_service, "configure"), \
             patch.object(cloudinary_service, "upload_image") as mock_upload, \
             patch.object(cloudinary_service, "_verify_url_accessible", return_value=True), \
             patch.object(cloudinary_service, "_save_local") as mock_save:
            mock_upload.return_value = {
                "public_id": "barang_brg-001",
                "secure_url": "https://res.cloudinary.com/test/image/upload/barang_brg-001.jpg",
                "width": 100,
                "height": 100,
            }
            mock_save.return_value = {"url": "/static/uploads/barang/brg-001.jpg"}
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001")
            assert result["public_id"] == "barang_brg-001"

    def test_upload_ghost_upload_fallback(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=True), \
             patch.object(cloudinary_service, "configure"), \
             patch.object(cloudinary_service, "upload_image") as mock_upload, \
             patch.object(cloudinary_service, "_verify_url_accessible", return_value=False), \
             patch.object(cloudinary_service, "_save_local") as mock_save:
            mock_upload.return_value = {
                "public_id": "test",
                "secure_url": "https://example.com/test.jpg",
            }
            mock_save.return_value = {"url": "/static/uploads/barang/test.jpg"}
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001")
            assert result["public_id"] is None
            assert result["url"] == "/static/uploads/barang/test.jpg"

    def test_upload_cloudinary_error_fallback(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=True), \
             patch.object(cloudinary_service, "configure"), \
             patch.object(cloudinary_service, "upload_image", side_effect=Exception("API Error")), \
             patch.object(cloudinary_service, "_save_local") as mock_save:
            mock_save.return_value = {"url": "/static/uploads/barang/test.jpg"}
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001")
            assert result["url"] == "/static/uploads/barang/test.jpg"

    def test_upload_with_filename_ext(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=False), \
             patch.object(cloudinary_service, "_save_local") as mock_save:
            mock_save.return_value = {"url": "/static/uploads/barang/test.png"}
            result = cloudinary_service.upload_barang_photo(file_obj, "BRG-001", filename="photo.png", ext="png")
            assert "png" in result["url"]

    def test_upload_no_cloudinary_no_local(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=True), \
             patch.object(cloudinary_service, "configure"), \
             patch.object(cloudinary_service, "upload_image", side_effect=Exception("API Error")), \
             patch.object(cloudinary_service, "_save_local", return_value=None):
            with pytest.raises(Exception):
                cloudinary_service.upload_barang_photo(file_obj, "BRG-001")


class TestUploadUserPhoto:
    def test_upload_not_configured(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=False), \
             patch.object(cloudinary_service, "_save_local") as mock_save:
            mock_save.return_value = {"url": "/static/uploads/users/user_test_at_test.com.jpg"}
            result = cloudinary_service.upload_user_photo(file_obj, "test@test.com")
            assert "url" in result

    def test_upload_configured_success(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=True), \
             patch.object(cloudinary_service, "configure"), \
             patch.object(cloudinary_service, "upload_image") as mock_upload:
            mock_upload.return_value = {
                "public_id": "user_test",
                "secure_url": "https://res.cloudinary.com/test/image/upload/user_test.jpg",
            }
            result = cloudinary_service.upload_user_photo(file_obj, "test@test.com")
            assert result["public_id"] == "user_test"

    def test_upload_configured_error_fallback(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=True), \
             patch.object(cloudinary_service, "configure"), \
             patch.object(cloudinary_service, "upload_image", side_effect=Exception("Error")), \
             patch.object(cloudinary_service, "_save_local") as mock_save:
            mock_save.return_value = {"url": "/static/uploads/users/user_test.jpg"}
            result = cloudinary_service.upload_user_photo(file_obj, "test@test.com")
            assert result["url"] == "/static/uploads/users/user_test.jpg"


class TestUploadAppLogo:
    def test_upload_not_configured(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=False), \
             patch.object(cloudinary_service, "_save_local") as mock_save:
            mock_save.return_value = {"url": "/static/uploads/settings/app_logo.png"}
            result = cloudinary_service.upload_app_logo(file_obj, "logo")
            assert result["url"] == "/static/uploads/settings/app_logo.png"

    def test_upload_configured_success(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=True), \
             patch.object(cloudinary_service, "configure"), \
             patch.object(cloudinary_service, "upload_image") as mock_upload:
            mock_upload.return_value = {
                "public_id": "app_logo",
                "secure_url": "https://res.cloudinary.com/test/image/upload/app_logo.png",
            }
            result = cloudinary_service.upload_app_logo(file_obj, "logo")
            assert result["public_id"] == "app_logo"

    def test_upload_configured_error_fallback(self):
        file_obj = io.BytesIO(b"test content")
        with patch.object(cloudinary_service, "is_configured", return_value=True), \
             patch.object(cloudinary_service, "configure"), \
             patch.object(cloudinary_service, "upload_image", side_effect=Exception("Error")), \
             patch.object(cloudinary_service, "_save_local") as mock_save:
            mock_save.return_value = {"url": "/static/uploads/settings/app_logo.png"}
            result = cloudinary_service.upload_app_logo(file_obj, "logo")
            assert result["url"] == "/static/uploads/settings/app_logo.png"


class TestRemovePhoto:
    def test_remove_photo_none(self):
        cloudinary_service.remove_photo(None)

    def test_remove_photo_empty(self):
        cloudinary_service.remove_photo("")

    def test_remove_photo_not_configured(self):
        with patch.object(cloudinary_service, "is_configured", return_value=False):
            cloudinary_service.remove_photo("test_public_id")

    def test_remove_photo_configured(self):
        with patch.object(cloudinary_service, "is_configured", return_value=True), \
             patch.object(cloudinary_service, "configure"), \
             patch.object(cloudinary_service, "delete_image") as mock_delete:
            cloudinary_service.remove_photo("test_public_id")
            mock_delete.assert_called_once_with("test_public_id")

    def test_remove_photo_configured_error(self):
        with patch.object(cloudinary_service, "is_configured", return_value=True), \
             patch.object(cloudinary_service, "configure"), \
             patch.object(cloudinary_service, "delete_image", side_effect=Exception("Error")):
            cloudinary_service.remove_photo("test_public_id")
