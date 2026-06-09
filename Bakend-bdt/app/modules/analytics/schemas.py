"""Pydantic schemas for analytics responses."""

from pydantic import BaseModel


class GlobalMetrics(BaseModel):
    """Global trading metrics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    net_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    rr_ratio: float | None = None
    breakeven_winrate: float | None = None
    profit_factor: float | None = None
    best_trade: float = 0.0
    worst_trade: float = 0.0
    initial_balance: float = 0.0
    final_balance: float = 0.0
    total_return_pct: float = 0.0


class HourMetrics(BaseModel):
    """Metrics by hour of day."""
    hour: int
    label: str
    trades: int
    wins: int
    losses: int
    win_rate: float
    net_pnl: float
    avg_pnl: float


class DayMetrics(BaseModel):
    """Metrics by day of week."""
    day: int
    label_es: str
    label_en: str
    trades: int
    wins: int
    losses: int
    win_rate: float
    net_pnl: float
    avg_pnl: float


class MonthMetrics(BaseModel):
    """Metrics by month."""
    month: int
    label: str
    trades: int
    wins: int
    losses: int
    win_rate: float
    net_pnl: float
    avg_pnl: float


class DirectionMetrics(BaseModel):
    """Metrics by trade direction."""
    buy: dict
    sell: dict


class SessionMetrics(BaseModel):
    """Metrics by market session."""
    session: str
    label_es: str
    label_en: str
    trades: int
    wins: int
    losses: int
    win_rate: float
    net_pnl: float
    avg_pnl: float


class BucketMetrics(BaseModel):
    """Distribution bucket."""
    range: str
    count: int
    total_pnl: float
    avg_pnl: float


class StreakMetrics(BaseModel):
    """Win/loss streak data."""
    max_win_streak: int = 0
    max_loss_streak: int = 0
    current_streak: int = 0
    loss_streak_3_plus_count: int = 0


class SimulationMetrics(BaseModel):
    """What-if simulation results."""
    sim_max_loss_5_pnl: float = 0.0
    sim_best_3_hours_pnl: float = 0.0


class SummaryResponse(BaseModel):
    """Summary response with global metrics only."""
    success: bool = True
    data: GlobalMetrics


class ByHourResponse(BaseModel):
    """Hourly breakdown response."""
    success: bool = True
    data: list[HourMetrics]


class ByDayResponse(BaseModel):
    """Day of week breakdown response."""
    success: bool = True
    data: list[DayMetrics]


class ByMonthResponse(BaseModel):
    """Monthly breakdown response."""
    success: bool = True
    data: list[MonthMetrics]


class BySessionResponse(BaseModel):
    """Session breakdown response."""
    success: bool = True
    data: list[SessionMetrics]


class StreaksResponse(BaseModel):
    """Streaks response."""
    success: bool = True
    data: StreakMetrics


class DistributionResponse(BaseModel):
    """Distribution response."""
    success: bool = True
    data: list[BucketMetrics]


class SimulateResponse(BaseModel):
    """Simulation response."""
    success: bool = True
    data: SimulationMetrics


class FullMetricsResponse(BaseModel):
    """Full metrics response with all dimensions."""
    success: bool = True
    data: dict


class CompareDelta(BaseModel):
    """Delta between two uploads."""
    pass


class CompareUpload(BaseModel):
    """Single upload metrics in comparison."""
    upload_id: str
    metrics: GlobalMetrics


class CompareResponse(BaseModel):
    """Compare response."""
    success: bool = True
    data: dict
