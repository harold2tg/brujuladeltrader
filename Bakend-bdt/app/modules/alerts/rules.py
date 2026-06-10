"""Stateless rule evaluation functions for alert types."""

from decimal import Decimal
from typing import Callable


def _max_loss_per_trade(metrics: dict, threshold: Decimal) -> bool:
    """Trigger if worst trade loss (abs) exceeds threshold."""
    worst = metrics.get("worst_trade", 0)
    return abs(worst) > float(threshold)


def _loss_streak(metrics: dict, threshold: Decimal) -> bool:
    """Trigger if max consecutive losses >= threshold."""
    return metrics.get("max_loss_streak", 0) >= int(threshold)


def _daily_loss_limit(metrics: dict, threshold: Decimal) -> bool:
    """Trigger if net_pnl is negative and its absolute value exceeds threshold."""
    net_pnl = metrics.get("net_pnl", 0)
    return net_pnl < 0 and abs(net_pnl) > float(threshold)


def _win_rate_drop(metrics: dict, threshold: Decimal) -> bool:
    """Trigger if win_rate (0-1) * 100 < threshold."""
    win_rate = metrics.get("win_rate", 0)
    return (win_rate * 100) < float(threshold)


def _rr_below(metrics: dict, threshold: Decimal) -> bool:
    """Trigger if rr_ratio is not None and is below threshold."""
    rr_ratio = metrics.get("rr_ratio")
    if rr_ratio is None:
        return False
    return rr_ratio < float(threshold)


ALERT_EVALUATORS: dict[str, Callable[[dict, Decimal], bool]] = {
    "max_loss_per_trade": _max_loss_per_trade,
    "loss_streak": _loss_streak,
    "daily_loss_limit": _daily_loss_limit,
    "win_rate_drop": _win_rate_drop,
    "rr_below": _rr_below,
}
