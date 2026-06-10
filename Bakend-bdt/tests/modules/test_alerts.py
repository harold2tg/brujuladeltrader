"""Alerts module tests — unit, service, and endpoint tests."""

from decimal import Decimal

import pytest

from app.modules.alerts.rules import (
    _daily_loss_limit,
    _loss_streak,
    _max_loss_per_trade,
    _rr_below,
    _win_rate_drop,
)


# ─── Unit tests: rules.py ────────────────────────────────────────────


class TestMaxLossPerTrade:
    """Tests for _max_loss_per_trade evaluator."""

    def test_triggers_when_worst_exceeds_threshold(self):
        metrics = {"worst_trade": -15.50}
        assert _max_loss_per_trade(metrics, Decimal("10")) is True

    def test_does_not_trigger_when_within_threshold(self):
        metrics = {"worst_trade": -8.00}
        assert _max_loss_per_trade(metrics, Decimal("10")) is False

    def test_does_not_trigger_on_positive_trade(self):
        metrics = {"worst_trade": 5.00}
        assert _max_loss_per_trade(metrics, Decimal("10")) is False

    def test_exact_threshold_does_not_trigger(self):
        metrics = {"worst_trade": -10.00}
        assert _max_loss_per_trade(metrics, Decimal("10")) is False

    def test_missing_metric_defaults_to_zero(self):
        metrics = {}
        assert _max_loss_per_trade(metrics, Decimal("10")) is False


class TestLossStreak:
    """Tests for _loss_streak evaluator."""

    def test_triggers_when_streak_meets_threshold(self):
        metrics = {"max_loss_streak": 5}
        assert _loss_streak(metrics, Decimal("5")) is True

    def test_triggers_when_streak_exceeds_threshold(self):
        metrics = {"max_loss_streak": 7}
        assert _loss_streak(metrics, Decimal("5")) is True

    def test_does_not_trigger_when_below_threshold(self):
        metrics = {"max_loss_streak": 3}
        assert _loss_streak(metrics, Decimal("5")) is False

    def test_missing_metric_defaults_to_zero(self):
        metrics = {}
        assert _loss_streak(metrics, Decimal("3")) is False


class TestDailyLossLimit:
    """Tests for _daily_loss_limit evaluator."""

    def test_triggers_when_loss_exceeds_threshold(self):
        metrics = {"net_pnl": -150.00}
        assert _daily_loss_limit(metrics, Decimal("100")) is True

    def test_does_not_trigger_on_profit(self):
        metrics = {"net_pnl": 50.00}
        assert _daily_loss_limit(metrics, Decimal("100")) is False

    def test_does_not_trigger_when_within_threshold(self):
        metrics = {"net_pnl": -80.00}
        assert _daily_loss_limit(metrics, Decimal("100")) is False

    def test_does_not_trigger_on_zero_pnl(self):
        metrics = {"net_pnl": 0}
        assert _daily_loss_limit(metrics, Decimal("100")) is False


class TestWinRateDrop:
    """Tests for _win_rate_drop evaluator."""

    def test_triggers_when_below_threshold(self):
        metrics = {"win_rate": 0.35}  # 35%
        assert _win_rate_drop(metrics, Decimal("40")) is True

    def test_does_not_trigger_when_above_threshold(self):
        metrics = {"win_rate": 0.55}  # 55%
        assert _win_rate_drop(metrics, Decimal("40")) is False

    def test_exact_threshold_does_not_trigger(self):
        metrics = {"win_rate": 0.40}  # 40%
        assert _win_rate_drop(metrics, Decimal("40")) is False


class TestRrBelow:
    """Tests for _rr_below evaluator."""

    def test_triggers_when_below_threshold(self):
        metrics = {"rr_ratio": 1.2}
        assert _rr_below(metrics, Decimal("1.5")) is True

    def test_does_not_trigger_when_above_threshold(self):
        metrics = {"rr_ratio": 2.0}
        assert _rr_below(metrics, Decimal("1.5")) is False

    def test_does_not_trigger_when_rr_ratio_is_none(self):
        metrics = {"rr_ratio": None}
        assert _rr_below(metrics, Decimal("1.5")) is False

    def test_missing_metric_does_not_trigger(self):
        metrics = {}
        assert _rr_below(metrics, Decimal("1.5")) is False


# ─── Integration tests: service CRUD ─────────────────────────────────


