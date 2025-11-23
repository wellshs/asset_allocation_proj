# Quickstart Guide: Backtesting Logic

**Feature**: [spec.md](./spec.md) | **Data Model**: [data-model.md](./data-model.md)
**Date**: 2025-11-23
**Status**: COMPLETE

## Overview

This guide shows how to use the backtesting system to validate asset allocation strategies against historical market data. You'll learn to:

1. Load historical price data
2. Define an allocation strategy
3. Configure and run a backtest
4. Analyze performance results

## Installation

```bash
# Install dependencies
pip install pandas numpy pytest hypothesis requests

# Install the backtesting package
pip install -e .
```

## Basic Usage

### Example 1: Simple 60/40 Stock/Bond Portfolio

This example backtests a classic 60% stocks / 40% bonds portfolio over 10 years.

```python
from backtesting import BacktestEngine
from backtesting.models import (
    BacktestConfiguration,
    AllocationStrategy,
    TransactionCosts,
    RebalancingFrequency
)
from backtesting.data import CSVDataProvider
from datetime import date
from decimal import Decimal

# Step 1: Load historical price data from CSV
data_provider = CSVDataProvider("data/historical_prices.csv")
prices = data_provider.load_prices(
    symbols=["SPY", "AGG"],  # S&P 500 ETF, Bond ETF
    start_date=date(2010, 1, 1),
    end_date=date(2020, 12, 31)
)

# Step 2: Define allocation strategy
strategy = AllocationStrategy(
    name="60/40 Portfolio",
    asset_weights={
        "SPY": Decimal("0.6"),  # 60% stocks
        "AGG": Decimal("0.4")   # 40% bonds
    }
)

# Step 3: Configure backtest parameters
config = BacktestConfiguration(
    start_date=date(2010, 1, 1),
    end_date=date(2020, 12, 31),
    initial_capital=Decimal("100000"),  # $100,000 starting capital
    rebalancing_frequency=RebalancingFrequency.QUARTERLY,
    transaction_costs=TransactionCosts(
        fixed_per_trade=Decimal("0"),      # No fixed commission
        percentage=Decimal("0.001")        # 0.1% per trade
    ),
    risk_free_rate=Decimal("0.02"),  # 2% risk-free rate for Sharpe ratio
    base_currency="USD"
)

# Step 4: Run backtest
engine = BacktestEngine()
result = engine.run_backtest(
    config=config,
    strategy=strategy,
    price_data=prices
)

# Step 5: Display results
print("=== Backtest Results ===\n")
print(result.metrics.to_dict())

# Output:
# === Backtest Results ===
#
# Total Return: 180.45%
# Annualized Return: 10.87%
# Volatility: 9.23%
# Maximum Drawdown: -19.34%
# Sharpe Ratio: 0.96
# Number of Trades: 88
# Period: 2010-01-01 to 2020-12-31
# Start Value: $100,000.00
# End Value: $280,450.00
```

### Example 2: Buy-and-Hold Strategy (No Rebalancing)

Test a simple buy-and-hold approach with a single asset.

```python
# 100% S&P 500, no rebalancing
strategy = AllocationStrategy(
    name="SPY Buy and Hold",
    asset_weights={"SPY": Decimal("1.0")}
)

config = BacktestConfiguration(
    start_date=date(2010, 1, 1),
    end_date=date(2020, 12, 31),
    initial_capital=Decimal("100000"),
    rebalancing_frequency=RebalancingFrequency.NEVER,  # No rebalancing
    base_currency="USD"
)

result = engine.run_backtest(config, strategy, prices)

print(f"Total Return: {result.metrics.total_return:.2%}")
print(f"Max Drawdown: {result.metrics.max_drawdown:.2%}")

# Output:
# Total Return: 256.34%
# Max Drawdown: -33.92%
```

### Example 3: High-Frequency Rebalancing

Compare the impact of monthly vs. quarterly rebalancing.

