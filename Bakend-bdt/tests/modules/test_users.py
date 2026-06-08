"""User profile endpoint tests."""

import pytest
from httpx import AsyncClient


class TestGetProfile:
    """Tests for GET /users/profile."""

    @pytest.mark.asyncio
    async def test_get_profile_success(self, client: AsyncClient, test_user):
        """Test getting user profile."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get profile
        response = await client.get(
            "/users/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "test@example.com"
        assert data["data"]["name"] == "Test Trader"
        assert "password_hash" not in data["data"]


class TestUpdateProfile:
    """Tests for PUT /users/profile."""

    @pytest.mark.asyncio
    async def test_update_profile_success(self, client: AsyncClient, test_user):
        """Test updating user profile."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Update profile
        response = await client.put(
            "/users/profile",
            json={
                "name": "Updated Trader",
                "language": "en",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Trader"
        assert data["data"]["language"] == "en"

    @pytest.mark.asyncio
    async def test_update_profile_invalid_language(self, client: AsyncClient, test_user):
        """Test updating profile with invalid language."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Update with invalid language
        response = await client.put(
            "/users/profile",
            json={"language": "fr"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_profile_invalid_timezone(self, client: AsyncClient, test_user):
        """Test updating profile with invalid timezone."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Update with invalid timezone
        response = await client.put(
            "/users/profile",
            json={"timezone": "Invalid/Timezone"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422


class TestChangePassword:
    """Tests for PUT /users/password."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient, test_user):
        """Test changing password successfully."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Change password
        response = await client.put(
            "/users/password",
            json={
                "current_password": "TestPass123",
                "new_password": "NewSecure456",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify new password works
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "NewSecure456",
            },
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client: AsyncClient, test_user):
        """Test changing password with wrong current password."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Change with wrong current password
        response = await client.put(
            "/users/password",
            json={
                "current_password": "WrongPassword",
                "new_password": "NewSecure456",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()


class TestGetStats:
    """Tests for GET /users/stats."""

    @pytest.mark.asyncio
    async def test_get_stats_no_data(self, client: AsyncClient, test_user):
        """Test getting stats for user with no data."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get stats
        response = await client.get(
            "/users/stats",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_uploads"] == 0
        assert data["data"]["total_trades"] == 0
        assert data["data"]["total_pnl"] == 0.0


class TestDeleteAccount:
    """Tests for DELETE /users/account."""

    @pytest.mark.asyncio
    async def test_delete_account_success(self, client: AsyncClient, test_user):
        """Test deleting account successfully."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Delete account
        response = await client.request(
            "DELETE",
            "/users/account",
            json={"password": "TestPass123"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify user cannot login anymore
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        assert login_response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_account_wrong_password(self, client: AsyncClient, test_user):
        """Test deleting account with wrong password."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Delete with wrong password
        response = await client.request(
            "DELETE",
            "/users/account",
            json={"password": "WrongPassword"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 401
