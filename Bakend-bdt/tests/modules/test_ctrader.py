"""Tests for cTrader module and DataSource integration."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.crypto import decrypt, encrypt, mask_token


# ============================================================================
# Crypto tests (existing)
# ============================================================================


class TestCrypto:
    """Tests for AES-256-GCM encryption utilities."""

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "my_secret_api_key_12345"
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertext(self):
        plaintext = "same_text"
        enc1 = encrypt(plaintext)
        enc2 = encrypt(plaintext)
        # Different nonces should produce different ciphertext
        assert enc1 != enc2

    def test_mask_token_long(self):
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        masked = mask_token(token)
        assert masked == "eyJhbGciOi..."
        assert len(masked) == 13

    def test_mask_token_short(self):
        token = "abc"
        masked = mask_token(token)
        assert masked == "abc..."

    def test_encrypt_empty_string(self):
        encrypted = encrypt("")
        decrypted = decrypt(encrypted)
        assert decrypted == ""

    def test_encrypt_unicode(self):
        plaintext = "ñáéíóú"
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)
        assert decrypted == plaintext


# ============================================================================
# DataSource Service tests
# ============================================================================


class TestDataSourceService:
    """Tests for DataSourceService CRUD and sync metadata operations."""

    @pytest_asyncio.fixture
    async def ds_service(self, db_session: AsyncSession):
        """Provide a DataSourceService instance."""
        from app.modules.data_sources.service import DataSourceService
        return DataSourceService(db_session)

    @pytest_asyncio.fixture
    async def test_user_id(self, test_user) -> str:
        """Return the test user ID as string."""
        return str(test_user.id)

    async def test_get_or_create_creates_new(self, ds_service, test_user_id):
        """get_or_create_data_source creates a new record when none exists."""
        ds = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="12345",
            name="cTrader Test Account",
        )
        assert ds.id is not None
        assert ds.broker == "ctrader"
        assert ds.broker_account_id == "12345"
        assert ds.name == "cTrader Test Account"
        assert ds.sync_status == "idle"
        assert ds.trade_count == 0

    async def test_get_or_create_idempotent(self, ds_service, test_user_id):
        """get_or_create_data_source returns existing record on duplicate."""
        ds1 = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="12345",
            name="cTrader Test Account",
        )
        ds2 = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="12345",
            name="cTrader Test Account",
        )
        assert ds1.id == ds2.id

    async def test_get_or_create_updates_name(self, ds_service, test_user_id):
        """get_or_create_data_source updates name if changed."""
        ds1 = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="12345",
            name="Old Name",
        )
        ds2 = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="12345",
            name="New Name",
        )
        assert ds1.id == ds2.id
        assert ds2.name == "New Name"

    async def test_list_data_sources(self, ds_service, test_user_id):
        """list_data_sources returns paginated results."""
        # Create two data sources
        await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="111",
            name="Account 1",
        )
        await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="222",
            name="Account 2",
        )

        result = await ds_service.list_data_sources(user_id=test_user_id)
        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["has_next"] is False

    async def test_get_data_source(self, ds_service, test_user_id):
        """get_data_source returns the correct record."""
        created = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="999",
            name="Get Test",
        )
        fetched = await ds_service.get_data_source(str(created.id), test_user_id)
        assert fetched.id == created.id
        assert fetched.name == "Get Test"

    async def test_get_data_source_not_found(self, ds_service, test_user_id):
        """get_data_source raises NotFoundException for missing record."""
        from app.shared.exceptions import NotFoundException

        fake_id = str(uuid.uuid4())
        with pytest.raises(NotFoundException):
            await ds_service.get_data_source(fake_id, test_user_id)

    async def test_delete_data_source(self, ds_service, test_user_id):
        """delete_data_source removes the record."""
        ds = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="del-test",
            name="Delete Me",
        )
        result = await ds_service.delete_data_source(str(ds.id), test_user_id)
        assert result is True

        from app.shared.exceptions import NotFoundException
        with pytest.raises(NotFoundException):
            await ds_service.get_data_source(str(ds.id), test_user_id)

    async def test_set_sync_status(self, ds_service, test_user_id):
        """set_sync_status updates the status correctly."""
        ds = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="status-test",
            name="Status Test",
        )
        assert ds.sync_status == "idle"

        await ds_service.set_sync_status(str(ds.id), "syncing")
        updated = await ds_service.get_data_source(str(ds.id), test_user_id)
        assert updated.sync_status == "syncing"

        await ds_service.set_sync_status(str(ds.id), "error")
        updated = await ds_service.get_data_source(str(ds.id), test_user_id)
        assert updated.sync_status == "error"

    async def test_set_sync_status_invalid(self, ds_service, test_user_id):
        """set_sync_status rejects invalid status values."""
        ds = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="invalid-status",
            name="Invalid Status",
        )
        with pytest.raises(ValueError, match="Invalid sync status"):
            await ds_service.set_sync_status(str(ds.id), "invalid_status")

    async def test_update_sync_metadata(self, ds_service, test_user_id):
        """update_sync_metadata updates trade_count and date range."""
        ds = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="meta-test",
            name="Metadata Test",
        )

        first = datetime(2025, 1, 1, tzinfo=timezone.utc)
        last = datetime(2025, 3, 31, tzinfo=timezone.utc)

        await ds_service.update_sync_metadata(
            data_source_id=str(ds.id),
            trades_added=50,
            first_trade_at=first,
            last_trade_at=last,
        )

        updated = await ds_service.get_data_source(str(ds.id), test_user_id)
        assert updated.trade_count == 50
        assert updated.first_trade_at == first
        assert updated.last_trade_at == last
        assert updated.sync_status == "idle"
        assert updated.last_synced_at is not None

    async def test_update_sync_metadata_accumulates(self, ds_service, test_user_id):
        """update_sync_metadata accumulates trade_count and extends date range."""
        ds = await ds_service.get_or_create_data_source(
            user_id=test_user_id,
            broker="ctrader",
            broker_account_id="accum-test",
            name="Accumulate Test",
        )

        # First sync: Jan-Feb
        await ds_service.update_sync_metadata(
            data_source_id=str(ds.id),
            trades_added=30,
            first_trade_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            last_trade_at=datetime(2025, 2, 28, tzinfo=timezone.utc),
        )

        # Second sync: Mar-Apr (extends range)
        await ds_service.update_sync_metadata(
            data_source_id=str(ds.id),
            trades_added=20,
            first_trade_at=datetime(2025, 3, 1, tzinfo=timezone.utc),
            last_trade_at=datetime(2025, 4, 30, tzinfo=timezone.utc),
        )

        updated = await ds_service.get_data_source(str(ds.id), test_user_id)
        assert updated.trade_count == 50  # 30 + 20
        assert updated.first_trade_at == datetime(2025, 1, 1, tzinfo=timezone.utc)
        assert updated.last_trade_at == datetime(2025, 4, 30, tzinfo=timezone.utc)


# ============================================================================
# cTrader sync integration tests (DataSource creation)
# ============================================================================


class TestCtraderSyncDataSource:
    """Verify that cTrader sync creates DataSource instead of Upload."""

    async def test_sync_creates_data_source(self, db_session, redis_client, test_user):
        """sync_trades creates a DataSource record and returns data_source_id."""
        from app.modules.ctrader.models import CtraderCredentials
        from app.modules.ctrader.service import CtraderService
        from app.shared.crypto import encrypt

        # Store credentials for test user
        creds = CtraderCredentials(
            user_id=test_user.id,
            client_id_enc=encrypt("test_client_id"),
            client_secret_enc=encrypt("test_client_secret"),
            access_token_enc=encrypt("test_access_token"),
            account_id_enc=encrypt("12345"),
            account_name="Test Account",
            broker_name="Test Broker",
            is_demo=True,
        )
        db_session.add(creds)
        await db_session.commit()

        # Mock CtraderClient to avoid real API calls
        mock_client = AsyncMock()
        mock_client.connect.return_value = True
        mock_client.authenticate_app.return_value = True
        mock_client.authenticate_account.return_value = True
        mock_client.get_symbols.return_value = {100: "XAUUSD"}
        mock_client.get_deals_history.return_value = []
        mock_client.disconnect.return_value = None

        service = CtraderService(db_session, redis_client)

        with patch(
            "app.modules.ctrader.service.CtraderClient",
            return_value=mock_client,
        ):
            result = await service.sync_trades(
                user_id=str(test_user.id),
                mode="year",
                date_str="2025-01-01",
            )

        # Verify result contains data_source_id, not upload_id
        assert "data_source_id" in result
        assert "upload_id" not in result
        assert result["status"] == "ready"

        # Verify DataSource was created
        from app.modules.data_sources.models import DataSource
        from sqlalchemy import select

        ds_result = await db_session.execute(
            select(DataSource).where(
                DataSource.user_id == test_user.id,
                DataSource.broker == "ctrader",
            )
        )
        ds = ds_result.scalar_one_or_none()
        assert ds is not None
        assert ds.broker_account_id == "12345"
        assert ds.sync_status == "idle"

    async def test_sync_sets_error_on_failure(self, db_session, redis_client, test_user):
        """sync_trades sets DataSource status to 'error' on failure."""
        from app.modules.ctrader.models import CtraderCredentials
        from app.modules.ctrader.service import CtraderService
        from app.shared.crypto import encrypt

        # Store credentials
        creds = CtraderCredentials(
            user_id=test_user.id,
            client_id_enc=encrypt("test_client_id"),
            client_secret_enc=encrypt("test_client_secret"),
            access_token_enc=encrypt("test_access_token"),
            account_id_enc=encrypt("99999"),
            account_name="Error Account",
            broker_name="Error Broker",
            is_demo=True,
        )
        db_session.add(creds)
        await db_session.commit()

        # Mock CtraderClient to simulate failure
        mock_client = AsyncMock()
        mock_client.connect.return_value = True
        mock_client.authenticate_app.return_value = False  # Auth failure
        mock_client.disconnect.return_value = None

        service = CtraderService(db_session, redis_client)

        with patch(
            "app.modules.ctrader.service.CtraderClient",
            return_value=mock_client,
        ):
            from app.shared.exceptions import BadRequestException
            with pytest.raises(BadRequestException):
                await service.sync_trades(
                    user_id=str(test_user.id),
                    mode="day",
                    date_str="2025-06-01",
                )

        # Verify DataSource status is 'error'
        from app.modules.data_sources.models import DataSource
        from sqlalchemy import select

        ds_result = await db_session.execute(
            select(DataSource).where(
                DataSource.user_id == test_user.id,
                DataSource.broker_account_id == "99999",
            )
        )
        ds = ds_result.scalar_one_or_none()
        assert ds is not None
        assert ds.sync_status == "error"
