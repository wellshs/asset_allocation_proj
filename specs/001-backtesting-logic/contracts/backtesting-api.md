# Contract: Backtesting API

**Feature**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)
**Date**: 2025-11-23
**Status**: COMPLETE

## Purpose

This contract defines the core backtesting engine API - the primary interface for executing backtests, calculating performance metrics, and managing portfolio simulation. This is the public API that users and tests will interact with.

## Core Interface

### BacktestEngine

**Responsibility**: Execute backtests by simulating asset allocation strategies over historical data and producing performance results.

#### Primary Method: run_backtest

```python
from datetime import date
from decimal import Decimal
from dataclasses import dataclass

class BacktestEngine:
    """
    Core backtesting engine for asset allocation strategies.

    This engine simulates a portfolio strategy over historical data,
    handling rebalancing, transaction costs, and multi-currency conversion.
    """

    def run_backtest(
        self,
        config: BacktestConfiguration,
        strategy: AllocationStrategy,
        price_data: pd.DataFrame,
        exchange_rates: pd.DataFrame | None = None
    ) -> BacktestResult:
        """
        Execute a backtest simulation.

        Args:
            config: Backtest parameters (dates, capital, rebalancing, costs)
            strategy: Target allocation weights for assets
            price_data: Historical price data (date, symbol, price, currency)
            exchange_rates: Optional exchange rate data for multi-currency portfolios
                           (date, from_currency, to_currency, rate)

        Returns:
            BacktestResult containing:
                - metrics: Performance statistics (returns, Sharpe, drawdown)
                - trades: List of all trades executed
                - portfolio_history: Time series of portfolio states

        Raises:
            ValueError: If configuration or strategy validation fails
            DataError: If price data is missing, invalid, or insufficient
            CurrencyError: If multi-currency assets lack exchange rate data

        Preconditions:
            - config.start_date and end_date are valid business days
            - strategy.asset_weights sum to 1.0 (±0.0001 tolerance)
            - price_data contains all strategy assets for the date range
            - If assets have different currencies, exchange_rates must be provided

        Postconditions:
            - All trades execute at valid prices from price_data
            - Portfolio value is never negative
            - Final portfolio state reflects all trades and rebalancing
            - Performance metrics match formulas in research.md
        """
```

#### Result Type

```python
@dataclass
class BacktestResult:
    """Results from a completed backtest."""

    metrics: PerformanceMetrics
    trades: list[Trade]
    portfolio_history: list[PortfolioState]

    def __post_init__(self):
        if not self.portfolio_history:
            raise ValueError("portfolio_history cannot be empty")
        if self.metrics.num_trades != len(self.trades):
            raise ValueError("metrics.num_trades must match len(trades)")
```

## Supporting Methods

### Pre-Execution Validation

```python
class BacktestEngine:
    def _validate_inputs(
        self,
        config: BacktestConfiguration,
        strategy: AllocationStrategy,
        price_data: pd.DataFrame
    ) -> None:
        """
        Validate all inputs before starting backtest execution.

        Validation checks (per FR-020, FR-021):
            1. All assets in strategy exist in price_data
            2. All assets have price data at config.start_date
            3. Strategy weights sum to 1.0 (±0.0001 tolerance)
            4. Date range is valid (start < end)

        Raises:
            ValueError: If strategy weights invalid or date range invalid
            DataError: If assets missing from price_data or missing at start_date

        Algorithm:
            1. Extract unique symbols from strategy.asset_weights
            2. Check each symbol exists in price_data
            3. Check each symbol has data at start_date
            4. If any checks fail, raise error with list of missing assets

        Error messages:
            - "Assets not in historical data: {missing_symbols}"
            - "Assets missing data at start date {start_date}: {missing_at_start}"
            - "Strategy weights sum to {actual}, must be 1.0 ±0.0001"
        """
```

### Portfolio Initialization

