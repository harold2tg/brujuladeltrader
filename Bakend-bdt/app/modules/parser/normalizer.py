"""Data normalization for CSV parsing."""

import re
from datetime import datetime

import pandas as pd
import pytz


def clean_balance(value: str) -> float:
    """
    Clean balance value by removing \xa0 and spaces.
    
    Examples:
        "845.36" -> 845.36
        "1,234.56" -> 1234.56
        "845\xa036" -> 845.36
    """
    if pd.isna(value):
        return None
    
    # Convert to string and clean
    str_val = str(value)
    str_val = str_val.replace("\xa0", "").replace(" ", "").replace(",", "")
    
    try:
        return float(str_val)
    except ValueError:
        return None


def extract_lot_size(value: str) -> float:
    """
    Extract numeric value from lot size string.
    
    Examples:
        "0.02 Lotes" -> 0.02
        "0.01" -> 0.01
        "1 Lote" -> 1.0
    """
    if pd.isna(value):
        return None
    
    # Extract numeric part using regex
    match = re.search(r"[\d.]+", str(value))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def parse_datetime(date_str: str) -> datetime | None:
    """
    Parse datetime string in DD/MM/YYYY HH:MM:SS.fff format.
    
    Returns:
        timezone-aware datetime in UTC-5
    """
    if pd.isna(date_str):
        return None
    
    try:
        # Parse the datetime string
        dt = datetime.strptime(str(date_str), "%d/%m/%Y %H:%M:%S.%f")
        
        # Make timezone-aware (UTC-5)
        tz = pytz.timezone("America/Bogota")
        dt = tz.localize(dt)
        
        return dt
    except (ValueError, TypeError):
        return None


def parse_net_pnl(value: str) -> float | None:
    """
    Parse net PnL value.
    
    Examples:
        "0.10" -> 0.10
        "-4.94" -> -4.94
        "12.44" -> 12.44
    """
    if pd.isna(value):
        return None
    
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None
