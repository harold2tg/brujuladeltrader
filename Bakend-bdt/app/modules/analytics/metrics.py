"""Pure pandas metric calculation functions."""

import pandas as pd


# Day names
DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Month names
MONTHS_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
MONTHS_EN = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Session labels
SESSION_LABELS = {
    "london_open": {"es": "Apertura Londres", "en": "London Open"},
    "ny_overlap": {"es": "Superposición NY", "en": "NY Overlap"},
    "ny_session": {"es": "Sesión NY", "en": "NY Session"},
    "off_hours": {"es": "Fuera de horario", "en": "Off Hours"},
}

# Hour labels
HOUR_LABELS = [f"{h:02d}:00" for h in range(24)]

# Distribution buckets
DISTRIBUTION_BUCKETS = [
    ("< -20", -float("inf"), -20),
    ("-20 / -10", -20, -10),
    ("-10 / -5", -10, -5),
    ("-5 / 0", -5, 0),
    ("0 / 5", 0, 5),
    ("5 / 10", 5, 10),
    ("> 10", 10, float("inf")),
]


def calculate_global_metrics(df: pd.DataFrame) -> dict:
    """Calculate global trading metrics from a DataFrame of trades."""
    if df.empty:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "net_pnl": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "rr_ratio": None,
            "breakeven_winrate": None,
            "profit_factor": None,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "initial_balance": 0.0,
            "final_balance": 0.0,
            "total_return_pct": 0.0,
        }

    total = len(df)
    winners = df[df["net_pnl"] > 0]
    losers = df[df["net_pnl"] <= 0]

    winning_trades = len(winners)
    losing_trades = len(losers)
    win_rate = winning_trades / total if total > 0 else 0.0

    net_pnl = float(df["net_pnl"].sum())
    gross_profit = float(winners["net_pnl"].sum()) if not winners.empty else 0.0
    gross_loss = float(losers["net_pnl"].sum()) if not losers.empty else 0.0

    avg_win = float(winners["net_pnl"].mean()) if not winners.empty else 0.0
    avg_loss = float(losers["net_pnl"].mean()) if not losers.empty else 0.0

    # R:R ratio: avg_win / abs(avg_loss)
    rr_ratio = None
    breakeven_winrate = None
    if losers.empty:
        rr_ratio = None
        breakeven_winrate = None
    else:
        abs_avg_loss = abs(avg_loss)
        if abs_avg_loss > 0:
            rr_ratio = avg_win / abs_avg_loss
            breakeven_winrate = 1 / (1 + rr_ratio)

    # Profit factor
    profit_factor = None
    if gross_loss != 0:
        profit_factor = gross_profit / abs(gross_loss)

    best_trade = float(df["net_pnl"].max())
    worst_trade = float(df["net_pnl"].min())

    # Balance
    initial_balance = float(df.iloc[0]["balance"]) if "balance" in df.columns else 0.0
    final_balance = float(df.iloc[-1]["balance"]) if "balance" in df.columns else 0.0

    total_return_pct = 0.0
    if initial_balance != 0:
        total_return_pct = ((final_balance - initial_balance) / initial_balance) * 100

    return {
        "total_trades": total,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(win_rate, 4),
        "net_pnl": round(net_pnl, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "rr_ratio": round(rr_ratio, 2) if rr_ratio is not None else None,
        "breakeven_winrate": round(breakeven_winrate, 4) if breakeven_winrate is not None else None,
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
        "best_trade": round(best_trade, 2),
        "worst_trade": round(worst_trade, 2),
        "initial_balance": round(initial_balance, 2),
        "final_balance": round(final_balance, 2),
        "total_return_pct": round(total_return_pct, 2),
    }


def calculate_by_hour(df: pd.DataFrame, threshold: int = 5) -> list[dict]:
    """Calculate metrics by hour of day. Hours with < threshold trades are excluded."""
    if df.empty:
        return []

    result = []
    for hour in range(24):
        hour_df = df[df["hour_of_day"] == hour]
        if len(hour_df) < threshold:
            continue

        wins = len(hour_df[hour_df["net_pnl"] > 0])
        losses = len(hour_df[hour_df["net_pnl"] <= 0])
        total = len(hour_df)

        result.append({
            "hour": hour,
            "label": HOUR_LABELS[hour],
            "trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total, 4) if total > 0 else 0.0,
            "net_pnl": round(float(hour_df["net_pnl"].sum()), 2),
            "avg_pnl": round(float(hour_df["net_pnl"].mean()), 2),
        })

    return result


def calculate_by_day(df: pd.DataFrame, threshold: int = 10) -> list[dict]:
    """Calculate metrics by day of week. Days with < threshold trades are excluded."""
    if df.empty:
        return []

    result = []
    for day in range(7):
        day_df = df[df["day_of_week"] == day]
        if len(day_df) < threshold:
            continue

        wins = len(day_df[day_df["net_pnl"] > 0])
        losses = len(day_df[day_df["net_pnl"] <= 0])
        total = len(day_df)

        result.append({
            "day": day,
            "label_es": DAYS_ES[day],
            "label_en": DAYS_EN[day],
            "trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total, 4) if total > 0 else 0.0,
            "net_pnl": round(float(day_df["net_pnl"].sum()), 2),
            "avg_pnl": round(float(day_df["net_pnl"].mean()), 2),
        })

    return result


def calculate_by_month(df: pd.DataFrame) -> list[dict]:
    """Calculate metrics by month."""
    if df.empty:
        return []

    result = []
    for month in sorted(df["month"].unique()):
        month_df = df[df["month"] == month]
        wins = len(month_df[month_df["net_pnl"] > 0])
        losses = len(month_df[month_df["net_pnl"] <= 0])
        total = len(month_df)

        result.append({
            "month": int(month),
            "label": f"{MONTHS_ES[int(month)]} {MONTHS_EN[int(month)]}",
            "trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total, 4) if total > 0 else 0.0,
            "net_pnl": round(float(month_df["net_pnl"].sum()), 2),
            "avg_pnl": round(float(month_df["net_pnl"].mean()), 2),
        })

    return result


def calculate_by_direction(df: pd.DataFrame) -> dict:
    """Calculate metrics by trade direction (Buy/Sell)."""
    if df.empty:
        return {"buy": {}, "sell": {}}

    result = {}
    for direction in ["Buy", "Sell"]:
        dir_df = df[df["direction"] == direction]
        if dir_df.empty:
            result[direction.lower()] = {
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "net_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
            }
            continue

        wins = len(dir_df[dir_df["net_pnl"] > 0])
        losses = len(dir_df[dir_df["net_pnl"] <= 0])
        total = len(dir_df)

        winners = dir_df[dir_df["net_pnl"] > 0]
        losers = dir_df[dir_df["net_pnl"] <= 0]

        result[direction.lower()] = {
            "trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total, 4) if total > 0 else 0.0,
            "net_pnl": round(float(dir_df["net_pnl"].sum()), 2),
            "avg_win": round(float(winners["net_pnl"].mean()), 2) if not winners.empty else 0.0,
            "avg_loss": round(float(losers["net_pnl"].mean()), 2) if not losers.empty else 0.0,
        }

    return result


def calculate_by_session(df: pd.DataFrame) -> list[dict]:
    """Calculate metrics by market session."""
    if df.empty:
        return []

    result = []
    for session in ["london_open", "ny_overlap", "ny_session", "off_hours"]:
        session_df = df[df["session"] == session]
        if session_df.empty:
            continue

        wins = len(session_df[session_df["net_pnl"] > 0])
        losses = len(session_df[session_df["net_pnl"] <= 0])
        total = len(session_df)

        result.append({
            "session": session,
            "label_es": SESSION_LABELS[session]["es"],
            "label_en": SESSION_LABELS[session]["en"],
            "trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total, 4) if total > 0 else 0.0,
            "net_pnl": round(float(session_df["net_pnl"].sum()), 2),
            "avg_pnl": round(float(session_df["net_pnl"].mean()), 2),
        })

    return result


def calculate_distribution(df: pd.DataFrame) -> list[dict]:
    """Calculate PnL distribution across fixed buckets."""
    if df.empty:
        return [{"range": r, "count": 0, "total_pnl": 0.0, "avg_pnl": 0.0} for r, _, _ in DISTRIBUTION_BUCKETS]

    result = []
    for label, low, high in DISTRIBUTION_BUCKETS:
        bucket_df = df[(df["net_pnl"] >= low) & (df["net_pnl"] < high)]
        count = len(bucket_df)
        total_pnl = round(float(bucket_df["net_pnl"].sum()), 2) if count > 0 else 0.0
        avg_pnl = round(float(bucket_df["net_pnl"].mean()), 2) if count > 0 else 0.0

        result.append({
            "range": label,
            "count": count,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
        })

    return result


def calculate_streaks(df: pd.DataFrame) -> dict:
    """Calculate win/loss streak data."""
    if df.empty:
        return {
            "max_win_streak": 0,
            "max_loss_streak": 0,
            "current_streak": 0,
            "loss_streak_3_plus_count": 0,
        }

    # Sort by trade number
    sorted_df = df.sort_values("trade_number")
    pnl_series = sorted_df["net_pnl"].values

    max_win = 0
    max_loss = 0
    current = 0
    loss_streak_3_plus = 0
    current_loss_streak = 0

    for pnl in pnl_series:
        if pnl > 0:
            # Winning trade
            if current > 0:
                current += 1
            else:
                current = 1
            current_loss_streak = 0
            max_win = max(max_win, current)
        else:
            # Losing trade (including zero)
            if current < 0:
                current -= 1
            else:
                current = -1
            current_loss_streak += 1
            max_loss = max(max_loss, abs(current))
            if current_loss_streak >= 3:
                loss_streak_3_plus += 1

    return {
        "max_win_streak": max_win,
        "max_loss_streak": max_loss,
        "current_streak": current,
        "loss_streak_3_plus_count": loss_streak_3_plus,
    }


def calculate_by_week(df: pd.DataFrame, threshold: int = 5) -> list[dict]:
    """Calculate metrics by week of year. Weeks with < threshold trades are excluded."""
    if df.empty or "week_of_year" not in df.columns:
        return []

    result = []
    for week in sorted(df["week_of_year"].unique()):
        week_df = df[df["week_of_year"] == week]
        if len(week_df) < threshold:
            continue

        wins = len(week_df[week_df["net_pnl"] > 0])
        losses = len(week_df[week_df["net_pnl"] <= 0])
        total = len(week_df)

        result.append({
            "week": int(week),
            "label": f"S{int(week):02d}",
            "trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total, 4) if total > 0 else 0.0,
            "net_pnl": round(float(week_df["net_pnl"].sum()), 2),
            "avg_pnl": round(float(week_df["net_pnl"].mean()), 2),
        })

    return result


def calculate_by_semester(df: pd.DataFrame) -> list[dict]:
    """Calculate metrics by semester (H1/H2)."""
    if df.empty or "month" not in df.columns:
        return []

    result = []
    for semester in [1, 2]:
        if semester == 1:
            sem_df = df[df["month"] <= 6]
            label = "H1 (Ene-Jun)"
        else:
            sem_df = df[df["month"] > 6]
            label = "H2 (Jul-Dic)"

        if sem_df.empty:
            continue

        wins = len(sem_df[sem_df["net_pnl"] > 0])
        losses = len(sem_df[sem_df["net_pnl"] <= 0])
        total = len(sem_df)

        result.append({
            "semester": semester,
            "label": label,
            "trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total, 4) if total > 0 else 0.0,
            "net_pnl": round(float(sem_df["net_pnl"].sum()), 2),
            "avg_pnl": round(float(sem_df["net_pnl"].mean()), 2),
        })

    return result


def calculate_by_year(df: pd.DataFrame, threshold: int = 5) -> list[dict]:
    """Calculate metrics by year. Years with < threshold trades are excluded."""
    if df.empty or "year" not in df.columns:
        return []

    result = []
    for year in sorted(df["year"].unique()):
        year_df = df[df["year"] == year]
        if len(year_df) < threshold:
            continue

        wins = len(year_df[year_df["net_pnl"] > 0])
        losses = len(year_df[year_df["net_pnl"] <= 0])
        total = len(year_df)

        result.append({
            "year": int(year),
            "label": str(int(year)),
            "trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total, 4) if total > 0 else 0.0,
            "net_pnl": round(float(year_df["net_pnl"].sum()), 2),
            "avg_pnl": round(float(year_df["net_pnl"].mean()), 2),
        })

    return result


def calculate_simulations(df: pd.DataFrame) -> dict:
    """Calculate what-if simulation results."""
    if df.empty:
        return {
            "sim_max_loss_5_pnl": 0.0,
            "sim_best_3_hours_pnl": 0.0,
        }

    # Simulation 1: Cap each loss at -$5
    sim_pnl = 0.0
    for _, row in df.iterrows():
        pnl = row["net_pnl"]
        if pnl < -5:
            sim_pnl += -5
        else:
            sim_pnl += pnl

    # Simulation 2: Best 3 hours by total PnL
    hourly_pnl = df.groupby("hour_of_day")["net_pnl"].sum()
    best_3_hours = hourly_pnl.nlargest(3).index.tolist()
    sim_best_3 = float(df[df["hour_of_day"].isin(best_3_hours)]["net_pnl"].sum())

    return {
        "sim_max_loss_5_pnl": round(sim_pnl, 2),
        "sim_best_3_hours_pnl": round(sim_best_3, 2),
    }
