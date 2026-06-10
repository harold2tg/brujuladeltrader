"""Alerts service — CRUD, evaluation orchestration, Redis dedup."""

import logging
import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import redis.asyncio as redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.alerts.models import AlertHistory, AlertRule
from app.modules.alerts.rules import ALERT_EVALUATORS
from app.modules.alerts.schemas import RuleCreate, RuleUpdate
from app.shared.exceptions import NotFoundException, PlanLimitException

logger = logging.getLogger(__name__)

DEDUP_TTL = 3900  # 1 hour + 5 min buffer


class AlertsService:
    """Service for alert rule CRUD and evaluation."""

    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    # ── Rules CRUD ──────────────────────────────────────────────

    async def create_rule(self, user_id: str, data: RuleCreate) -> AlertRule:
        """Create an alert rule, enforcing free plan limit."""
        if data.alert_type not in ALERT_EVALUATORS:
            from app.shared.exceptions import BadRequestException
            raise BadRequestException(
                f"Invalid alert_type. Must be one of: {', '.join(ALERT_EVALUATORS.keys())}"
            )

        # Check plan limit for free users
        count_result = await self.db.execute(
            select(func.count()).where(
                AlertRule.user_id == uuid.UUID(user_id),
                AlertRule.is_active == True,
            )
        )
        active_count = count_result.scalar()

        if active_count >= settings.FREE_PLAN_MAX_ALERT_RULES:
            raise PlanLimitException(
                f"Free plan allows max {settings.FREE_PLAN_MAX_ALERT_RULES} active alert rules"
            )

        rule = AlertRule(
            user_id=uuid.UUID(user_id),
            alert_type=data.alert_type,
            threshold=data.threshold,
            is_active=data.is_active,
        )
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def list_rules(self, user_id: str) -> list[AlertRule]:
        """List all alert rules for a user, ordered by created_at DESC."""
        result = await self.db.execute(
            select(AlertRule)
            .where(AlertRule.user_id == uuid.UUID(user_id))
            .order_by(AlertRule.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_rule_or_404(self, rule_id: str, user_id: str) -> AlertRule:
        """Get a rule by ID and verify ownership."""
        result = await self.db.execute(
            select(AlertRule).where(
                AlertRule.id == uuid.UUID(rule_id),
                AlertRule.user_id == uuid.UUID(user_id),
            )
        )
        rule = result.scalar_one_or_none()
        if not rule:
            raise NotFoundException("Alert rule not found")
        return rule

    async def update_rule(self, rule_id: str, user_id: str, data: RuleUpdate) -> AlertRule:
        """Update threshold or is_active for a rule."""
        rule = await self.get_rule_or_404(rule_id, user_id)

        if data.threshold is not None:
            rule.threshold = data.threshold
        if data.is_active is not None:
            rule.is_active = data.is_active

        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def delete_rule(self, rule_id: str, user_id: str) -> None:
        """Delete a rule (cascades to alert_history)."""
        rule = await self.get_rule_or_404(rule_id, user_id)
        await self.db.delete(rule)
        await self.db.flush()

    # ── History ─────────────────────────────────────────────────

    async def get_history(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        rule_id: str | None = None,
    ) -> tuple[list[AlertHistory], int]:
        """Get paginated alert history with optional rule_id filter."""
        query = select(AlertHistory).where(AlertHistory.user_id == uuid.UUID(user_id))

        if rule_id:
            query = query.where(AlertHistory.rule_id == uuid.UUID(rule_id))

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginated results
        offset = (page - 1) * limit
        query = query.order_by(AlertHistory.triggered_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    # ── Redis Dedup ─────────────────────────────────────────────

    def _dedup_key(self, user_id: str, rule_id: str) -> str:
        """Generate Redis dedup key for the current hour."""
        now = datetime.now(timezone.utc)
        hour_str = now.strftime("%Y%m%d%H")
        return f"alert_dedup:{user_id}:{rule_id}:{hour_str}"

    async def _check_dedup(self, user_id: str, rule_id: str) -> bool:
        """Return True if this rule already fired this hour."""
        key = self._dedup_key(user_id, rule_id)
        try:
            exists = await self.redis.exists(key)
            return bool(exists)
        except Exception:
            logger.warning("Redis dedup check failed for key: %s", key)
            return False

    async def _set_dedup(self, user_id: str, rule_id: str) -> None:
        """Set dedup key with TTL."""
        key = self._dedup_key(user_id, rule_id)
        try:
            await self.redis.setex(key, DEDUP_TTL, "1")
        except Exception:
            logger.warning("Redis dedup set failed for key: %s", key)

    async def _record_alert(
        self,
        rule_id: str,
        user_id: str,
        upload_id: str | None,
        value: Decimal,
    ) -> AlertHistory:
        """Insert an alert_history row."""
        history = AlertHistory(
            rule_id=uuid.UUID(rule_id),
            user_id=uuid.UUID(user_id),
            upload_id=uuid.UUID(upload_id) if upload_id else None,
            triggered_value=value,
        )
        self.db.add(history)
        await self.db.flush()
        return history

    # ── Evaluation ──────────────────────────────────────────────

    async def evaluate_for_upload(self, upload_id: str, user_id: str) -> None:
        """Evaluate all active rules for a user against upload metrics.

        Called after parser marks an upload as ready.
        """
        from app.modules.analytics.service import AnalyticsService

        # Fetch active rules
        result = await self.db.execute(
            select(AlertRule).where(
                AlertRule.user_id == uuid.UUID(user_id),
                AlertRule.is_active == True,
            )
        )
        rules = list(result.scalars().all())

        if not rules:
            return

        # Fetch metrics
        analytics_service = AnalyticsService(self.db, self.redis)
        try:
            metrics = await analytics_service.get_summary(upload_id, user_id)
        except Exception:
            logger.warning(
                "Failed to fetch metrics for upload %s, skipping alert evaluation", upload_id
            )
            return

        for rule in rules:
            evaluator = ALERT_EVALUATORS.get(rule.alert_type)
            if not evaluator:
                continue

            # Check dedup
            if await self._check_dedup(user_id, str(rule.id)):
                continue

            # Evaluate
            triggered = evaluator(metrics, rule.threshold)
            if triggered:
                # Determine which metric value triggered it
                triggered_value = self._get_triggered_value(rule.alert_type, metrics)
                await self._record_alert(
                    rule_id=str(rule.id),
                    user_id=user_id,
                    upload_id=upload_id,
                    value=Decimal(str(triggered_value)),
                )
                await self._set_dedup(user_id, str(rule.id))
                logger.info(
                    "Alert triggered: user=%s rule=%s type=%s value=%s",
                    user_id,
                    rule.id,
                    rule.alert_type,
                    triggered_value,
                )

    def _get_triggered_value(self, alert_type: str, metrics: dict) -> float:
        """Extract the relevant metric value that triggered the alert."""
        mapping = {
            "max_loss_per_trade": lambda m: abs(m.get("worst_trade", 0)),
            "loss_streak": lambda m: m.get("max_loss_streak", 0),
            "daily_loss_limit": lambda m: abs(m.get("net_pnl", 0)),
            "win_rate_drop": lambda m: m.get("win_rate", 0) * 100,
            "rr_below": lambda m: m.get("rr_ratio", 0),
        }
        extractor = mapping.get(alert_type)
        if extractor:
            return float(extractor(metrics))
        return 0.0
