"""Parser module tests."""

import io
import uuid
from datetime import datetime

import pandas as pd
import pytest
import pytz
from httpx import AsyncClient

from app.modules.parser.normalizer import (
    clean_balance,
    extract_lot_size,
    parse_datetime,
    parse_net_pnl,
)
from app.modules.parser.service import classify_session, calculate_derived_fields
from app.modules.parser.validators import validate_columns, map_columns


class TestCleanBalance:
    """Tests for balance cleaning."""

    def test_clean_balance_normal(self):
        """Test cleaning normal balance value."""
        assert clean_balance("845.36") == 845.36

    def test_clean_balance_with_comma(self):
        """Test cleaning balance with comma."""
        assert clean_balance("1,234.56") == 1234.56

    def test_clean_balance_with_xa0(self):
        """Test cleaning balance with \\xa0 as thousands separator."""
        # \xa0 is a non-breaking space used as thousands separator
        # "845\xa036" means 845,036 (eight hundred forty-five thousand thirty-six)
        assert clean_balance("845\xa036") == 84536.0

    def test_clean_balance_none(self):
        """Test cleaning None value."""
        assert clean_balance(None) is None


class TestExtractLotSize:
    """Tests for lot size extraction."""

    def test_extract_lot_size_normal(self):
        """Test extracting lot size from normal string."""
        assert extract_lot_size("0.02 Lotes") == 0.02

    def test_extract_lot_size_no_text(self):
        """Test extracting lot size without text."""
        assert extract_lot_size("0.01") == 0.01

    def test_extract_lot_size_single_lote(self):
        """Test extracting lot size with singular."""
        assert extract_lot_size("1 Lote") == 1.0

    def test_extract_lot_size_none(self):
        """Test extracting from None value."""
        assert extract_lot_size(None) is None


class TestParseDatetime:
    """Tests for datetime parsing."""

    def test_parse_datetime_normal(self):
        """Test parsing normal datetime string."""
        result = parse_datetime("08/06/2026 14:25:40.501")
        assert result is not None
        assert result.year == 2026
        assert result.month == 6
        assert result.day == 8
        assert result.hour == 14
        assert result.minute == 25
        assert result.second == 40
        assert result.tzinfo is not None

    def test_parse_datetime_none(self):
        """Test parsing None value."""
        assert parse_datetime(None) is None

    def test_parse_datetime_invalid(self):
        """Test parsing invalid datetime string."""
        assert parse_datetime("invalid") is None


class TestParseNetPnl:
    """Tests for net PnL parsing."""

    def test_parse_net_pnl_positive(self):
        """Test parsing positive value."""
        assert parse_net_pnl("0.10") == 0.10

    def test_parse_net_pnl_negative(self):
        """Test parsing negative value."""
        assert parse_net_pnl("-4.94") == -4.94

    def test_parse_net_pnl_none(self):
        """Test parsing None value."""
        assert parse_net_pnl(None) is None


class TestClassifySession:
    """Tests for session classification."""

    def test_london_open(self):
        """Test london_open session."""
        assert classify_session(7) == "london_open"
        assert classify_session(8) == "london_open"

    def test_ny_overlap(self):
        """Test ny_overlap session."""
        assert classify_session(9) == "ny_overlap"
        assert classify_session(11) == "ny_overlap"

    def test_ny_session(self):
        """Test ny_session session."""
        assert classify_session(12) == "ny_session"
        assert classify_session(16) == "ny_session"

    def test_off_hours(self):
        """Test off_hours session."""
        assert classify_session(0) == "off_hours"
        assert classify_session(6) == "off_hours"
        assert classify_session(17) == "off_hours"
        assert classify_session(23) == "off_hours"


class TestValidateColumns:
    """Tests for column validation."""

    def test_validate_columns_valid(self):
        """Test validation with all required columns."""
        df = pd.DataFrame({
            "Símbolo": ["XAUUSD"],
            "Dirección de apertura": ["Buy"],
            "Hora de cierre (UTC-5)": ["08/06/2026 14:25:40.501"],
            "Precio de entrada": ["4326.73"],
            "Precio de cierre": ["4326.68"],
            "Cantidad de Cierre": ["0.02 Lotes"],
            "$ neto": ["0.10"],
            "Saldo $": ["845.36"],
        })
        missing = validate_columns(df)
        assert missing == []

    def test_validate_columns_missing(self):
        """Test validation with missing columns."""
        df = pd.DataFrame({
            "Símbolo": ["XAUUSD"],
            "Dirección de apertura": ["Buy"],
        })
        missing = validate_columns(df)
        assert len(missing) == 6
        assert "Hora de cierre (UTC-5)" in missing


class TestMapColumns:
    """Tests for column mapping."""

    def test_map_columns(self):
        """Test column mapping."""
        df = pd.DataFrame({
            "Símbolo": ["XAUUSD"],
            "Dirección de apertura": ["Buy"],
            "Hora de cierre (UTC-5)": ["08/06/2026 14:25:40.501"],
            "Precio de entrada": ["4326.73"],
            "Precio de cierre": ["4326.68"],
            "Cantidad de Cierre": ["0.02 Lotes"],
            "$ neto": ["0.10"],
            "Saldo $": ["845.36"],
        })
        mapped = map_columns(df)
        assert "symbol" in mapped.columns
        assert "direction" in mapped.columns
        assert "closed_at" in mapped.columns
