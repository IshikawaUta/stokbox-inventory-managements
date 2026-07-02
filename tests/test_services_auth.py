"""Test untuk services/auth_service.py."""
from __future__ import annotations

from bson import ObjectId

from services import auth_service


class TestAuthenticate:
    def test_valid_credentials(self, sample_user):
        result = auth_service.authenticate("admin@test.com", "admin123")
        assert result is not None
        assert result["email"] == "admin@test.com"

    def test_wrong_password(self, sample_user):
        result = auth_service.authenticate("admin@test.com", "wrongpassword")
        assert result is None

    def test_nonexistent_email(self, sample_user):
        result = auth_service.authenticate("wrong@test.com", "admin123")
        assert result is None

    def test_inactive_user(self, db, sample_user):
        db["users"].update_one(
            {"_id": sample_user["_id"]},
            {"$set": {"is_active": False}},
        )
        result = auth_service.authenticate("admin@test.com", "admin123")
        assert result is None

    def test_empty_email(self, sample_user):
        result = auth_service.authenticate("", "admin123")
        assert result is None

    def test_empty_password(self, sample_user):
        result = auth_service.authenticate("admin@test.com", "")
        assert result is None

    def test_creates_admin_if_empty(self, db):
        assert db["users"].count_documents({}) == 0
        result = auth_service.authenticate("admin@inventaris.local", "admin123")
        assert result is not None
        assert db["users"].count_documents({}) == 1


class TestListUsers:
    def test_empty_list(self, db):
        result = auth_service.list_users()
        assert result == []

    def test_returns_users(self, sample_user, sample_staff_user):
        result = auth_service.list_users()
        assert len(result) == 2

    def test_sorted_by_created_at(self, sample_user, sample_staff_user):
        result = auth_service.list_users()
        assert result[0]["created_at"] >= result[1]["created_at"]


class TestGetUser:
    def test_valid_id(self, sample_user):
        result = auth_service.get_user(str(sample_user["_id"]))
        assert result is not None
        assert result["email"] == "admin@test.com"

    def test_invalid_id(self):
        result = auth_service.get_user("invalid-id")
        assert result is None

    def test_nonexistent_id(self):
        result = auth_service.get_user(str(ObjectId()))
        assert result is None


class TestCreateUser:
    def test_create_success(self, db, mock_session):
        payload = {
            "name": "New User",
            "email": "new@test.com",
            "password": "password123",
            "role": "staff",
        }
        result = auth_service.create_user(payload)
        assert result["name"] == "New User"
        assert result["email"] == "new@test.com"
        assert result["role"] == "staff"

    def test_create_admin(self, db, mock_session):
        payload = {
            "name": "New Admin",
            "email": "admin2@test.com",
            "password": "password123",
            "role": "admin",
        }
        result = auth_service.create_user(payload)
        assert result["role"] == "admin"

    def test_duplicate_email_raises(self, sample_user):
        payload = {
            "name": "Duplicate",
            "email": "admin@test.com",
            "password": "password123",
            "role": "staff",
        }
        try:
            auth_service.create_user(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Email sudah digunakan" in str(e)

    def test_empty_name_raises(self, db):
        payload = {
            "name": "",
            "email": "test@test.com",
            "password": "password123",
            "role": "staff",
        }
        try:
            auth_service.create_user(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Nama wajib diisi" in str(e)

    def test_invalid_email_raises(self, db):
        payload = {
            "name": "Test",
            "email": "bukan-email",
            "password": "password123",
            "role": "staff",
        }
        try:
            auth_service.create_user(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Format email tidak valid" in str(e)

    def test_short_password_raises(self, db):
        payload = {
            "name": "Test",
            "email": "test@test.com",
            "password": "12345",
            "role": "staff",
        }
        try:
            auth_service.create_user(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "minimal 6 karakter" in str(e)

    def test_invalid_role_raises(self, db):
        payload = {
            "name": "Test",
            "email": "test@test.com",
            "password": "password123",
            "role": "superadmin",
        }
        try:
            auth_service.create_user(payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Role harus admin atau staff" in str(e)


class TestUpdateUser:
    def test_update_name(self, sample_user, mock_session):
        result = auth_service.update_user(
            str(sample_user["_id"]), {"name": "Updated Name"}
        )
        assert result["name"] == "Updated Name"

    def test_update_email(self, sample_user, mock_session):
        result = auth_service.update_user(
            str(sample_user["_id"]), {"email": "updated@test.com"}
        )
        assert result["email"] == "updated@test.com"

    def test_update_role(self, sample_user, mock_session):
        result = auth_service.update_user(
            str(sample_user["_id"]), {"role": "staff"}
        )
        assert result["role"] == "staff"

    def test_update_password(self, sample_user, mock_session):
        result = auth_service.update_user(
            str(sample_user["_id"]), {"password": "newpassword123"}
        )
        assert result is not None
        assert verify_password("newpassword123", result["password"])

    def test_invalid_id_returns_none(self):
        result = auth_service.update_user("invalid", {"name": "Test"})
        assert result is None

    def test_nonexistent_id_returns_none(self):
        result = auth_service.update_user(str(ObjectId()), {"name": "Test"})
        assert result is None


def verify_password(password, stored):
    from utils.security import verify_password as vp
    return vp(password, stored)


class TestDeleteUser:
    def test_delete_existing(self, sample_user, mock_session):
        result = auth_service.delete_user(str(sample_user["_id"]))
        assert result is True

    def test_delete_nonexistent(self):
        result = auth_service.delete_user(str(ObjectId()))
        assert result is False

    def test_invalid_id(self):
        result = auth_service.delete_user("invalid")
        assert result is False


class TestToggleActive:
    def test_deactivate(self, sample_user, mock_session):
        result = auth_service.toggle_active(str(sample_user["_id"]))
        assert result["is_active"] is False

    def test_reactivate(self, db, sample_user, mock_session):
        db["users"].update_one(
            {"_id": sample_user["_id"]}, {"$set": {"is_active": False}}
        )
        result = auth_service.toggle_active(str(sample_user["_id"]))
        assert result["is_active"] is True

    def test_nonexistent(self):
        result = auth_service.toggle_active(str(ObjectId()))
        assert result is None


class TestUpdateProfile:
    def test_update_name(self, sample_user):
        result = auth_service.update_profile(
            str(sample_user["_id"]), {"name": "New Name"}
        )
        assert result["name"] == "New Name"

    def test_nonexistent(self):
        result = auth_service.update_profile(str(ObjectId()), {"name": "X"})
        assert result is None


class TestChangePassword:
    def test_correct_old_password(self, sample_user):
        payload = {
            "old_password": "admin123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        result = auth_service.change_password(str(sample_user["_id"]), payload)
        assert result is not None

    def test_wrong_old_password(self, sample_user):
        payload = {
            "old_password": "wrongold",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        try:
            auth_service.change_password(str(sample_user["_id"]), payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Password lama salah" in str(e)

    def test_mismatched_confirm(self, sample_user):
        payload = {
            "old_password": "admin123",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword",
        }
        try:
            auth_service.change_password(str(sample_user["_id"]), payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "Konfirmasi password tidak cocok" in str(e)

    def test_short_new_password(self, sample_user):
        payload = {
            "old_password": "admin123",
            "new_password": "12345",
            "confirm_password": "12345",
        }
        try:
            auth_service.change_password(str(sample_user["_id"]), payload)
            assert False, "Seharusnya raise ValueError"
        except ValueError as e:
            assert "minimal 6 karakter" in str(e)
