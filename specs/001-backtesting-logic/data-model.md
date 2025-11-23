# Data Model: Backtesting Logic

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Date**: 2025-11-23
**Status**: COMPLETE

## Purpose

This document defines the data structures and entities used in the backtesting system. All entities include validation rules, calculation methods, and precision requirements to ensure Financial Accuracy.

## Core Entities

### BacktestConfiguration

**Purpose**: Parameters for configuring and executing a backtest simulation

**Fields**:

| Field | Type | Required | Validation | Default |
|-------|------|----------|------------|---------|
| `start_date` | `datetime.date` | Yes | Must be before `end_date` | - |
| `end_date` | `datetime.date` | Yes | Must be after `start_date` | - |
| `initial_capital` | `Decimal` | Yes | Must be > 0 | - |
| `rebalancing_frequency` | `RebalancingFrequency` | Yes | Enum value | - |
| `transaction_costs` | `TransactionCosts` | No | If provided, values ≥ 0 | Zero costs |
| `risk_free_rate` | `Decimal` | No | Must be ≥ 0, typically 0.0-0.10 | 0.02 |
| `base_currency` | `str` | Yes | ISO 4217 code (3 letters) | - |

**Related entities**: `AllocationStrategy`, `TransactionCosts`, `RebalancingFrequency`

**Validation rules**:
- Date range must span at least 1 trading day
- Initial capital precision: 2 decimal places (cents)
- Risk-free rate precision: 4 decimal places (0.0200 = 2.00%)

**Python type example**:
```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

class RebalancingFrequency(Enum):
    NEVER = "never"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"

@dataclass
class TransactionCosts:
    fixed_per_trade: Decimal  # Fixed cost per trade (e.g., $0)
    percentage: Decimal       # Percentage of trade value (e.g., 0.001 = 0.1%)

@dataclass
class BacktestConfiguration:
    start_date: date
    end_date: date
    initial_capital: Decimal
    rebalancing_frequency: RebalancingFrequency
    base_currency: str
    transaction_costs: TransactionCosts = TransactionCosts(Decimal(0), Decimal(0))
    risk_free_rate: Decimal = Decimal("0.02")

    def __post_init__(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")
        if self.risk_free_rate < 0:
            raise ValueError("risk_free_rate cannot be negative")
        if len(self.base_currency) != 3:
            raise ValueError("base_currency must be ISO 4217 code (3 letters)")
```

---

### AllocationStrategy

**Purpose**: Defines target portfolio weights for asset allocation

**Fields**:

| Field | Type | Required | Validation | Default |
|-------|------|----------|------------|---------|
| `name` | `str` | Yes | Non-empty string | - |
| `asset_weights` | `dict[str, Decimal]` | Yes | Weights sum to 1.0, all ≥ 0 | - |
| `rebalance_threshold` | `Decimal` | No | If provided: 0 < threshold ≤ 1.0 | None |

**Validation rules**:
- Sum of all weights must equal 1.0 (within ±0.0001 tolerance for floating-point)
- All weights must be ≥ 0 (no short positions in initial version)
- Weight precision: 4 decimal places (0.6000 = 60.00%)
- At least one asset must have weight > 0

**Python type example**:
```python
@dataclass
class AllocationStrategy:
    name: str
    asset_weights: dict[str, Decimal]
    rebalance_threshold: Decimal | None = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.asset_weights:
            raise ValueError("asset_weights cannot be empty")

        total_weight = sum(self.asset_weights.values())
        if not (Decimal("0.9999") <= total_weight <= Decimal("1.0001")):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        if any(w < 0 for w in self.asset_weights.values()):
            raise ValueError("All weights must be non-negative")

        if self.rebalance_threshold is not None:
            if not (0 < self.rebalance_threshold <= 1):
                raise ValueError("rebalance_threshold must be between 0 and 1")
```

**Usage notes**:
- `rebalance_threshold` is optional for future enhancement (threshold-based rebalancing)
- Initial version uses time-based rebalancing only (per `RebalancingFrequency`)

---

### PortfolioState

