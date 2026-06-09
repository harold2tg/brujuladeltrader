"""Tests for analytics metrics calculations."""

import pandas as pd
import pytest

from app.modules.analytics.metrics import (
    calculate_by_day,
    calculate_by_direction,
    calculate_by_hour,
    calculate_by_month,
    calculate_by_session,
    calculate_distribution,
    calculate_global_metrics,
    calculate_simulations,
    calculate_streaks,
)


@pytest.fixture
def sample_trades_df() -> pd.DataFrame:
    """Create a sample trades DataFrame for testing."""
    return pd.DataFrame({
        "net_pnl": [10.0, -5.0, 15.0, -3.0, 8.0, -12.0, 20.0, -2.0, 7.0, -1.0,
                    5.0, -8.0, 12.0, -4.0, 9.0, -6.0, 3.0, -7.0, 11.0, -9.0],
        "hour_of_day": [9, 9, 10, 10, 11, 11, 12, 12, 13, 13,
                        14, 14, 15, 15, 16, 16, 10, 10, 11, 11],
        "day_of_week": [0, 0, 0, 1, 1, 1, 2, 2, 2, 3,
                        3, 3, 4, 4, 4, 5, 5, 6, 6, 6],
        "month": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                  2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        "session": ["ny_overlap", "ny_overlap", "ny_overlap", "ny_overlap",
                    "ny_session", "ny_session", "ny_session", "ny_session",
                    "ny_session", "ny_session", "ny_session", "ny_session",
                    "ny_session", "ny_session", "ny_session", "ny_session",
                    "ny_overlap", "ny_overlap", "ny_session", "ny_session"],
        "direction": ["Buy", "Sell", "Buy", "Buy", "Sell", "Buy", "Sell", "Buy",
                      "Sell", "Buy", "Buy", "Sell", "Buy", "Sell", "Buy", "Sell",
                      "Buy", "Sell", "Buy", "Sell"],
        "balance": [1000, 1005, 1010, 1007, 1015, 1012, 1020, 1008, 1028, 1026,
                    1033, 1025, 1037, 1033, 1042, 1036, 1039, 1032, 1043, 1034],
        "trade_number": list(range(1, 21)),
    })


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """Create an empty DataFrame."""
    return pd.DataFrame()


class TestCalculateGlobalMetrics:
    """Tests for calculate_global_metrics."""

    def test_basic_metrics(self, sample_trades_df: pd.DataFrame):
        result = calculate_global_metrics(sample_trades_df)

        assert result["total_trades"] == 20
        assert result["winning_trades"] == 10
        assert result["losing_trades"] == 10
        assert result["win_rate"] == 0.5
        assert result["net_pnl"] == 43.0
        assert result["best_trade"] == 20.0
        assert result["worst_trade"] == -12.0

    def test_empty_df(self, empty_df: pd.DataFrame):
        result = calculate_global_metrics(empty_df)

        assert result["total_trades"] == 0
        assert result["win_rate"] == 0.0
        assert result["rr_ratio"] is None
        assert result["profit_factor"] is None

    def test_all_winners(self):
        df = pd.DataFrame({
            "net_pnl": [10.0, 15.0, 20.0],
            "balance": [1000, 1010, 1025],
        })
        result = calculate_global_metrics(df)

        assert result["win_rate"] == 1.0
        assert result["rr_ratio"] is None  # No losses
        assert result["profit_factor"] is None

    def test_all_losers(self):
        df = pd.DataFrame({
            "net_pnl": [-10.0, -15.0, -20.0],
            "balance": [1000, 990, 975],
        })
        result = calculate_global_metrics(df)

        assert result["win_rate"] == 0.0
        assert result["rr_ratio"] == 0.0  # avg_win=0, so 0/abs(avg_loss) = 0

    def test_zero_pnl_counts_as_loss(self):
        df = pd.DataFrame({
            "net_pnl": [10.0, 0.0, -5.0],
            "balance": [1000, 1010, 1010],
        })
        result = calculate_global_metrics(df)

        assert result["winning_trades"] == 1
        assert result["losing_trades"] == 2  # zero counts as loss


