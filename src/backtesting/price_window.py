"""Historical price window extraction for dynamic strategies."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


class InsufficientDataError(Exception):
    """Raised when insufficient historical data available for calculation."""

    pass


@dataclass
class PriceWindow:
    """Extracted historical price data for strategy calculations.

    Attributes:
        start_date: First date in window
        end_date: Last date in window (inclusive)
        prices: Prices indexed by date, columns = symbols
        num_days: Actual number of trading days in window
    """

    start_date: date
    end_date: date
    prices: pd.DataFrame
    num_days: int

    def get_asset_prices(self, symbol: str) -> pd.Series:
        """Get price series for specific asset."""
        if symbol not in self.prices.columns:
            raise ValueError(f"Asset {symbol} not found in price window")
        return self.prices[symbol]

    def has_complete_data(self, symbol: str) -> bool:
        """Check if asset has all non-null prices in window."""
        if symbol not in self.prices.columns:
            return False
        return self.prices[symbol].notna().all()

    def get_complete_assets(self) -> list[str]:
        """Return list of assets with complete (no missing) data."""
        complete = []
        for symbol in self.prices.columns:
            if self.has_complete_data(symbol):
                complete.append(symbol)
        return complete

    def validate(self) -> None:
        """Validate window data structure.

        Raises:
            ValueError: If window invalid
        """
        # Check DataFrame not empty
        if self.prices.empty:
            raise ValueError("Price window DataFrame is empty")

        # Check end_date > start_date
        if self.end_date <= self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) must be after start_date ({self.start_date})"
            )

        # Check num_days matches DataFrame length
        if self.num_days != len(self.prices):
            raise ValueError(
                f"num_days ({self.num_days}) does not match DataFrame length ({len(self.prices)})"
            )

        # Check all prices non-negative
        if (self.prices < 0).any().any():
            raise ValueError("Price window contains negative prices")


def get_price_window(
    prices_df: pd.DataFrame,
    calculation_date: date,
    lookback_days: int,
    assets: list[str],
) -> PriceWindow:
    """Extract price window ending at calculation_date (exclusive).

    Args:
        prices_df: DataFrame with columns [date, symbol, price]
        calculation_date: Date for which to calculate weights
        lookback_days: Number of trading days to look back
        assets: List of asset symbols to include

    Returns:
        PriceWindow with prices for lookback window, pivoted by symbol

    Raises:
        InsufficientDataError: If fewer than lookback_days available
    """
    # Filter to dates before calculation_date (convert to pd.Timestamp for comparison)
    calc_ts = pd.Timestamp(calculation_date)
    historical_data = prices_df[prices_df["date"] < calc_ts].copy()

    # Filter to required assets
    asset_data = historical_data[historical_data["symbol"].isin(assets)]

    # Get last N days per asset
    window_data_list = []
    for asset in assets:
        asset_prices = asset_data[asset_data["symbol"] == asset].sort_values("date")
        asset_window = asset_prices.tail(lookback_days)

        # Check if sufficient data exists
        if len(asset_window) < lookback_days:
            raise InsufficientDataError(
                f"{asset}: only {len(asset_window)} days available, need {lookback_days}"
            )

        window_data_list.append(asset_window)

    # Combine all assets
    window_data = pd.concat(window_data_list, ignore_index=True)

    # Pivot to get prices by date x symbol
    pivot_data = window_data.pivot(index="date", columns="symbol", values="price")

    # Ensure all assets present
    for asset in assets:
        if asset not in pivot_data.columns:
            raise InsufficientDataError(f"{asset}: no data found in window")

    # Get date range
    dates = pivot_data.index
    start_date = dates.min().date() if hasattr(dates.min(), "date") else dates.min()
    end_date = dates.max().date() if hasattr(dates.max(), "date") else dates.max()

    price_window = PriceWindow(
        start_date=start_date,
        end_date=end_date,
        prices=pivot_data,
        num_days=len(pivot_data),
    )

    price_window.validate()
    return price_window