**Purpose**: Snapshot of portfolio holdings and value at a specific point in time

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | `datetime.date` | Yes | Date of this portfolio state |
| `cash_balance` | `Decimal` | Yes | Cash holdings in base currency |
| `asset_holdings` | `dict[str, Decimal]` | Yes | Quantity of each asset held |
| `current_prices` | `dict[str, Decimal]` | Yes | Current price of each asset in base currency |
| `total_value` | `Decimal` | Yes (computed) | Total portfolio value in base currency |

**Computed fields**:
- `total_value = cash_balance + sum(holdings[asset] × prices[asset] for each asset)`

**Precision**:
- Cash balance: 2 decimal places
- Asset holdings: 6 decimal places (fractional shares supported)
- Prices: 4 decimal places
- Total value: 2 decimal places

**Python type example**:
```python
@dataclass
class PortfolioState:
    timestamp: date
    cash_balance: Decimal
    asset_holdings: dict[str, Decimal]
    current_prices: dict[str, Decimal]

    @property
    def total_value(self) -> Decimal:
        """Compute total portfolio value in base currency."""
        holdings_value = sum(
            qty * self.current_prices.get(symbol, Decimal(0))
            for symbol, qty in self.asset_holdings.items()
        )
        return self.cash_balance + holdings_value

    def get_current_weights(self) -> dict[str, Decimal]:
        """Calculate current portfolio weights."""
        total = self.total_value
        if total == 0:
            return {}
        return {
            symbol: (qty * self.current_prices[symbol]) / total
            for symbol, qty in self.asset_holdings.items()
        }
```

**Invariants**:
- Total value must always be ≥ 0 (cannot have negative portfolio value)
- Asset holdings can be 0 (asset sold completely) but not negative (no shorts)
- Cash balance can temporarily be negative during rebalancing calculations but must be ≥ 0 after rebalancing completes

---

### Trade

**Purpose**: Record of a buy or sell transaction executed during backtesting

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | `datetime.date` | Yes | Date trade was executed |
| `asset_symbol` | `str` | Yes | Symbol of asset traded |
| `quantity` | `Decimal` | Yes | Quantity traded (+ for buy, - for sell) |
| `price` | `Decimal` | Yes | Execution price per unit in asset currency |
| `currency` | `str` | Yes | Currency of the price (ISO 4217) |
| `transaction_cost` | `Decimal` | Yes | Total cost incurred for this trade |
| `trade_value` | `Decimal` | Yes (computed) | Absolute value of trade in asset currency |

**Computed fields**:
- `trade_value = abs(quantity × price)`

**Validation rules**:
- Quantity cannot be 0 (no zero-quantity trades)
- Price must be > 0
- Transaction cost must be ≥ 0

**Precision**:
- Quantity: 6 decimal places
- Price: 4 decimal places
- Transaction cost: 2 decimal places
- Trade value: 2 decimal places

**Python type example**:
```python
@dataclass
class Trade:
    timestamp: date
    asset_symbol: str
    quantity: Decimal
    price: Decimal
    currency: str
    transaction_cost: Decimal

    def __post_init__(self):
        if self.quantity == 0:
            raise ValueError("quantity cannot be zero")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.transaction_cost < 0:
            raise ValueError("transaction_cost cannot be negative")
        if len(self.currency) != 3:
            raise ValueError("currency must be ISO 4217 code")

    @property
    def trade_value(self) -> Decimal:
        """Absolute value of trade in asset currency."""
        return abs(self.quantity * self.price)

    @property
    def is_buy(self) -> bool:
        return self.quantity > 0

    @property
    def is_sell(self) -> bool:
        return self.quantity < 0
```

---

### PerformanceMetrics

**Purpose**: Calculated performance statistics for a completed backtest

**Fields**:

| Field | Type | Required | Description | Formula Reference |
|-------|------|----------|-------------|-------------------|
| `total_return` | `Decimal` | Yes | Total return over backtest period | (final - initial) / initial |
| `annualized_return` | `Decimal` | Yes | Return annualized to yearly basis | (1 + total)^(252/days) - 1 |
| `volatility` | `Decimal` | Yes | Annualized standard deviation | std(daily_returns) × sqrt(252) |
| `max_drawdown` | `Decimal` | Yes | Maximum peak-to-trough decline | min((value - peak) / peak) |
| `sharpe_ratio` | `Decimal` | Yes | Risk-adjusted return metric | (annual_return - rf_rate) / volatility |
| `num_trades` | `int` | Yes | Total number of trades executed | Count of Trade objects |
| `start_date` | `datetime.date` | Yes | Backtest start date | From configuration |
| `end_date` | `datetime.date` | Yes | Backtest end date | From configuration |
| `start_value` | `Decimal` | Yes | Initial portfolio value | Initial capital |
| `end_value` | `Decimal` | Yes | Final portfolio value | Portfolio value at end |

**Precision requirements** (per research.md):
- Returns: 4 decimal places (0.1256 = 12.56%)
- Volatility: 4 decimal places
- Sharpe ratio: 2 decimal places
- Drawdown: 4 decimal places
- Currency values: 2 decimal places

**Python type example**:
```python
@dataclass
class PerformanceMetrics:
    total_return: Decimal
    annualized_return: Decimal
    volatility: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    num_trades: int
    start_date: date
    end_date: date
    start_value: Decimal
    end_value: Decimal

    def to_dict(self) -> dict:
        """Format metrics for display."""
        return {
            "Total Return": f"{self.total_return:.2%}",
            "Annualized Return": f"{self.annualized_return:.2%}",
            "Volatility": f"{self.volatility:.2%}",
            "Maximum Drawdown": f"{self.max_drawdown:.2%}",
            "Sharpe Ratio": f"{self.sharpe_ratio:.2f}",
            "Number of Trades": self.num_trades,
            "Period": f"{self.start_date} to {self.end_date}",
            "Start Value": f"${self.start_value:,.2f}",
            "End Value": f"${self.end_value:,.2f}",
        }
```

**Calculation formulas**: See research.md Section 4 for detailed formulas with references.

---

### HistoricalPriceData

**Purpose**: Time-series price data for backtesting assets

**Structure**: Represented as pandas DataFrame with the following schema:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `date` | `datetime64[ns]` | Yes | Trading date (business days) |
| `symbol` | `str` | Yes | Asset identifier |
| `price` | `float64` | Yes | Adjusted closing price |
| `currency` | `str` | Yes | Price currency (ISO 4217) |

**Index**: None (flat table structure)

**Validation rules**:
- Dates must be in chronological order for each symbol
- Prices must be > 0 (per FR-015)
- No duplicate (date, symbol) combinations
- All symbols must have data for the same date range (or gaps handled by forward-fill)

**Data format** (CSV representation):
```csv
date,symbol,price,currency
2010-01-04,SPY,112.37,USD
2010-01-04,AGG,105.23,USD
2010-01-05,SPY,112.86,USD
2010-01-05,AGG,105.45,USD
```

**Pandas DataFrame example**:
```python
import pandas as pd

def validate_price_data(df: pd.DataFrame) -> None:
    """Validate historical price data structure and contents."""
    required_columns = {'date', 'symbol', 'price', 'currency'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Missing columns: {required_columns - set(df.columns)}")

    # Check for zero or negative prices
    if (df['price'] <= 0).any():
        invalid = df[df['price'] <= 0]
        raise ValueError(f"Invalid prices found:\n{invalid}")

    # Check for duplicates
    duplicates = df.duplicated(subset=['date', 'symbol'], keep=False)
    if duplicates.any():
        raise ValueError(f"Duplicate entries found:\n{df[duplicates]}")

    # Verify chronological order within each symbol
    for symbol in df['symbol'].unique():
        symbol_data = df[df['symbol'] == symbol].sort_values('date')
        if not symbol_data['date'].is_monotonic_increasing:
            raise ValueError(f"Dates not chronological for {symbol}")
```

---

### ExchangeRateData

**Purpose**: Historical exchange rate data for multi-currency portfolio conversion

**Structure**: Similar to HistoricalPriceData but with from/to currency pairs

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `date` | `datetime64[ns]` | Yes | Trading date |
| `from_currency` | `str` | Yes | Base currency (ISO 4217) |
| `to_currency` | `str` | Yes | Target currency (ISO 4217) |
| `rate` | `float64` | Yes | Exchange rate (1 from = rate × to) |