```python
class BacktestEngine:
    def _initialize_portfolio(
        self,
        config: BacktestConfiguration,
        start_date: date
    ) -> PortfolioState:
        """
        Create initial portfolio state with all cash, no holdings.

        Args:
            config: Backtest configuration (provides initial_capital)
            start_date: Start date for the portfolio

        Returns:
            PortfolioState with cash = initial_capital, empty holdings

        Postconditions:
            - cash_balance == config.initial_capital
            - asset_holdings is empty dict
            - total_value == initial_capital
        """
```

### Rebalancing

```python
class BacktestEngine:
    def _rebalance_portfolio(
        self,
        current_state: PortfolioState,
        target_weights: dict[str, Decimal],
        current_prices: dict[str, Decimal],
        transaction_costs: TransactionCosts
    ) -> tuple[PortfolioState, list[Trade]]:
        """
        Rebalance portfolio to target weights.

        Args:
            current_state: Current portfolio holdings and cash
            target_weights: Desired allocation weights (sum to 1.0)
            current_prices: Current market prices in base currency
            transaction_costs: Cost parameters for trades

        Returns:
            Tuple of:
                - Updated PortfolioState after rebalancing
                - List of Trade objects executed

        Algorithm:
            1. Calculate target dollar amounts: target_value[asset] = total_value × weight
            2. Calculate current dollar amounts: current_value[asset] = holdings × price
            3. Determine trades needed: trade_value = target - current
            4. Calculate total transaction costs for all trades
            5. If transaction costs > available cash:
               - Execute trades with available cash only (partial execution)
               - Log warning: "Insufficient cash for full rebalancing"
            6. Execute trades and apply transaction costs
            7. Update holdings and cash balance

        Edge Cases:
            - Insufficient cash (per clarification): Complete partial rebalancing with available cash + warning
            - Backtest period < rebalancing frequency: Skip rebalancing + warning
            - Delisted asset (no price data): Liquidate at last known price, hold proceeds as cash (per FR-022)

        Postconditions:
            - New portfolio weights match target_weights (within rounding) or best effort if cash constrained
            - Cash balance reduced by transaction costs
            - All trades have non-zero quantities
            - Portfolio total value = previous value - transaction costs
        """
```

### Price Data Handling

```python
class BacktestEngine:
    def _get_prices_for_date(
        self,
        price_data: pd.DataFrame,
        target_date: date,
        symbols: list[str]
    ) -> dict[str, Decimal]:
        """
        Get prices for all symbols on a specific date with forward-fill.

        Args:
            price_data: Historical price DataFrame
            target_date: Date for which to get prices
            symbols: List of asset symbols needed

        Returns:
            Dictionary mapping symbol to price (in base currency)

        Raises:
            DataError: If any symbol has no data within 5 business days before target_date

        Algorithm:
            1. Filter price_data for target_date
            2. If missing data, forward-fill from previous dates (max 5 days)
            3. If still missing after 5 days, raise DataError
            4. Convert to base currency using exchange rates if needed

        Postconditions:
            - Returns exactly one price per symbol in symbols list
            - All prices are > 0
            - Prices are in base currency
        """
```

### Currency Conversion

```python
class BacktestEngine:
    def _convert_to_base_currency(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        conversion_date: date,
        exchange_rates: pd.DataFrame
    ) -> Decimal:
        """
        Convert amount from one currency to base currency.

        Args:
            amount: Amount in from_currency
            from_currency: Source currency code (ISO 4217)
            to_currency: Target currency code (base currency)
            conversion_date: Date for exchange rate lookup
            exchange_rates: Historical exchange rate data

        Returns:
            Amount converted to base currency

        Raises:
            CurrencyError: If exchange rate not available for conversion_date

        Algorithm:
            1. If from_currency == to_currency, return amount unchanged
            2. Lookup rate for (from_currency, to_currency) on conversion_date
            3. Apply conversion: result = amount / rate
               (Note: rate is "1 from = rate × to", so to convert from→to, divide)

        Postconditions:
            - Result is in to_currency
            - Precision: 2 decimal places for currency amounts
        """
```

