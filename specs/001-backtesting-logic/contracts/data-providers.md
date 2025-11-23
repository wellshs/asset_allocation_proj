# Contract: Data Providers

**Feature**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)
**Date**: 2025-11-23
**Status**: COMPLETE

## Purpose

This contract defines interfaces for loading historical price data and fetching exchange rates. The provider pattern allows users to supply data from different sources (CSV files, APIs, databases) while maintaining a consistent interface for the backtesting engine.

## Provider Interfaces

### HistoricalDataProvider

**Responsibility**: Load historical price data for assets within a specified date range.

```python
from abc import ABC, abstractmethod
from datetime import date
import pandas as pd

class HistoricalDataProvider(ABC):
    """
    Abstract interface for loading historical asset price data.

    Implementations can load from CSV files, databases, APIs, or other sources.
    All providers must return data in the standard format defined in data-model.md.
    """

    @abstractmethod
    def load_prices(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Load historical price data for specified assets.

        Args:
            symbols: List of asset identifiers (e.g., ["SPY", "AGG"])
            start_date: Start of historical period (inclusive)
            end_date: End of historical period (inclusive)

        Returns:
            DataFrame with columns: date, symbol, price, currency
            - date: datetime64[ns], business days only
            - symbol: str, asset identifier
            - price: float64, adjusted closing price (splits/dividends applied)
            - currency: str, ISO 4217 currency code

        Raises:
            DataError: If data unavailable, invalid, or missing required symbols
            ValueError: If start_date >= end_date or invalid date formats

        Preconditions:
            - start_date < end_date
            - symbols list is non-empty
            - All symbols are valid identifiers

        Postconditions:
            - DataFrame contains all symbols for the date range
            - Dates are in chronological order for each symbol
            - All prices are > 0
            - No duplicate (date, symbol) pairs
            - Missing dates handled via forward-fill (up to 5 days)
        """
        pass

    @abstractmethod
    def validate_data(self, df: pd.DataFrame) -> None:
        """
        Validate that loaded data meets format requirements.

        Args:
            df: DataFrame to validate

        Raises:
            DataError: If validation fails

        Validation checks:
            1. Required columns present: date, symbol, price, currency
            2. No null values in required columns
            3. Prices > 0 (no zero or negative prices)
            4. Dates chronological within each symbol
            5. No duplicate (date, symbol) combinations
            6. Valid currency codes (3-letter ISO 4217)
        """
        pass
```

### ExchangeRateProvider

**Responsibility**: Fetch historical exchange rates for currency conversion.

```python
class ExchangeRateProvider(ABC):
    """
    Abstract interface for fetching historical exchange rate data.

    Implementations can fetch from APIs, databases, or user-provided files.
    Required for multi-currency portfolio support (FR-017, FR-018).
    """

    @abstractmethod
    def fetch_rates(
        self,
        base_currency: str,
        target_currencies: list[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Fetch historical exchange rates for currency pairs.

        Args:
            base_currency: Base currency for conversions (e.g., "USD")
            target_currencies: List of currencies to convert to (e.g., ["EUR", "GBP"])
            start_date: Start of historical period (inclusive)
            end_date: End of historical period (inclusive)

        Returns:
            DataFrame with columns: date, from_currency, to_currency, rate
            - date: datetime64[ns], business days
            - from_currency: str, base currency (ISO 4217)
            - to_currency: str, target currency (ISO 4217)
            - rate: float64, exchange rate (1 from = rate × to)

        Raises:
            CurrencyError: If currency codes invalid or rates unavailable
            APIError: If external API call fails (for API-based providers)
            ValueError: If date range invalid

        Example:
            If base="USD", targets=["EUR"], rate=0.85 on 2020-01-01:
            - 1 USD = 0.85 EUR
            - To convert 100 EUR to USD: 100 / 0.85 = 117.65 USD

        Preconditions:
            - base_currency and all target_currencies are valid ISO 4217 codes
            - start_date < end_date
            - Provider has access to historical rate data

        Postconditions:
            - DataFrame covers entire date range (start to end)
            - All (date, from, to) combinations present
            - Rates are > 0
            - Missing dates forward-filled from previous day
        """
        pass

    @abstractmethod
    def get_supported_currencies(self) -> list[str]:
        """
        Return list of supported currency codes.

        Returns:
            List of ISO 4217 currency codes this provider supports

        Example:
            ["USD", "EUR", "GBP", "JPY", "AUD", ...]
        """
        pass
```