**Example**:
```csv
date,from_currency,to_currency,rate
2010-01-04,USD,EUR,0.6913
2010-01-04,USD,GBP,0.6192
2010-01-05,USD,EUR,0.6951
```

**Usage**: When asset priced in EUR needs conversion to USD base currency:
```python
usd_value = eur_price * (1 / eur_to_usd_rate)
# If rate is USD→EUR=0.69, then EUR→USD=1/0.69=1.45
```

---

## Data Flow

### Backtest Execution Flow

```
1. Load Configuration (BacktestConfiguration + AllocationStrategy)
   ↓
2. Load Historical Data (HistoricalPriceData + ExchangeRateData if multi-currency)
   ↓
3. Initialize Portfolio (PortfolioState with initial_capital in cash)
   ↓
4. FOR each rebalancing date:
   a. Get current prices
   b. Calculate current portfolio value and weights
   c. Determine required trades to reach target weights
   d. Execute trades → generate Trade records
   e. Apply transaction costs
   f. Update PortfolioState
   ↓
5. Calculate Performance Metrics from portfolio value time series
   ↓
6. Return (PerformanceMetrics, list[Trade], list[PortfolioState])
```

### Currency Conversion Flow (Multi-Currency)

```
1. Identify unique currencies in portfolio assets
   ↓
2. Fetch exchange rates: asset_currency → base_currency for date range
   ↓
3. FOR each asset price:
   a. If asset.currency == base_currency: use price as-is
   b. Else: convert using rate for that date
      converted_price = asset_price / exchange_rate[asset.currency][base_currency]
   ↓
4. All calculations use converted prices in base currency
```

## Precision and Rounding

**Decimal usage**: All financial calculations use Python `Decimal` type to avoid floating-point errors.

**Rounding modes**:
- Currency amounts (cash, portfolio value): Round HALF_UP to 2 decimal places
- Percentages (returns, weights): Round HALF_UP to 4 decimal places (0.0001 = 0.01%)
- Ratios (Sharpe): Round HALF_UP to 2 decimal places
- Quantities (shares): Round HALF_UP to 6 decimal places (supports fractional shares)

**Example**:
```python
from decimal import Decimal, ROUND_HALF_UP

def round_currency(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def round_percentage(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
```

**Tolerance for comparisons**:
- Weight sum validation: ±0.0001 (0.01%)
- Performance metric matching (tests): ±0.0001 for returns, ±0.05 for Sharpe

## Entity Relationships

```
BacktestConfiguration
├── references: AllocationStrategy
├── configures: BacktestEngine
└── produces: PerformanceMetrics

AllocationStrategy
├── defines target for: PortfolioState
└── drives: Trade generation

PortfolioState
├── updated by: Trade execution
├── tracked in: list[PortfolioState] (time series)
└── uses: HistoricalPriceData, ExchangeRateData

Trade
├── modifies: PortfolioState
└── counted in: PerformanceMetrics.num_trades

PerformanceMetrics
├── calculated from: list[PortfolioState]
└── returned by: BacktestEngine.run_backtest()

HistoricalPriceData
├── loaded by: HistoricalDataProvider
└── converted using: ExchangeRateData

ExchangeRateData
├── fetched by: ExchangeRateProvider
└── converts: HistoricalPriceData to base currency
```

## Validation Summary

All entities implement validation in `__post_init__` to enforce:
- Type correctness
- Value range constraints (positive amounts, valid dates)
- Business rules (weights sum to 1.0, no negative holdings)
- Data integrity (no duplicates, chronological dates)

**Error handling**: Validation errors raise `ValueError` with descriptive messages indicating which constraint was violated.

## Next Steps

**Phase 1 Progress**: Data model complete ✓

Proceed to:
1. Create contracts/backtesting-api.md
2. Create contracts/data-providers.md
3. Create quickstart.md

## References

- Python Decimal documentation: https://docs.python.org/3/library/decimal.html
- pandas DataFrame schema best practices
- ISO 4217 Currency Codes: https://www.iso.org/iso-4217-currency-codes.html
