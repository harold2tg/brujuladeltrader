"""Upload endpoint tests."""

import io

import pytest
from httpx import AsyncClient


class TestUploadFile:
    """Tests for POST /uploads/."""

    @pytest.mark.asyncio
    async def test_upload_csv_success(self, client: AsyncClient, test_user):
        """Test uploading a valid CSV file."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "TestPass123"},
        )
        access_token = login_response.json()["data"]["access_token"]

        # Create test CSV content
        csv_content = (
            '"Símbolo","Dirección de apertura","Hora de cierre (UTC-5)",'
            '"Precio de entrada","Precio de cierre","Cantidad de Cierre","$ neto","Saldo $"\n'
            '"XAUUSD","Sell","08/06/2026 14:25:40.501","4326.73","4326.68","0.02 Lotes","0.10","845.36"\n'
        )

        # Upload file
        response = await client.post(
            "/uploads",
            files={"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "upload_id" in data["data"]
        assert data["data"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_upload_invalid_extension(self, client: AsyncClient, test_user):
        """Test uploading invalid file type."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "TestPass123"},
        )
        access_token = login_response.json()["data"]["access_token"]

        # Upload invalid file
        response = await client.post(
            "/uploads",
            files={"file": ("test.txt", io.BytesIO(b"test content"), "text/plain")},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "not allowed" in data["detail"].lower()


class TestListUploads:
    """Tests for GET /uploads/."""

    @pytest.mark.asyncio
    async def test_list_uploads_empty(self, client: AsyncClient, test_user):
        """Test listing uploads when none exist."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "TestPass123"},
        )
        access_token = login_response.json()["data"]["access_token"]

        # List uploads
        response = await client.get(
            "/uploads",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0


class TestGetUpload:
    """Tests for GET /uploads/{id}."""

    @pytest.mark.asyncio
    async def test_get_upload_not_found(self, client: AsyncClient, test_user):
        """Test getting non-existent upload."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "TestPass123"},
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get non-existent upload
        response = await client.get(
            "/uploads/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404


class TestDeleteUpload:
    """Tests for DELETE /uploads/{id}."""

    @pytest.mark.asyncio
    async def test_delete_upload_not_found(self, client: AsyncClient, test_user):
        """Test deleting non-existent upload."""
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "TestPass123"},
        )
        access_token = login_response.json()["data"]["access_token"]

        # Delete non-existent upload
        response = await client.request(
            "DELETE",
            "/uploads/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404