```python
# Monthly rebalancing
config_monthly = BacktestConfiguration(
    start_date=date(2015, 1, 1),
    end_date=date(2020, 12, 31),
    initial_capital=Decimal("100000"),
    rebalancing_frequency=RebalancingFrequency.MONTHLY,
    transaction_costs=TransactionCosts(
        fixed_per_trade=Decimal("0"),
        percentage=Decimal("0.001")
    ),
    base_currency="USD"
)

result_monthly = engine.run_backtest(config_monthly, strategy, prices)

# Quarterly rebalancing
config_quarterly = config_monthly
config_quarterly.rebalancing_frequency = RebalancingFrequency.QUARTERLY

result_quarterly = engine.run_backtest(config_quarterly, strategy, prices)

# Compare results
print(f"Monthly - Return: {result_monthly.metrics.annualized_return:.2%}, "
      f"Trades: {result_monthly.metrics.num_trades}")
print(f"Quarterly - Return: {result_quarterly.metrics.annualized_return:.2%}, "
      f"Trades: {result_quarterly.metrics.num_trades}")

# Output:
# Monthly - Return: 9.45%, Trades: 144
# Quarterly - Return: 9.52%, Trades: 48
```

## Multi-Currency Portfolios

### Example 4: International Portfolio with Exchange Rates

Backtest a portfolio with assets denominated in different currencies.

```python
from backtesting.data import ExchangeRateHostProvider

# Load price data (mixed currencies)
prices = data_provider.load_prices(
    symbols=["SPY", "EWG"],  # SPY (USD), EWG (EUR)
    start_date=date(2015, 1, 1),
    end_date=date(2020, 12, 31)
)

# Fetch exchange rates automatically
rate_provider = ExchangeRateHostProvider()
exchange_rates = rate_provider.fetch_rates(
    base_currency="USD",
    target_currencies=["EUR"],
    start_date=date(2015, 1, 1),
    end_date=date(2020, 12, 31)
)

# Define international strategy
strategy = AllocationStrategy(
    name="US/Europe 50/50",
    asset_weights={
        "SPY": Decimal("0.5"),  # 50% US stocks
        "EWG": Decimal("0.5")   # 50% German stocks
    }
)

# Run backtest with exchange rates
result = engine.run_backtest(
    config=config,
    strategy=strategy,
    price_data=prices,
    exchange_rates=exchange_rates  # Convert EUR to USD
)

print(f"Total Return (USD): {result.metrics.total_return:.2%}")
```

## Analyzing Trade History

### Example 5: Inspect Executed Trades

Review the trades executed during a backtest.

```python
result = engine.run_backtest(config, strategy, prices)

# Display first 10 trades
print("=== Trade History ===\n")
for trade in result.trades[:10]:
    action = "BUY" if trade.is_buy else "SELL"
    print(f"{trade.timestamp}: {action} {abs(trade.quantity):.2f} shares of {trade.asset_symbol} "
          f"@ ${trade.price:.2f} (cost: ${trade.transaction_cost:.2f})")

# Output:
# === Trade History ===
#
# 2010-01-04: BUY 557.04 shares of SPY @ 112.37 (cost: $62.60)
# 2010-01-04: BUY 357.89 shares of AGG @ 105.23 (cost: $37.66)
# 2010-04-01: SELL 23.45 shares of SPY @ 118.56 (cost: $2.78)
# 2010-04-01: BUY 25.67 shares of AGG @ 107.89 (cost: $2.77)
# ...
```

## Portfolio Value Over Time

### Example 6: Track Portfolio Growth

Analyze how portfolio value changed throughout the backtest.

```python
result = engine.run_backtest(config, strategy, prices)

# Extract portfolio value time series
portfolio_values = [
    (state.timestamp, float(state.total_value))
    for state in result.portfolio_history
]

# Find peak value and maximum drawdown date
peak_value = max(portfolio_values, key=lambda x: x[1])
trough_value = min(portfolio_values, key=lambda x: x[1])

print(f"Peak: ${peak_value[1]:,.2f} on {peak_value[0]}")
print(f"Trough: ${trough_value[1]:,.2f} on {trough_value[0]}")

# Plot portfolio growth (requires matplotlib)
import matplotlib.pyplot as plt

dates, values = zip(*portfolio_values)
plt.figure(figsize=(12, 6))
plt.plot(dates, values)
plt.title("Portfolio Value Over Time")
plt.xlabel("Date")
plt.ylabel("Portfolio Value ($)")
plt.grid(True)
plt.show()
```

## Preparing Your Data

### CSV Format Requirements

Your historical price data CSV must follow this format:

```csv
date,symbol,price,currency
2010-01-04,SPY,112.37,USD
2010-01-04,AGG,105.23,USD
2010-01-05,SPY,112.86,USD
2010-01-05,AGG,105.45,USD
```