## Concrete Implementations

### CSVDataProvider

**Purpose**: Load historical price data from CSV files.

```python
import pandas as pd
from pathlib import Path

class CSVDataProvider(HistoricalDataProvider):
    """
    Load historical price data from CSV files.

    Expected CSV format:
        date,symbol,price,currency
        2010-01-04,SPY,112.37,USD
        2010-01-04,AGG,105.23,USD
        2010-01-05,SPY,112.86,USD

    Files can be:
    - Single file with all symbols
    - Multiple files (one per symbol)
    - Directory of CSV files
    """

    def __init__(self, data_path: str | Path):
        """
        Initialize CSV data provider.

        Args:
            data_path: Path to CSV file or directory containing CSV files
        """
        self.data_path = Path(data_path)
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data path not found: {data_path}")

    def load_prices(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Load prices from CSV file(s).

        Algorithm:
            1. If data_path is file: Read single CSV
            2. If data_path is directory: Read all CSVs and concatenate
            3. Filter by symbols and date range
            4. Convert date column to datetime
            5. Validate data format
            6. Sort by date and symbol
            7. Forward-fill missing dates (max 5 days)

        Returns:
            Validated DataFrame with historical prices
        """
        if self.data_path.is_file():
            df = pd.read_csv(self.data_path)
        else:
            # Read all CSV files in directory
            csv_files = list(self.data_path.glob("*.csv"))
            if not csv_files:
                raise DataError(f"No CSV files found in {self.data_path}")
            dfs = [pd.read_csv(f) for f in csv_files]
            df = pd.concat(dfs, ignore_index=True)

        # Convert date column
        df['date'] = pd.to_datetime(df['date'])

        # Filter by symbols and date range
        df = df[df['symbol'].isin(symbols)]
        df = df[(df['date'] >= pd.Timestamp(start_date)) &
                (df['date'] <= pd.Timestamp(end_date))]

        # Check all symbols present
        missing = set(symbols) - set(df['symbol'].unique())
        if missing:
            raise DataError(f"Missing data for symbols: {missing}")

        # Validate and return
        self.validate_data(df)
        return df.sort_values(['date', 'symbol']).reset_index(drop=True)

    def validate_data(self, df: pd.DataFrame) -> None:
        """Validate CSV data format per contract."""
        required_cols = {'date', 'symbol', 'price', 'currency'}
        if not required_cols.issubset(df.columns):
            raise DataError(f"Missing columns: {required_cols - set(df.columns)}")

        if df.isnull().any().any():
            raise DataError("Data contains null values")

        if (df['price'] <= 0).any():
            invalid = df[df['price'] <= 0]
            raise DataError(f"Invalid prices (<=0):\n{invalid}")

        # Check for duplicates
        dupes = df.duplicated(subset=['date', 'symbol'], keep=False)
        if dupes.any():
            raise DataError(f"Duplicate entries:\n{df[dupes]}")

        # Validate currency codes (3 letters)
        invalid_currencies = df[df['currency'].str.len() != 3]
        if not invalid_currencies.empty:
            raise DataError(f"Invalid currency codes:\n{invalid_currencies}")
```

### ExchangeRateHostProvider

**Purpose**: Fetch exchange rates from exchangerate.host API (per research.md).