class TestCalculateByHour:
    """Tests for calculate_by_hour."""

    def test_filters_low_volume(self, sample_trades_df: pd.DataFrame):
        result = calculate_by_hour(sample_trades_df, threshold=5)

        # All hours have 2-4 trades, all below threshold of 5
        assert len(result) == 0

    def test_includes_high_volume(self):
        df = pd.DataFrame({
            "net_pnl": [10.0] * 6 + [-5.0] * 6,
            "hour_of_day": [10] * 6 + [14] * 6,
        })
        result = calculate_by_hour(df, threshold=5)

        assert len(result) == 2
        hours = [r["hour"] for r in result]
        assert 10 in hours
        assert 14 in hours

    def test_empty_df(self, empty_df: pd.DataFrame):
        result = calculate_by_hour(empty_df)
        assert result == []


class TestCalculateByDay:
    """Tests for calculate_by_day."""

    def test_filters_low_volume(self, sample_trades_df: pd.DataFrame):
        result = calculate_by_day(sample_trades_df, threshold=10)

        # Most days have 3-4 trades, all below threshold of 10
        assert len(result) == 0

    def test_includes_high_volume(self):
        df = pd.DataFrame({
            "net_pnl": [10.0] * 12,
            "day_of_week": [0] * 12,  # Monday
        })
        result = calculate_by_day(df, threshold=10)

        assert len(result) == 1
        assert result[0]["day"] == 0
        assert result[0]["label_es"] == "Lunes"
        assert result[0]["label_en"] == "Monday"


class TestCalculateByMonth:
    """Tests for calculate_by_month."""

    def test_basic(self, sample_trades_df: pd.DataFrame):
        result = calculate_by_month(sample_trades_df)

        assert len(result) == 2  # January and February
        months = [r["month"] for r in result]
        assert 1 in months
        assert 2 in months


class TestCalculateByDirection:
    """Tests for calculate_by_direction."""

    def test_basic(self, sample_trades_df: pd.DataFrame):
        result = calculate_by_direction(sample_trades_df)

        assert "buy" in result
        assert "sell" in result
        assert result["buy"]["trades"] > 0
        assert result["sell"]["trades"] > 0


class TestCalculateBySession:
    """Tests for calculate_by_session."""

    def test_basic(self, sample_trades_df: pd.DataFrame):
        result = calculate_by_session(sample_trades_df)

        sessions = [r["session"] for r in result]
        assert "ny_overlap" in sessions
        assert "ny_session" in sessions

        # Check bilingual labels
        for r in result:
            assert "label_es" in r
            assert "label_en" in r


class TestCalculateDistribution:
    """Tests for calculate_distribution."""

    def test_basic(self, sample_trades_df: pd.DataFrame):
        result = calculate_distribution(sample_trades_df)

        assert len(result) == 7  # 7 buckets
        total_count = sum(b["count"] for b in result)
        assert total_count == 20

    def test_empty_df(self, empty_df: pd.DataFrame):
        result = calculate_distribution(empty_df)

        assert len(result) == 7
        assert all(b["count"] == 0 for b in result)


class TestCalculateStreaks:
    """Tests for calculate_streaks."""

    def test_basic(self, sample_trades_df: pd.DataFrame):
        result = calculate_streaks(sample_trades_df)

        assert "max_win_streak" in result
        assert "max_loss_streak" in result
        assert "current_streak" in result
        assert "loss_streak_3_plus_count" in result

    def test_empty_df(self, empty_df: pd.DataFrame):
        result = calculate_streaks(empty_df)

        assert result["max_win_streak"] == 0
        assert result["max_loss_streak"] == 0
        assert result["current_streak"] == 0
        assert result["loss_streak_3_plus_count"] == 0


class TestCalculateSimulations:
    """Tests for calculate_simulations."""

    def test_basic(self, sample_trades_df: pd.DataFrame):
        result = calculate_simulations(sample_trades_df)

        assert "sim_max_loss_5_pnl" in result
        assert "sim_best_3_hours_pnl" in result

    def test_loss_capping(self):
        df = pd.DataFrame({
            "net_pnl": [-12.0, -3.0, 10.0],
            "hour_of_day": [10, 10, 10],
        })
        result = calculate_simulations(df)

        # -12 capped to -5, -3 unchanged, +10 unchanged
        assert result["sim_max_loss_5_pnl"] == 2.0

    def test_empty_df(self, empty_df: pd.DataFrame):
        result = calculate_simulations(empty_df)

        assert result["sim_max_loss_5_pnl"] == 0.0
        assert result["sim_best_3_hours_pnl"] == 0.0
