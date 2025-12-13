"""Data downloader utility with error handling.

This module provides a reusable data downloader for fetching historical price data
from Yahoo Finance with proper error handling and retry logic.
"""

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    raise ImportError(
        "yfinance is required for data downloading. Install with: pip install yfinance"
    )


class DataDownloadError(Exception):
    """Exception raised when data download fails."""

    pass


def download_price_data(
    symbol: str,
    start_date: str = "2019-01-01",
    end_date: str = "2024-12-31",
    progress: bool = False,
) -> pd.DataFrame:
    """Download historical price data from Yahoo Finance.

    Args:
        symbol: Ticker symbol (e.g., "SPY", "TQQQ")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        progress: Show download progress bar

    Returns:
        DataFrame with OHLCV data and DatetimeIndex

    Raises:
        DataDownloadError: If download fails or returns empty data
        ValueError: If dates are invalid

    Example:
        >>> data = download_price_data("SPY", "2020-01-01", "2024-12-31")
        >>> print(data.head())
    """
    # Validate inputs
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty")

    try:
        # Parse dates to validate format
        pd.to_datetime(start_date)
        pd.to_datetime(end_date)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid date format: {e}") from e

    # Attempt download with error handling
    try:
        print(f"Downloading {symbol} data from {start_date} to {end_date}...")

        data = yf.download(
            symbol,
            start=start_date,
            end=end_date,
            progress=progress,
            auto_adjust=True,  # Use adjusted prices
        )

        # Check if download succeeded
        if data.empty:
            raise DataDownloadError(
                f"No data returned for {symbol}. "
                f"Check if symbol is valid and date range has data."
            )

        # Validate required columns
        if "Close" not in data.columns:
            raise DataDownloadError(
                f"Downloaded data missing 'Close' column for {symbol}"
            )

        print(f"Downloaded {len(data)} days of data")
        print(f"Date range: {data.index[0].date()} to {data.index[-1].date()}")

        return data

    except Exception as e:
        # Catch network errors, API errors, etc.
        if isinstance(e, DataDownloadError):
            raise

        raise DataDownloadError(
            f"Failed to download data for {symbol}: {type(e).__name__}: {e}"
        ) from e


def download_multiple_symbols(
    symbols: list[str],
    start_date: str = "2019-01-01",
    end_date: str = "2024-12-31",
    progress: bool = False,
) -> dict[str, pd.DataFrame]:
    """Download data for multiple symbols.

    Args:
        symbols: List of ticker symbols
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        progress: Show download progress bar

    Returns:
        Dictionary mapping symbol to DataFrame

    Raises:
        DataDownloadError: If all downloads fail
        ValueError: If symbols list is empty

    Example:
        >>> data = download_multiple_symbols(["SPY", "QQQ"], "2020-01-01")
        >>> print(data["SPY"].head())
    """
    if not symbols:
        raise ValueError("Symbols list cannot be empty")

    results = {}
    errors = []

    for symbol in symbols:
        try:
            results[symbol] = download_price_data(
                symbol, start_date, end_date, progress
            )
        except DataDownloadError as e:
            errors.append(f"{symbol}: {e}")
            print(f"Warning: Failed to download {symbol}: {e}")

    if not results:
        raise DataDownloadError("All downloads failed. Errors:\n" + "\n".join(errors))

    return results
