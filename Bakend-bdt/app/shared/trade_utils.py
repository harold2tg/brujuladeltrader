"""Shared utilities for trade data processing.

Used by all broker integrations (cTrader, MetaTrader, Binance, etc.)
to calculate derived fields from raw trade data.
"""


def classify_session(hour: int) -> str:
    """
    Classify trading session based on hour (UTC-5).

    Sessions:
        - london_open: 07:00 - 09:00
        - ny_overlap: 09:00 - 12:00
        - ny_session: 12:00 - 17:00
        - off_hours: all other times
    """
    if 7 <= hour < 9:
        return "london_open"
    elif 9 <= hour < 12:
        return "ny_overlap"
    elif 12 <= hour < 17:
        return "ny_session"
    else:
        return "off_hours"


def calculate_derived_fields(row: dict, trade_number: int) -> dict:
    """
    Calculate derived fields for a trade.

    Args:
        row: Dictionary with normalized trade data (must include 'closed_at' and 'net_pnl')
        trade_number: Sequential number within the data source

    Returns:
        Dictionary with derived fields added:
        - hour_of_day (0-23)
        - day_of_week (0=Monday, 6=Sunday)
        - week_of_year (ISO calendar week)
        - month (1-12)
        - year
        - session (london_open | ny_overlap | ny_session | off_hours)
        - is_winner (net_pnl > 0)
        - trade_number
    """
    closed_at = row.get("closed_at")

    if closed_at is None:
        return row

    # Extract time components
    row["hour_of_day"] = closed_at.hour
    row["day_of_week"] = closed_at.weekday()  # 0=Monday, 6=Sunday
    row["week_of_year"] = closed_at.isocalendar()[1]
    row["month"] = closed_at.month
    row["year"] = closed_at.year
    row["session"] = classify_session(closed_at.hour)
    row["is_winner"] = row.get("net_pnl", 0) > 0
    row["trade_number"] = trade_number

    return row
