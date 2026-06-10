"""Tests for reports module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.reports.insights import InsightGenerator
from app.modules.reports.service import ReportsService


class TestInsightGenerator:
    """Tests for InsightGenerator."""

    def test_monthly_insights_high_win_rate(self):
        """High win rate generates success insight."""
        metrics = {"win_rate": 0.65, "total_trades": 50}
        insights = InsightGenerator.monthly_insights(metrics, "es")
        assert any(i["type"] == "success" for i in insights)

    def test_monthly_insights_low_win_rate(self):
        """Low win rate generates warning insight."""
        metrics = {"win_rate": 0.35, "total_trades": 50}
        insights = InsightGenerator.monthly_insights(metrics, "es")
        assert any(i["type"] == "warning" for i in insights)

    def test_monthly_insights_profitable(self):
        """Positive PnL generates success insight."""
        metrics = {"win_rate": 0.5, "net_pnl": 500.0, "total_trades": 50}
        insights = InsightGenerator.monthly_insights(metrics, "es")
        assert any(i["title"] == "Mes Rentable" for i in insights)

    def test_monthly_insights_losing(self):
        """Negative PnL generates warning insight."""
        metrics = {"win_rate": 0.5, "net_pnl": -300.0, "total_trades": 50}
        insights = InsightGenerator.monthly_insights(metrics, "es")
        assert any(i["title"] == "Mes con Pérdidas" for i in insights)

    def test_monthly_insights_english(self):
        """English language works correctly."""
        metrics = {"win_rate": 0.65, "total_trades": 50}
        insights = InsightGenerator.monthly_insights(metrics, "en")
        assert any(i["title"] == "Solid Win Rate" for i in insights)

    def test_monthly_insights_profit_factor(self):
        """Profit factor generates appropriate insight."""
        metrics = {"win_rate": 0.5, "profit_factor": 2.5, "total_trades": 50}
        insights = InsightGenerator.monthly_insights(metrics, "es")
        assert any(i["title"] == "Profit Factor Fuerte" for i in insights)

    def test_monthly_insights_negative_profit_factor(self):
        """Negative profit factor generates critical insight."""
        metrics = {"win_rate": 0.5, "profit_factor": 0.7, "total_trades": 50}
        insights = InsightGenerator.monthly_insights(metrics, "es")
        assert any(i["type"] == "critical" for i in insights)

    def test_annual_insights_profitable_year(self):
        """Positive annual return generates success insight."""
        metrics = {"win_rate": 0.55, "total_return_pct": 15.0}
        insights = InsightGenerator.annual_insights(metrics, "es")
        assert any(i["title"] == "Año Rentable" for i in insights)

    def test_annual_insights_major_loss(self):
        """Large annual loss generates critical insight."""
        metrics = {"win_rate": 0.45, "total_return_pct": -15.0}
        insights = InsightGenerator.annual_insights(metrics, "es")
        assert any(i["type"] == "critical" for i in insights)

    def test_empty_metrics(self):
        """Empty metrics don't crash."""
        insights = InsightGenerator.monthly_insights({}, "es")
        assert isinstance(insights, list)


class TestReportsService:
    """Tests for ReportsService."""

    @pytest.fixture
    def mock_deps(self):
        """Mock dependencies for ReportsService."""
        db = AsyncMock()
        redis_client = AsyncMock()
        redis_client.get = AsyncMock(return_value=None)
        redis_client.setex = AsyncMock()
        analytics = AsyncMock()
        return db, redis_client, analytics

    @pytest.mark.asyncio
    async def test_build_monthly_summary_english(self, mock_deps):
        """Monthly summary builds correctly in English."""
        db, redis_client, analytics = mock_deps
        service = ReportsService(db, redis_client, analytics)

        metrics = {
            "total_trades": 100,
            "win_rate": 0.6,
            "net_pnl": 1500.0,
            "profit_factor": 2.1,
        }

        summary = service._build_monthly_summary(metrics, "en")
        assert "100 trades" in summary
        assert "60.0%" in summary
        assert "$1,500.00" in summary
        assert "2.10" in summary

    @pytest.mark.asyncio
    async def test_build_monthly_summary_spanish(self, mock_deps):
        """Monthly summary builds correctly in Spanish."""
        db, redis_client, analytics = mock_deps
        service = ReportsService(db, redis_client, analytics)

        metrics = {
            "total_trades": 50,
            "win_rate": 0.45,
            "net_pnl": -200.0,
            "profit_factor": 0.8,
        }

        summary = service._build_monthly_summary(metrics, "es")
        assert "50 trades" in summary
        assert "45.0%" in summary
        assert "$200.00" in summary
        assert "0.80" in summary