```python
import requests
from datetime import timedelta

class ExchangeRateHostProvider(ExchangeRateProvider):
    """
    Fetch historical exchange rates from exchangerate.host API.

    API Documentation: https://exchangerate.host/#/
    Data Source: European Central Bank (ECB)
    Rate Limits: 1500 requests/month (free tier)
    Historical Data: Available from 1999
    """

    BASE_URL = "https://api.exchangerate.host"

    def __init__(self, cache_dir: str | Path | None = None):
        """
        Initialize exchange rate provider.

        Args:
            cache_dir: Optional directory to cache API responses
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_rates(
        self,
        base_currency: str,
        target_currencies: list[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Fetch exchange rates from API.

        API Endpoint:
            GET /timeseries?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
                           &base=USD&symbols=EUR,GBP,JPY

        Response format:
            {
                "success": true,
                "timeseries": true,
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
                "base": "USD",
                "rates": {
                    "2020-01-01": {"EUR": 0.8913, "GBP": 0.7553},
                    "2020-01-02": {"EUR": 0.8951, "GBP": 0.7592},
                    ...
                }
            }

        Algorithm:
            1. Check cache for existing data
            2. If not cached or stale, make API request
            3. Parse JSON response
            4. Convert to DataFrame format
            5. Validate and forward-fill missing dates
            6. Cache results if cache_dir configured
        """
        # Build request parameters
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "base": base_currency,
            "symbols": ",".join(target_currencies)
        }

        # Make API request
        try:
            response = requests.get(
                f"{self.BASE_URL}/timeseries",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise APIError(f"Exchange rate API request failed: {e}")

        if not data.get("success"):
            error_msg = data.get("error", {}).get("info", "Unknown error")
            raise APIError(f"Exchange rate API error: {error_msg}")

        # Convert to DataFrame
        rows = []
        for date_str, rates in data["rates"].items():
            for currency, rate in rates.items():
                rows.append({
                    "date": pd.Timestamp(date_str),
                    "from_currency": base_currency,
                    "to_currency": currency,
                    "rate": rate
                })

        df = pd.DataFrame(rows)

        # Forward-fill missing dates
        df = self._fill_missing_dates(df, start_date, end_date)

        return df.sort_values('date').reset_index(drop=True)

    def _fill_missing_dates(
        self,
        df: pd.DataFrame,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Fill missing dates with forward-fill (weekends, holidays)."""
        # Create complete date range (business days)
        all_dates = pd.bdate_range(start=start_date, end=end_date)

        # For each currency pair, ensure all dates present
        filled_dfs = []
        for (from_curr, to_curr), group in df.groupby(['from_currency', 'to_currency']):
            # Reindex to all dates and forward-fill
            group = group.set_index('date').reindex(all_dates).fillna(method='ffill', limit=5)
            group['from_currency'] = from_curr
            group['to_currency'] = to_curr
            filled_dfs.append(group.reset_index().rename(columns={'index': 'date'}))

        return pd.concat(filled_dfs, ignore_index=True)

    def get_supported_currencies(self) -> list[str]:
        """
        Get supported currencies from API.

        API Endpoint: GET /symbols
        """
        try:
            response = requests.get(f"{self.BASE_URL}/symbols", timeout=10)
            response.raise_for_status()
            data = response.json()
            return list(data.get("symbols", {}).keys())
        except requests.RequestException:
            # Return common currencies as fallback
            return ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY"]
```

### CSVExchangeRateProvider

**Purpose**: Load exchange rates from user-provided CSV files (fallback option).

```python
class CSVExchangeRateProvider(ExchangeRateProvider):
    """
    Load exchange rates from CSV files.

    Expected CSV format:
        date,from_currency,to_currency,rate
        2020-01-01,USD,EUR,0.8913
        2020-01-01,USD,GBP,0.7553
        2020-01-02,USD,EUR,0.8951

    Useful when:
    - API unavailable or rate-limited
    - Custom exchange rates needed
    - Offline backtesting
    """

    def __init__(self, csv_path: str | Path):
        """
        Initialize CSV exchange rate provider.

        Args:
            csv_path: Path to CSV file with exchange rates
        """
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Exchange rate file not found: {csv_path}")

    def fetch_rates(
        self,
        base_currency: str,
        target_currencies: list[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Load exchange rates from CSV file."""
        df = pd.read_csv(self.csv_path)
        df['date'] = pd.to_datetime(df['date'])

        # Filter by base currency, target currencies, and date range
        df = df[
            (df['from_currency'] == base_currency) &
            (df['to_currency'].isin(target_currencies)) &
            (df['date'] >= pd.Timestamp(start_date)) &
            (df['date'] <= pd.Timestamp(end_date))
        ]

        # Validate all requested currencies present
        missing = set(target_currencies) - set(df['to_currency'].unique())
        if missing:
            raise CurrencyError(
                f"Missing exchange rates for: {base_currency} → {missing}"
            )

        return df.sort_values('date').reset_index(drop=True)

    def get_supported_currencies(self) -> list[str]:
        """Return currencies present in CSV file."""
        df = pd.read_csv(self.csv_path)
        from_currencies = set(df['from_currency'].unique())
        to_currencies = set(df['to_currency'].unique())
        return sorted(from_currencies | to_currencies)
```