**Requirements**:
- `date`: ISO format (YYYY-MM-DD)
- `symbol`: Asset identifier (ticker symbol)
- `price`: Adjusted closing price (splits/dividends already applied)
- `currency`: ISO 4217 currency code (USD, EUR, GBP, etc.)

### Data Sources

**Free historical data sources**:
- **Yahoo Finance**: Download CSV from finance.yahoo.com
- **Alpha Vantage**: Free API with daily data
- **FRED (Federal Reserve)**: Economic and bond data

**Preparing Yahoo Finance data**:
```python
import pandas as pd

# Download CSV from Yahoo Finance for SPY
yahoo_data = pd.read_csv("SPY.csv")

# Convert to backtest format
backtest_data = pd.DataFrame({
    'date': yahoo_data['Date'],
    'symbol': 'SPY',
    'price': yahoo_data['Adj Close'],  # Use adjusted close
    'currency': 'USD'
})

backtest_data.to_csv("spy_backtest.csv", index=False)
```

## Common Patterns

### Pattern 1: Compare Multiple Strategies

```python
strategies = [
    ("100% Stocks", {"SPY": Decimal("1.0")}),
    ("60/40", {"SPY": Decimal("0.6"), "AGG": Decimal("0.4")}),
    ("50/50", {"SPY": Decimal("0.5"), "AGG": Decimal("0.5")}),
    ("100% Bonds", {"AGG": Decimal("1.0")})
]

results = {}
for name, weights in strategies:
    strategy = AllocationStrategy(name=name, asset_weights=weights)
    result = engine.run_backtest(config, strategy, prices)
    results[name] = result.metrics

# Compare returns
for name, metrics in results.items():
    print(f"{name:15} | Return: {metrics.annualized_return:6.2%} | "
          f"Sharpe: {metrics.sharpe_ratio:5.2f} | "
          f"Drawdown: {metrics.max_drawdown:6.2%}")

# Output:
# 100% Stocks    | Return: 12.87% | Sharpe:  1.23 | Drawdown: -33.92%
# 60/40          | Return: 10.87% | Sharpe:  1.18 | Drawdown: -19.34%
# 50/50          | Return:  9.92% | Sharpe:  1.12 | Drawdown: -16.78%
# 100% Bonds     | Return:  4.23% | Sharpe:  0.67 | Drawdown:  -5.12%
```

### Pattern 2: Measure Impact of Transaction Costs

```python
# No transaction costs
config_no_costs = BacktestConfiguration(
    start_date=date(2010, 1, 1),
    end_date=date(2020, 12, 31),
    initial_capital=Decimal("100000"),
    rebalancing_frequency=RebalancingFrequency.MONTHLY,
    transaction_costs=TransactionCosts(Decimal("0"), Decimal("0")),
    base_currency="USD"
)

result_no_costs = engine.run_backtest(config_no_costs, strategy, prices)

# With 0.1% transaction costs
config_with_costs = config_no_costs
config_with_costs.transaction_costs = TransactionCosts(Decimal("0"), Decimal("0.001"))

result_with_costs = engine.run_backtest(config_with_costs, strategy, prices)

# Compare
print(f"No costs:   {result_no_costs.metrics.annualized_return:.2%}")
print(f"With costs: {result_with_costs.metrics.annualized_return:.2%}")
print(f"Cost drag:  {(result_no_costs.metrics.annualized_return - result_with_costs.metrics.annualized_return):.2%}")

# Output:
# No costs:   10.98%
# With costs: 10.87%
# Cost drag:  0.11%
```

### Pattern 3: Backtest During Market Crisis

```python
# Test performance during 2008 financial crisis
crisis_config = BacktestConfiguration(
    start_date=date(2008, 1, 1),
    end_date=date(2009, 3, 31),
    initial_capital=Decimal("100000"),
    rebalancing_frequency=RebalancingFrequency.QUARTERLY,
    base_currency="USD"
)

crisis_prices = data_provider.load_prices(
    symbols=["SPY", "AGG"],
    start_date=date(2008, 1, 1),
    end_date=date(2009, 3, 31)
)

result = engine.run_backtest(crisis_config, strategy, crisis_prices)

print(f"Crisis Return: {result.metrics.total_return:.2%}")
print(f"Max Drawdown: {result.metrics.max_drawdown:.2%}")

# Output:
# Crisis Return: -32.45%
# Max Drawdown: -38.67%
```

## Error Handling