### Performance Calculation

```python
class BacktestEngine:
    def _calculate_performance(
        self,
        portfolio_history: list[PortfolioState],
        config: BacktestConfiguration,
        num_trades: int
    ) -> PerformanceMetrics:
        """
        Calculate performance metrics from portfolio value time series.

        Args:
            portfolio_history: List of portfolio states over time (chronological)
            config: Backtest configuration (provides start/end dates, risk-free rate)
            num_trades: Total number of trades executed

        Returns:
            PerformanceMetrics with all statistics calculated

        Algorithm (formulas from research.md):
            1. Extract portfolio values into time series
            2. Calculate daily returns: pct_change()
            3. Total return: (final - initial) / initial
            4. Annualized return: (1 + total)^(252/days) - 1
            5. Volatility: std(daily_returns) × sqrt(252)
            6. Max drawdown: min((value - cummax(value)) / cummax(value))
            7. Sharpe ratio: (annual_return - rf_rate) / volatility

        Postconditions:
            - All metrics rounded to specified precision (data-model.md)
            - Returns are in decimal form (0.10 = 10%)
            - Sharpe ratio uses config.risk_free_rate
        """
```

## Error Handling

### Custom Exceptions

```python
class BacktestError(Exception):
    """Base exception for backtesting errors."""
    pass

class DataError(BacktestError):
    """Raised when historical data is missing, invalid, or insufficient."""
    pass

class CurrencyError(BacktestError):
    """Raised when exchange rate data is missing for multi-currency portfolios."""
    pass

class ConfigurationError(BacktestError):
    """Raised when backtest configuration is invalid."""
    pass
```

### Error Scenarios

| Scenario | Exception | Message Example |
|----------|-----------|-----------------|
| Strategy weights don't sum to 1.0 | `ValueError` | "Strategy weights sum to 0.95, must be 1.0 ±0.0001" |
| Missing price data for asset | `DataError` | "No price data for SPY on 2020-03-15 (5-day forward-fill exceeded)" |
| Multi-currency without exchange rates | `CurrencyError` | "Asset AGG priced in EUR but no EUR→USD exchange rates provided" |
| Start date after end date | `ConfigurationError` | "start_date (2020-01-01) must be before end_date (2019-12-31)" |
| Negative price encountered | `DataError` | "Invalid price for SPY on 2020-03-15: -10.50 (prices must be > 0)" |
| **Asset not in historical data (FR-021)** | `DataError` | "Assets not in historical data: ['TSLA', 'BTC']" |
| **Asset missing at start date (FR-020)** | `DataError` | "Assets missing data at start date 2020-01-01: ['SPY']" |

### Warning Scenarios (Logged, Not Raised)

| Scenario | Warning Level | Message Example |
|----------|---------------|-----------------|
| Insufficient cash for full rebalancing | `WARNING` | "Insufficient cash for full rebalancing: required $10,000, available $5,000. Executing partial rebalancing." |
| Backtest period < rebalancing frequency | `WARNING` | "Backtest period (30 days) shorter than rebalancing frequency (quarterly). No rebalancing will occur." |
| Asset delisted during backtest | `INFO` | "Asset LEHM delisted on 2008-09-15. Position liquidated at $0.21, proceeds held as cash." |

## Testing Contract

### Unit Test Requirements

1. **Portfolio initialization**:
   - Initial state has all cash, no holdings
   - Total value equals initial capital

2. **Rebalancing logic**:
   - Weights after rebalancing match targets (within 0.01%)
   - Transaction costs correctly reduce portfolio value
   - Trades have correct signs (buy = +, sell = -)

3. **Price handling**:
   - Forward-fill works up to 5 days
   - Raises error if gap > 5 days
   - Zero/negative prices raise DataError

4. **Currency conversion**:
   - Same currency returns unchanged amount
   - Conversion uses correct exchange rate
   - Missing rates raise CurrencyError

