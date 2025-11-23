"""Download full historical data from Yahoo Finance."""

import yfinance as yf
import pandas as pd
from pathlib import Path


def download_ticker_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Download historical data for a ticker from Yahoo Finance.

    Args:
        symbol: Ticker symbol (e.g., 'SPY', 'AGG')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        DataFrame with date, symbol, and price columns
    """
    print(f"Downloading {symbol} data from {start_date} to {end_date}...")

    ticker = yf.Ticker(symbol)
    hist = ticker.history(start=start_date, end=end_date)

    # Use adjusted close price
    df = pd.DataFrame(
        {
            "date": hist.index.strftime("%Y-%m-%d"),
            "symbol": symbol,
            "price": hist["Close"].round(2),
            "currency": "USD",
        }
    )

    print(f"✓ Downloaded {len(df)} records for {symbol}")
    return df


def main():
    print("=" * 60)
    print("Historical Data Download")
    print("=" * 60)
    print()

    # Configuration
    start_date = "2000-01-01"
    end_date = "2025-11-23"
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"

    # Download SPY data
    spy_data = download_ticker_data("SPY", start_date, end_date)
    spy_file = fixtures_dir / "spy_2010_2020.csv"
    spy_data.to_csv(spy_file, index=False)
    print(f"✓ Saved to {spy_file}")
    print()

    # Download AGG data
    agg_data = download_ticker_data("AGG", start_date, end_date)
    agg_file = fixtures_dir / "agg_2010_2020.csv"
    agg_data.to_csv(agg_file, index=False)
    print(f"✓ Saved to {agg_file}")
    print()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"SPY: {len(spy_data)} trading days")
    print(f"  Date range: {spy_data['date'].min()} to {spy_data['date'].max()}")
    print()
    print(f"AGG: {len(agg_data)} trading days")
    print(f"  Date range: {agg_data['date'].min()} to {agg_data['date'].max()}")
    print()
    print("✓ Historical data download complete!")


if __name__ == "__main__":
    main()