class TestAlertsServiceCRUD:
    """Tests for AlertsService CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_rule(self, db_session, redis_client, test_user):
        """Creating a rule persists it and returns it."""
        from app.modules.alerts.service import AlertsService
        from app.modules.alerts.schemas import RuleCreate

        service = AlertsService(db_session, redis_client)
        rule = await service.create_rule(
            str(test_user.id),
            RuleCreate(alert_type="max_loss_per_trade", threshold=Decimal("10.00")),
        )
        assert rule.alert_type == "max_loss_per_trade"
        assert rule.threshold == Decimal("10.00")
        assert rule.is_active is True
        assert rule.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_list_rules_empty(self, db_session, redis_client, test_user):
        """List rules returns empty when no rules exist."""
        from app.modules.alerts.service import AlertsService

        service = AlertsService(db_session, redis_client)
        rules = await service.list_rules(str(test_user.id))
        assert rules == []

    @pytest.mark.asyncio
    async def test_list_rules_returns_created(self, db_session, redis_client, test_user):
        """List rules returns created rules."""
        from app.modules.alerts.service import AlertsService
        from app.modules.alerts.schemas import RuleCreate

        service = AlertsService(db_session, redis_client)
        await service.create_rule(
            str(test_user.id),
            RuleCreate(alert_type="loss_streak", threshold=Decimal("3")),
        )
        rules = await service.list_rules(str(test_user.id))
        assert len(rules) == 1
        assert rules[0].alert_type == "loss_streak"

    @pytest.mark.asyncio
    async def test_get_rule_or_404_not_found(self, db_session, redis_client, test_user):
        """Get rule raises NotFoundException for nonexistent ID."""
        import uuid
        from app.modules.alerts.service import AlertsService
        from app.shared.exceptions import NotFoundException

        service = AlertsService(db_session, redis_client)
        with pytest.raises(NotFoundException):
            await service.get_rule_or_404(str(uuid.uuid4()), str(test_user.id))

    @pytest.mark.asyncio
    async def test_update_rule(self, db_session, redis_client, test_user):
        """Update rule changes threshold and is_active."""
        from app.modules.alerts.service import AlertsService
        from app.modules.alerts.schemas import RuleCreate, RuleUpdate

        service = AlertsService(db_session, redis_client)
        rule = await service.create_rule(
            str(test_user.id),
            RuleCreate(alert_type="win_rate_drop", threshold=Decimal("40")),
        )
        updated = await service.update_rule(
            str(rule.id),
            str(test_user.id),
            RuleUpdate(threshold=Decimal("35"), is_active=False),
        )
        assert updated.threshold == Decimal("35")
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_delete_rule(self, db_session, redis_client, test_user):
        """Delete rule removes it from DB."""
        from app.modules.alerts.service import AlertsService
        from app.modules.alerts.schemas import RuleCreate

        service = AlertsService(db_session, redis_client)
        rule = await service.create_rule(
            str(test_user.id),
            RuleCreate(alert_type="rr_below", threshold=Decimal("1.5")),
        )
        await service.delete_rule(str(rule.id), str(test_user.id))
        rules = await service.list_rules(str(test_user.id))
        assert len(rules) == 0

    @pytest.mark.asyncio
    async def test_create_rule_invalid_type(self, db_session, redis_client, test_user):
        """Create rule with invalid alert_type raises BadRequestException."""
        from app.modules.alerts.service import AlertsService
        from app.modules.alerts.schemas import RuleCreate
        from app.shared.exceptions import BadRequestException

        service = AlertsService(db_session, redis_client)
        with pytest.raises(BadRequestException):
            await service.create_rule(
                str(test_user.id),
                RuleCreate(alert_type="invalid_type", threshold=Decimal("10")),
            )

    @pytest.mark.asyncio
    async def test_create_rule_plan_limit(self, db_session, redis_client, test_user):
        """Free plan user cannot create more than 3 active rules."""
        from app.modules.alerts.service import AlertsService
        from app.modules.alerts.schemas import RuleCreate
        from app.shared.exceptions import PlanLimitException

        service = AlertsService(db_session, redis_client)
        # Create 3 rules (free plan limit)
        for i, alert_type in enumerate(["max_loss_per_trade", "loss_streak", "win_rate_drop"]):
            await service.create_rule(
                str(test_user.id),
                RuleCreate(alert_type=alert_type, threshold=Decimal(str(10 + i))),
            )
        # 4th should fail
        with pytest.raises(PlanLimitException):
            await service.create_rule(
                str(test_user.id),
                RuleCreate(alert_type="daily_loss_limit", threshold=Decimal("100")),
            )


# ─── Integration tests: Redis dedup ──────────────────────────────────


class TestAlertsDedup:
    """Tests for Redis-based alert deduplication."""

    @pytest.mark.asyncio
    async def test_dedup_key_format(self, db_session, redis_client, test_user):
        """Dedup key contains user_id, rule_id, and hour string."""
        import uuid
        from app.modules.alerts.service import AlertsService

        service = AlertsService(db_session, redis_client)
        rule_id = str(uuid.uuid4())
        key = service._dedup_key(str(test_user.id), rule_id)
        assert str(test_user.id) in key
        assert rule_id in key
        assert "alert_dedup:" in key

    @pytest.mark.asyncio
    async def test_check_dedup_returns_false_when_no_key(self, db_session, redis_client, test_user):
        """Check dedup returns False when no key exists."""
        import uuid
        from app.modules.alerts.service import AlertsService

        service = AlertsService(db_session, redis_client)
        result = await service._check_dedup(str(test_user.id), str(uuid.uuid4()))
        assert result is False

    @pytest.mark.asyncio
    async def test_set_dedup_and_check(self, db_session, redis_client, test_user):
        """After setting dedup, check returns True."""
        import uuid
        from app.modules.alerts.service import AlertsService

        service = AlertsService(db_session, redis_client)
        rule_id = str(uuid.uuid4())
        await service._set_dedup(str(test_user.id), rule_id)
        result = await service._check_dedup(str(test_user.id), rule_id)
        assert result is True


# ─── Endpoint tests ──────────────────────────────────────────────────


class TestAlertsEndpoints:
    """Integration tests for alerts API endpoints."""

    @pytest.mark.asyncio
    async def test_list_rules_empty(self, client, test_user, test_user_tokens):
        """GET /alerts/rules returns empty list."""
        response = await client.get(
            "/alerts/rules",
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_create_rule(self, client, test_user, test_user_tokens):
        """POST /alerts/rules creates a rule."""
        response = await client.post(
            "/alerts/rules",
            json={"alert_type": "max_loss_per_trade", "threshold": 10.00},
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["alert_type"] == "max_loss_per_trade"
        assert float(data["data"]["threshold"]) == 10.00

    @pytest.mark.asyncio
    async def test_create_and_list_rules(self, client, test_user, test_user_tokens):
        """POST + GET /alerts/rules."""
        # Create
        await client.post(
            "/alerts/rules",
            json={"alert_type": "loss_streak", "threshold": 5},
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        # List
        response = await client.get(
            "/alerts/rules",
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["alert_type"] == "loss_streak"

    @pytest.mark.asyncio
    async def test_update_rule(self, client, test_user, test_user_tokens):
        """PUT /alerts/rules/{id} updates threshold."""
        # Create
        create_resp = await client.post(
            "/alerts/rules",
            json={"alert_type": "win_rate_drop", "threshold": 40},
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        rule_id = create_resp.json()["data"]["id"]

        # Update
        response = await client.put(
            f"/alerts/rules/{rule_id}",
            json={"threshold": 35},
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert float(data["data"]["threshold"]) == 35.0

    @pytest.mark.asyncio
    async def test_delete_rule(self, client, test_user, test_user_tokens):
        """DELETE /alerts/rules/{id} removes rule."""
        # Create
        create_resp = await client.post(
            "/alerts/rules",
            json={"alert_type": "rr_below", "threshold": 1.5},
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        rule_id = create_resp.json()["data"]["id"]

        # Delete
        response = await client.delete(
            f"/alerts/rules/{rule_id}",
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        assert response.status_code == 200

        # Verify deleted
        list_resp = await client.get(
            "/alerts/rules",
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        assert list_resp.json()["data"] == []

    @pytest.mark.asyncio
    async def test_list_history_empty(self, client, test_user, test_user_tokens):
        """GET /alerts/history returns empty list."""
        response = await client.get(
            "/alerts/history",
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """Alerts endpoints return 422 without auth."""
        response = await client.get("/alerts/rules")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_rule_invalid_type(self, client, test_user, test_user_tokens):
        """POST /alerts/rules rejects invalid alert_type."""
        response = await client.post(
            "/alerts/rules",
            json={"alert_type": "nonexistent", "threshold": 10},
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_create_rule_plan_limit_enforced(self, client, test_user, test_user_tokens):
        """Free plan user gets 403 after 3 active rules."""
        headers = {"Authorization": f"Bearer {test_user_tokens['access_token']}"}
        for alert_type in ["max_loss_per_trade", "loss_streak", "win_rate_drop"]:
            await client.post(
                "/alerts/rules",
                json={"alert_type": alert_type, "threshold": 10},
                headers=headers,
            )
        response = await client.post(
            "/alerts/rules",
            json={"alert_type": "daily_loss_limit", "threshold": 100},
            headers=headers,
        )
        assert response.status_code == 403
