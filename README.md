# Asset Allocation Backtesting Engine

A Python library for backtesting asset allocation strategies against historical market data.

## Features

- **Accurate Performance Metrics**: Calculate returns, Sharpe ratio, volatility, and maximum drawdown
- **Flexible Rebalancing**: Support for various rebalancing frequencies (never, daily, weekly, monthly, quarterly, annually)
- **Transaction Costs**: Model realistic trading costs (fixed and percentage-based)
- **Multi-Currency Support**: Handle portfolios with assets in different currencies
- **Missing Data Handling**: Gracefully handle market holidays and missing price data

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install dependencies
uv sync

# Install with development dependencies
uv sync --all-extras
```

## Quick Start

```python
from backtesting import BacktestEngine
from backtesting.models import BacktestConfiguration, AllocationStrategy, RebalancingFrequency
from backtesting.data import CSVDataProvider
from datetime import date
from decimal import Decimal

# Load historical data
data_provider = CSVDataProvider("data/historical_prices.csv")
prices = data_provider.load_prices(
    symbols=["SPY", "AGG"],
    start_date=date(2010, 1, 1),
    end_date=date(2020, 12, 31)
)

# Define strategy
strategy = AllocationStrategy(
    name="60/40 Portfolio",
    asset_weights={"SPY": Decimal("0.6"), "AGG": Decimal("0.4")}
)

# Configure backtest
config = BacktestConfiguration(
    start_date=date(2010, 1, 1),
    end_date=date(2020, 12, 31),
    initial_capital=Decimal("100000"),
    rebalancing_frequency=RebalancingFrequency.QUARTERLY,
    base_currency="USD"
)

# Run backtest
engine = BacktestEngine()
result = engine.run_backtest(config, strategy, prices)

# Display results
print(result.metrics.to_dict())
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_portfolio.py
```

## Project Structure

```
src/
├── backtesting/      # Core backtest engine
├── data/             # Data loading and providers
├── models/           # Data models and entities
└── cli/              # Command-line interface

tests/
├── unit/             # Unit tests
├── integration/      # Integration tests
├── contract/         # Contract/acceptance tests
└── fixtures/         # Test data
```

## Documentation

For detailed usage examples and API documentation, see the `specs/001-backtesting-logic/` directory:

- [spec.md](specs/001-backtesting-logic/spec.md) - Feature specification
- [quickstart.md](specs/001-backtesting-logic/quickstart.md) - Usage guide
- [data-model.md](specs/001-backtesting-logic/data-model.md) - Data structures
- [contracts/](specs/001-backtesting-logic/contracts/) - API contracts

## License

MIT
