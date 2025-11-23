"""Data provider interfaces."""

from abc import ABC, abstractmethod
from datetime import date
import pandas as pd


class HistoricalDataProvider(ABC):
    """Abstract interface for loading historical price data."""

    @abstractmethod
    def load_prices(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Load historical price data for symbols.

        Args:
            symbols: List of asset symbols to load
            start_date: Start date of data range
            end_date: End date of data range

        Returns:
            DataFrame with columns: date, symbol, price, currency
            Index: None (flat structure)

        Raises:
            DataError: If required data unavailable or invalid
        """
        pass


class ExchangeRateProvider(ABC):
    """Abstract interface for fetching exchange rate data."""

    @abstractmethod
    def fetch_rates(
        self,
        base_currency: str,
        target_currencies: list[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Fetch historical exchange rates.

        Args:
            base_currency: Base currency (ISO 4217 code)
            target_currencies: List of target currencies
            start_date: Start date of rate range
            end_date: End date of rate range

        Returns:
            DataFrame with columns: date, from_currency, to_currency, rate
            Example: USD to EUR on 2020-01-01 = 0.89

        Raises:
            APIError: If external API fails
            DataError: If invalid currency codes
        """
        pass
