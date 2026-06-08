"""Column validation for CSV parsing."""

import pandas as pd

# Required columns for cTrader CSV format
REQUIRED_COLUMNS = [
    "Símbolo",
    "Dirección de apertura",
    "Hora de cierre (UTC-5)",
    "Precio de entrada",
    "Precio de cierre",
    "Cantidad de Cierre",
    "$ neto",
    "Saldo $",
]

# Column mapping to database fields
COLUMN_MAPPING = {
    "Símbolo": "symbol",
    "Dirección de apertura": "direction",
    "Hora de cierre (UTC-5)": "closed_at",
    "Precio de entrada": "entry_price",
    "Precio de cierre": "close_price",
    "Cantidad de Cierre": "lot_size",
    "$ neto": "net_pnl",
    "Saldo $": "balance",
}


def validate_columns(df: pd.DataFrame) -> list[str]:
    """
    Validate that all required columns exist in the DataFrame.
    
    Returns:
        List of missing column names (empty if all present)
    """
    missing = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing.append(col)
    return missing


def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map CSV column names to database field names.
    
    Returns:
        DataFrame with mapped column names
    """
    df_mapped = df.rename(columns=COLUMN_MAPPING)
    return df_mapped
