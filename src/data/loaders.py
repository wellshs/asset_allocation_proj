"""Data loading implementations."""

from pathlib import Path
from datetime import date
import pandas as pd

from .providers import HistoricalDataProvider
from .validation import validate_price_data
from ..backtesting.exceptions import DataError


class CSVDataProvider(HistoricalDataProvider):
    """Load historical price data from CSV files."""

    def __init__(self, data_dir: Path | str):
        """Initialize CSV data provider.

        Args:
            data_dir: Directory containing CSV price data files
        """
        self.data_dir = Path(data_dir)

    def load_prices(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Load historical price data for symbols from CSV files.

        Expected CSV format:
            date,symbol,price,currency
            2010-01-04,SPY,112.37,USD

        Args:
            symbols: List of asset symbols to load
            start_date: Start date of data range
            end_date: End date of data range

        Returns:
            DataFrame with columns: date, symbol, price, currency

        Raises:
            DataError: If files not found or data invalid
        """
        all_data = []

        for symbol in symbols:
            # Try to find CSV file for this symbol
            csv_path = self.data_dir / f"{symbol.lower()}_*.csv"
            matching_files = list(self.data_dir.glob(f"{symbol.lower()}_*.csv"))

            if not matching_files:
                # Try exact symbol name
                csv_path = self.data_dir / f"{symbol}.csv"
                matching_files = [csv_path] if csv_path.exists() else []

            if not matching_files:
                raise DataError(f"No CSV file found for symbol {symbol} in {self.data_dir}")

            # Load the first matching file
            try:
                df = pd.read_csv(matching_files[0])
            except Exception as e:
                raise DataError(f"Failed to read CSV for {symbol}: {e}")

            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'])

            # Filter by symbol (in case file contains multiple symbols)
            df = df[df['symbol'] == symbol].copy()

            all_data.append(df)

        # Combine all symbol data
        if not all_data:
            raise DataError("No data loaded")

        combined_df = pd.concat(all_data, ignore_index=True)

        # Filter by date range
        combined_df = combined_df[
            (combined_df['date'] >= pd.Timestamp(start_date)) &
            (combined_df['date'] <= pd.Timestamp(end_date))
        ].copy()

        if combined_df.empty:
            raise DataError(f"No data found for date range {start_date} to {end_date}")

        # Validate the data
        self.validate_data(combined_df)

        # Sort by date and symbol
        combined_df = combined_df.sort_values(['date', 'symbol']).reset_index(drop=True)

        return combined_df

    def validate_data(self, df: pd.DataFrame) -> None:
        """Validate price data structure and contents.

        Args:
            df: DataFrame to validate

        Raises:
            DataError: If validation fails
        """
        validate_price_data(df)
