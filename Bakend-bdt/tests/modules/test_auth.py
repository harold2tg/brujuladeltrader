"""Authentication endpoint tests."""

import pytest
from httpx import AsyncClient


class TestRegister:
    """Tests for POST /auth/register."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newtrader@example.com",
                "password": "SecurePass123",
                "name": "New Trader",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["user"]["email"] == "newtrader@example.com"
        assert data["data"]["user"]["name"] == "New Trader"
        assert data["data"]["user"]["plan"] == "free"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email returns 409."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",  # Same as test_user
                "password": "AnotherPass123",
                "name": "Another Trader",
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert "already registered" in data["detail"].lower() or "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123",
                "name": "Trader",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "trader@example.com",
                "password": "weak",  # Too short, no uppercase, no number
                "name": "Trader",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "trader@example.com",
                # Missing password and name
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /auth/login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password returns generic 401."""
        response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid credentials"

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: AsyncClient):
        """Test login with nonexistent email returns same generic 401."""
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid credentials"


class TestRefreshToken:
    """Tests for POST /auth/refresh."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, client: AsyncClient, test_user):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        refresh_token = login_response.json()["data"]["refresh_token"]

        # Refresh
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401


class TestLogout:
    """Tests for POST /auth/logout."""

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, test_user):
        """Test successful logout blacklists token."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Logout
        response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        # Try to use the same token - should fail
        me_response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_response.status_code == 401


class TestGetMe:
    """Tests for GET /auth/me."""

    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient, test_user):
        """Test getting current user profile."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get me
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "test@example.com"
        assert data["data"]["name"] == "Test Trader"
        assert "password_hash" not in data["data"]

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_no_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/auth/me")
        assert response.status_code == 422  # Missing required header