5. **Performance metrics**:
   - Calculations match formulas in research.md
   - Precision matches data-model.md specifications
   - Known scenarios produce expected results (see research.md Tier 3 tests)

### Integration Test Requirements

1. **End-to-end backtest**:
   - Simple 60/40 portfolio produces expected returns
   - Multi-asset rebalancing generates correct trades
   - Portfolio value never goes negative

2. **Multi-currency support**:
   - Mixed USD/EUR portfolio calculates correct base currency values
   - Exchange rate fetching works with external API
   - Fallback to user-provided rates works

3. **Edge cases**:
   - Backtest period shorter than rebalancing frequency
   - All assets same currency (no conversion needed)
   - Very high transaction costs (approaching 100% of trades)

### Contract Test Requirements (Known Scenarios)

From research.md Section 5:

1. **SPY 2010-2020 buy-and-hold**:
   - Expected total return: ~256% (±0.01%)
   - Expected annualized return: ~12.8% (±0.01%)
   - Expected max drawdown: ~34% (±0.01%)

2. **60/40 SPY/AGG 2010-2020**:
   - Expected total return: ~180% (±0.01%)
   - Expected Sharpe ratio: ~1.1 (±0.05)

3. **SPY 2008 crisis**:
   - Expected total return: ~-50% (±0.01%)
   - Expected max drawdown: ~-55% (±0.01%)

## Performance Requirements

From spec.md Success Criteria:

- **SC-001**: Process 10 years × 5 assets within 30 seconds
- **SC-002**: Accuracy within 0.01% of manual calculations
- **SC-004**: 95% success rate for valid inputs
- **SC-007**: Handle datasets with 10% missing data

**Optimization strategy** (per Simplicity principle):
- Start with direct Python loops, no premature optimization
- Use pandas vectorized operations for time series calculations
- Profile before optimizing (measure, don't guess)
- Only optimize if SC-001 fails

## API Versioning

**Version**: 1.0.0 (initial implementation)

**Breaking changes policy**:
- Additions (new optional parameters) are non-breaking
- Changes to return types or method signatures are breaking
- Changes to exception types/messages are non-breaking
- Changes to calculation precision are breaking

**Deprecation policy**: Mark methods deprecated for one minor version before removal.

## Usage Examples

### Basic Single-Currency Backtest

```python
from backtesting import BacktestEngine
from models import BacktestConfiguration, AllocationStrategy, TransactionCosts
from data import CSVDataProvider
from datetime import date
from decimal import Decimal

# Load historical data
data_provider = CSVDataProvider()
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
    transaction_costs=TransactionCosts(
        fixed_per_trade=Decimal("0"),
        percentage=Decimal("0.001")
    ),
    risk_free_rate=Decimal("0.02"),
    base_currency="USD"
)

# Run backtest
engine = BacktestEngine()
result = engine.run_backtest(config, strategy, prices)

# Display results
print(result.metrics.to_dict())
print(f"\nTotal trades: {len(result.trades)}")
```

### Multi-Currency Backtest

```python
# Load historical data (mixed currencies)
prices = data_provider.load_prices(
    symbols=["SPY", "EWG"],  # SPY=USD, EWG=EUR
    start_date=date(2015, 1, 1),
    end_date=date(2020, 12, 31)
)

# Fetch exchange rates
from data import ExchangeRateHostProvider

rate_provider = ExchangeRateHostProvider()
exchange_rates = rate_provider.fetch_rates(
    base_currency="USD",
    target_currencies=["EUR"],
    start_date=date(2015, 1, 1),
    end_date=date(2020, 12, 31)
)

# Run backtest with exchange rates
result = engine.run_backtest(config, strategy, prices, exchange_rates)
```

## Next Steps

**Phase 1 Progress**: Backtesting API contract complete ✓

Proceed to:
1. Create contracts/data-providers.md
2. Create quickstart.md

## References

- [spec.md](../spec.md) - Functional requirements
- [data-model.md](../data-model.md) - Entity definitions
- [research.md](../research.md) - Technical decisions and formulas