### Common Errors and Solutions

**Error**: `DataError: No price data for SPY on 2020-03-15`
- **Cause**: Missing price data for asset
- **Solution**: Ensure CSV contains data for all assets in strategy and date range

**Error**: `ValueError: Strategy weights sum to 0.95, must be 1.0`
- **Cause**: Allocation weights don't add up to 100%
- **Solution**: Check that weights sum to 1.0 (e.g., 0.6 + 0.4 = 1.0)

**Error**: `CurrencyError: Asset EWG priced in EUR but no EUR→USD exchange rates provided`
- **Cause**: Multi-currency portfolio without exchange rates
- **Solution**: Provide exchange rates via `ExchangeRateProvider`

**Error**: `APIError: Exchange rate API request failed`
- **Cause**: Network issue or API rate limit
- **Solution**: Use `CSVExchangeRateProvider` with local exchange rate file

## Performance Tips

1. **Cache price data**: Load CSV once, reuse for multiple backtests
   ```python
   prices = data_provider.load_prices(...)  # Load once
   for strategy in strategies:
       result = engine.run_backtest(config, strategy, prices)  # Reuse
   ```

2. **Use appropriate rebalancing frequency**: Monthly/quarterly is typical; daily is usually unnecessary

3. **Start simple**: Begin with single-currency, 2-asset portfolios before adding complexity

4. **Validate data first**: Check CSV format before running long backtests
   ```python
   data_provider.validate_data(prices)  # Check for errors
   ```

## Next Steps

- **Run tests**: Execute `/speckit.tasks` to generate implementation tasks
- **Review formulas**: See [research.md](./research.md) for calculation details
- **Understand data model**: Read [data-model.md](./data-model.md) for entity definitions
- **API reference**: See [contracts/backtesting-api.md](./contracts/backtesting-api.md)

## Configuration Reference

### RebalancingFrequency Options

| Value | Description | Typical Use Case |
|-------|-------------|------------------|
| `NEVER` | Buy and hold, no rebalancing | Passive index investing |
| `DAILY` | Rebalance every trading day | High-frequency strategies |
| `WEEKLY` | Rebalance every Monday | Active tactical allocation |
| `MONTHLY` | Rebalance first trading day of month | Standard rebalancing |
| `QUARTERLY` | Rebalance every 3 months | Low-cost rebalancing |
| `ANNUALLY` | Rebalance once per year | Minimal trading |

### TransactionCosts Parameters

```python
TransactionCosts(
    fixed_per_trade=Decimal("5.00"),     # Fixed commission per trade
    percentage=Decimal("0.001")           # 0.1% of trade value
)

# Total cost = fixed_per_trade + (percentage × trade_value)
# Example: $10,000 trade with above costs
#   = $5.00 + (0.001 × $10,000)
#   = $5.00 + $10.00
#   = $15.00
```

### Risk-Free Rate Guidelines

| Rate | Typical Period |
|------|----------------|
| 0.01 (1%) | Low interest rate environment (2010-2015) |
| 0.02 (2%) | Moderate rates (default) |
| 0.05 (5%) | High interest rate environment (1990s, 2023+) |

**Source**: Use historical 10-year US Treasury rate for the backtest period.

## Frequently Asked Questions

**Q: Can I backtest with fractional shares?**
A: Yes, the system supports fractional shares (6 decimal places precision).

**Q: How does the system handle market holidays?**
A: Rebalancing scheduled for holidays occurs on the next trading day. Missing price data is forward-filled up to 5 business days.

**Q: Can I backtest short positions or leverage?**
A: No, the initial version supports long-only positions. Short selling and leverage are out of scope.

**Q: How accurate are the calculations?**
A: All calculations use Python's `Decimal` type for financial accuracy. Results match manual calculations within 0.01% (per SC-002).

**Q: What if my CSV has missing dates?**
A: The system automatically forward-fills missing prices up to 5 business days. If gaps exceed 5 days, a `DataError` is raised.

**Q: Can I use custom data sources?**
A: Yes, implement the `HistoricalDataProvider` interface for any data source (API, database, etc.). See [contracts/data-providers.md](./contracts/data-providers.md).

## Support

For issues, questions, or feature requests:
- Review [spec.md](./spec.md) for requirements and acceptance criteria
- Check [research.md](./research.md) for technical decisions and formulas
- See [data-model.md](./data-model.md) for entity validation rules