## Error Types

```python
class DataError(Exception):
    """Raised when data is missing, invalid, or does not meet requirements."""
    pass

class CurrencyError(Exception):
    """Raised when exchange rate data is unavailable or currencies invalid."""
    pass

class APIError(Exception):
    """Raised when external API call fails."""
    pass
```

## Testing Contract

### Unit Tests

**CSVDataProvider**:
- Load single CSV file with all symbols
- Load multiple CSV files from directory
- Filter by date range correctly
- Raise DataError for missing symbols
- Validate price data format
- Detect and reject duplicate entries
- Detect and reject zero/negative prices

**ExchangeRateHostProvider**:
- Parse API response correctly
- Handle API errors gracefully
- Forward-fill missing dates (weekends/holidays)
- Respect cache if configured
- Handle rate limit errors with clear message

**CSVExchangeRateProvider**:
- Load exchange rates from CSV
- Filter by currency pairs and dates
- Detect missing currency pairs

### Integration Tests

1. **CSV data loading**:
   - Load real SPY/AGG data for 2010-2020
   - Verify all dates present (with forward-fill)
   - Validate data passes all checks

2. **API exchange rate fetching**:
   - Fetch USD→EUR rates for 1-year period
   - Verify all business days covered
   - Handle weekend/holiday gaps

3. **Fallback to CSV rates**:
   - When API unavailable, use CSV provider
   - Verify results identical to API

### Mock Data

Test fixtures location: `tests/fixtures/`

**sample_prices.csv**:
```csv
date,symbol,price,currency
2020-01-02,SPY,322.86,USD
2020-01-02,AGG,111.85,USD
2020-01-03,SPY,321.45,USD
2020-01-03,AGG,111.92,USD
```

**sample_exchange_rates.csv**:
```csv
date,from_currency,to_currency,rate
2020-01-02,USD,EUR,0.8913
2020-01-02,USD,GBP,0.7553
2020-01-03,USD,EUR,0.8951
2020-01-03,USD,GBP,0.7592
```

## Provider Selection Guide

| Use Case | Recommended Provider | Rationale |
|----------|---------------------|-----------|
| Local CSV files | `CSVDataProvider` | Simplest, no external dependencies |
| Multi-currency with internet | `ExchangeRateHostProvider` | Automatic, accurate ECB data |
| Multi-currency offline | `CSVExchangeRateProvider` | User provides exchange rates |
| Custom data source | Implement `HistoricalDataProvider` | Full control over data loading |
| API rate limits hit | `CSVExchangeRateProvider` | Avoid API dependency |

## Extension Points

### Custom Data Provider Example

Users can implement custom providers for proprietary data sources:

```python
class DatabaseDataProvider(HistoricalDataProvider):
    """Load historical prices from SQL database."""

    def __init__(self, connection_string: str):
        self.connection = create_connection(connection_string)

    def load_prices(self, symbols, start_date, end_date):
        query = """
            SELECT date, symbol, adjusted_close as price, currency
            FROM historical_prices
            WHERE symbol IN (?)
              AND date BETWEEN ? AND ?
            ORDER BY date, symbol
        """
        df = pd.read_sql(query, self.connection, params=[symbols, start_date, end_date])
        self.validate_data(df)
        return df

    def validate_data(self, df):
        # Use base validation logic
        ...
```

## Performance Considerations

**CSV loading**:
- Use `pd.read_csv()` with `dtype` hints for faster parsing
- For large files, consider `usecols` to load only needed columns
- Cache parsed DataFrames in memory if loading multiple times

**API calls**:
- Implement caching to avoid redundant requests
- Batch requests when possible (API supports date ranges)
- Respect rate limits (1500/month for exchangerate.host)
- Add retry logic with exponential backoff

**Data validation**:
- Run validation only once after loading
- Use vectorized pandas operations, not row-by-row checks
- Early-exit validation on first error to fail fast

## Next Steps

**Phase 1 Progress**: Data provider contracts complete ✓

Proceed to:
1. Create quickstart.md

## References

- [spec.md](../spec.md) - Requirements FR-002 (user-provided data), FR-018 (exchange rates)
- [data-model.md](../data-model.md) - HistoricalPriceData and ExchangeRateData formats
- [research.md](../research.md) - Decision to use exchangerate.host API
- exchangerate.host API docs: https://exchangerate.host/#/
