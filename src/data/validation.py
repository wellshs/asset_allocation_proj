"""Data validation utilities."""

from datetime import date

import pandas as pd

from ..backtesting.exceptions import DataError


def validate_price_data(df: pd.DataFrame) -> None:
    """Validate historical price data structure and contents.

    Args:
        df: DataFrame to validate

    Raises:
        DataError: If validation fails
    """
    # Check required columns
    required_columns = {"date", "symbol", "price", "currency"}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise DataError(f"Missing required columns: {missing}")

    # Check for zero or negative prices
    if (df["price"] <= 0).any():
        invalid = df[df["price"] <= 0]
        raise DataError(f"Invalid prices found (must be > 0):\n{invalid}")

    # Check for duplicates
    duplicates = df.duplicated(subset=["date", "symbol"], keep=False)
    if duplicates.any():
        raise DataError(f"Duplicate entries found:\n{df[duplicates]}")

    # Verify chronological order within each symbol
    for symbol in df["symbol"].unique():
        symbol_data = df[df["symbol"] == symbol].sort_values("date")
        if not symbol_data["date"].is_monotonic_increasing:
            raise DataError(f"Dates not chronological for {symbol}")


def validate_exchange_rate_data(df: pd.DataFrame) -> None:
    """Validate exchange rate data structure and contents.

    Args:
        df: DataFrame to validate

    Raises:
        DataError: If validation fails
    """
    # Check required columns
    required_columns = {"date", "from_currency", "to_currency", "rate"}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise DataError(f"Missing required columns: {missing}")

    # Check for zero or negative rates
    if (df["rate"] <= 0).any():
        invalid = df[df["rate"] <= 0]
        raise DataError(f"Invalid exchange rates found (must be > 0):\n{invalid}")

    # Check for duplicates
    duplicates = df.duplicated(
        subset=["date", "from_currency", "to_currency"], keep=False
    )
    if duplicates.any():
        raise DataError(f"Duplicate entries found:\n{df[duplicates]}")

    # Verify chronological order within each currency pair
    for _, group_df in df.groupby(["from_currency", "to_currency"]):
        if not group_df["date"].is_monotonic_increasing:
            pair = (
                f"{group_df.iloc[0]['from_currency']}/{group_df.iloc[0]['to_currency']}"
            )
            raise DataError(f"Dates not chronological for {pair}")


def validate_lookback_data(
    df: pd.DataFrame,
    calculation_date: date,
    lookback_days: int,
    assets: list[str],
) -> None:
    """Validate sufficient data exists for lookback window.

    Args:
        df: Price data DataFrame with columns [date, symbol, price]
        calculation_date: Date for weight calculation
        lookback_days: Required lookback period
        assets: Assets to validate

    Raises:
        DataError: If insufficient data for any asset
    """
    historical_data = df[df["date"] < calculation_date]

    for asset in assets:
        asset_data = historical_data[historical_data["symbol"] == asset]
        available_days = len(asset_data)

        if available_days < lookback_days:
            raise DataError(
                f"{asset}: only {available_days} days available before {calculation_date}, "
                f"need {lookback_days} for lookback window"
            )
