"""Diagnose the actual data available in fixtures."""

import pandas as pd
from pathlib import Path

fixtures_dir = Path(__file__).parent / "tests" / "fixtures"

# Load SPY data
spy_data = pd.read_csv(fixtures_dir / "spy_2010_2020.csv")
agg_data = pd.read_csv(fixtures_dir / "agg_2010_2020.csv")

print("=" * 60)
print("Test Fixture Data Diagnosis")
print("=" * 60)
print()

print("SPY Data:")
print(f"  Total records: {len(spy_data)}")
print(f"  Date range: {spy_data['date'].min()} to {spy_data['date'].max()}")
print(f"  Unique dates: {spy_data['date'].nunique()}")
print()

print("AGG Data:")
print(f"  Total records: {len(agg_data)}")
print(f"  Date range: {agg_data['date'].min()} to {agg_data['date'].max()}")
print(f"  Unique dates: {agg_data['date'].nunique()}")
print()

print("SPY Dates:")
for i, row in spy_data.iterrows():
    print(f"  {row['date']}: ${row['price']}")
print()

print("=" * 60)
print("⚠️  ISSUE IDENTIFIED")
print("=" * 60)
print()
print("The test fixtures contain only SAMPLE data (15 days total).")
print("Running a backtest from 2000-2025 with only 15 days of data")
print("causes annualized return calculations to be distorted.")
print()
print("Calculation:")
print(f"  Actual trading days: {len(spy_data)}")
print("  Annualized formula: (1 + total_return)^(252/days) - 1")
print("  With 15 days: (1 + return)^(252/15) = (1 + return)^16.8")
print("  This exponential amplification creates unrealistic numbers!")
print()
print("=" * 60)
print("SOLUTION")
print("=" * 60)
print()
print("Option 1: Use the actual date range of available data")
print("  start_date=date(2010, 1, 4)")
print("  end_date=date(2010, 12, 31)")
print()
print("Option 2: Download full historical data for 2000-2025")
print("  - Use Yahoo Finance, Alpha Vantage, or other sources")
print("  - Create complete daily price files")
print()
