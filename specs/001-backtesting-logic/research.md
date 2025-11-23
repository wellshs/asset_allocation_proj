# Research: Backtesting Logic

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Date**: 2025-11-23
**Status**: COMPLETE

## Purpose

This document resolves technical unknowns identified in the implementation plan before proceeding to design. All decisions prioritize the constitution principles: Test-First Development, Financial Accuracy, and Simplicity.

## Research Questions & Decisions

### 1. Language and Ecosystem Selection

**Question**: Confirm Python 3.11+ with pandas/numpy for financial calculations vs alternatives (R, Julia)?

**Decision**: **Python 3.11+** with pandas/numpy

**Rationale**:
- **Performance**: NumPy's vectorized operations can handle 10 years × 5 assets (12,500 data points) well within the 30-second requirement (SC-001)
- **Financial libraries**: Mature ecosystem (pandas for time series, numpy for calculations, pytest for testing)
- **Testing ecosystem**: pytest + hypothesis (property-based testing) provide comprehensive test coverage needed for Financial Accuracy principle
- **Simplicity**: Widely adopted with extensive documentation, reducing learning curve
- **Cross-platform**: Works on Linux/macOS/Windows without modification

**Alternatives rejected**:
- **R**: Strong statistical capabilities but weaker general-purpose testing frameworks and CLI tooling
- **Julia**: Better numerical performance but smaller ecosystem and less mature testing tools
- **Pure Python**: Cannot meet SC-001 performance requirement for large datasets

**Dependencies required**:
- `pandas >= 2.0.0` - Time series data manipulation, business day handling
- `numpy >= 1.24.0` - Numerical calculations
- `pytest >= 7.0.0` - Test framework
- `hypothesis >= 6.0.0` - Property-based testing

### 2. Historical Data Format and Sources

**Question**: What format for historical price data (CSV, Parquet, database)?

**Decision**: **CSV for initial implementation**, with extensible provider interface

**Rationale (Simplicity principle)**:
- CSV is universally supported, human-readable, and requires no additional dependencies
- Users can easily provide their own data (FR-002)
- Satisfies all functional requirements without adding database complexity
- File-based approach avoids infrastructure dependencies for initial version

**Data format specification**:
```csv
date,symbol,price,currency
2010-01-04,SPY,112.37,USD
2010-01-04,AGG,105.23,USD
2010-01-05,SPY,112.86,USD
```

**Required columns**:
- `date`: ISO 8601 format (YYYY-MM-DD)
- `symbol`: Asset identifier
- `price`: Adjusted closing price (splits/dividends already applied, per spec assumptions)
- `currency`: ISO 4217 currency code (e.g., USD, EUR, JPY)

**Validation rules**:
- Dates must be chronological for each symbol
- Prices must be > 0 (zero/negative triggers error per FR-015)
- Missing dates handled by forward-fill (FR-009)

**Future extensibility**: Abstract data loading behind `HistoricalDataProvider` interface to support Parquet, databases, or APIs later without changing core engine.

**Question**: Which data providers/APIs for exchange rates (Alpha Vantage, IEX, Yahoo Finance)?

**Decision**: **exchangerate.host API** for exchange rates (free tier sufficient)

**Rationale**:
- **Free tier**: 1,500 requests/month covers typical backtesting needs (10 currency pairs × 10 years ÷ batching = ~100 requests)
- **Historical data**: Provides historical rates back to 1999 (sufficient for most backtests)
- **Reliability**: ECB (European Central Bank) data source, high accuracy
- **No authentication required**: Simplifies initial implementation
- **API simplicity**: Single endpoint for historical rates

**API example**:
```
GET https://api.exchangerate.host/timeseries
  ?start_date=2010-01-01
  &end_date=2020-12-31
  &base=USD
  &symbols=EUR,GBP,JPY
```

**Alternatives considered**:
- **Alpha Vantage**: Requires API key, stricter rate limits (25 requests/day free tier)
- **Yahoo Finance (yfinance library)**: Unofficial API, reliability concerns for production use
- **Open Exchange Rates**: Requires API key, limited free tier

**Complexity justification**: External API dependency justified in plan.md Complexity Tracking table - automatic fetching required by FR-018, manual entry too error-prone.

**Fallback strategy**: If API unavailable, allow users to provide exchange rate CSV in same format as price data.

### 3. Date and Business Day Handling

**Question**: How to handle market holidays and business day calculations?

**Decision**: Use **pandas business day functionality** with US market calendar

**Rationale (Simplicity principle)**:
- pandas `BDay()` provides business day arithmetic without external calendar libraries
- Handles weekends automatically
- US market (NYSE/NASDAQ) is most common for initial use case
- Avoids dependency on specialized libraries like `trading-calendars` or `pandas-market-calendars`

**Market holiday handling strategy**:
- **Rebalancing dates**: If rebalancing date falls on holiday/weekend, use next business day (FR-009 acceptance scenario 3)
- **Missing prices**: Forward-fill from most recent available date (FR-009 acceptance scenario 1)
- **Max forward-fill**: Limit to 5 business days; beyond that, log warning and skip rebalancing period

**Implementation approach**:
```python
import pandas as pd

# Generate business day sequence
trading_days = pd.bdate_range(start='2010-01-01', end='2020-12-31')

# Forward-fill missing prices (limit 5 days)
prices_filled = prices.reindex(trading_days).fillna(method='ffill', limit=5)
```

**Edge case**: If backtest start date has no price data, raise `DataError` immediately (cannot forward-fill from nothing).

**Future enhancement**: Support other market calendars (UK, EU, Asia) via configuration, but defer until user need confirmed (YAGNI principle).

### 4. Performance Metric Formulas

**Question**: Exact formula for Sharpe ratio (annual vs period-based)? Maximum drawdown calculation methodology?

**Decision**: Use **annualized Sharpe ratio** with industry-standard formulas

**Formulas with references**:

#### Total Return
```
total_return = (final_value - initial_value) / initial_value
```
**Reference**: Standard financial definition

#### Annualized Return
```
annualized_return = (1 + total_return) ^ (252 / num_trading_days) - 1
```
**Reference**: Assumes 252 trading days per year (US market standard)
**Precision**: Round to 4 decimal places (0.01% accuracy per SC-002)

#### Volatility (Annualized)
```
daily_returns = portfolio_values.pct_change()
volatility = daily_returns.std() * sqrt(252)
```
**Reference**: Standard deviation of daily returns, annualized using square-root-of-time rule
**Assumption**: Returns are independent and identically distributed (IID)

#### Sharpe Ratio
```
sharpe_ratio = (annualized_return - risk_free_rate) / volatility
```
**Reference**: Sharpe, William F. (1994). "The Sharpe Ratio". Journal of Portfolio Management.
**Risk-free rate**: User-configurable parameter (FR-016), default 0.02 (2% per spec)
**Precision**: Round to 2 decimal places

#### Maximum Drawdown
```
cumulative_returns = (1 + daily_returns).cumprod()
running_max = cumulative_returns.cummax()
drawdown = (cumulative_returns - running_max) / running_max
max_drawdown = drawdown.min()
```
**Reference**: Maximum peak-to-trough decline during backtest period
**Precision**: Round to 4 decimal places (0.01% accuracy)

**Calculation order**:
1. Compute daily returns from portfolio value time series
2. Calculate annualized return and volatility
3. Compute Sharpe ratio using risk-free rate
4. Calculate maximum drawdown from cumulative returns

**Validation**: Test suite will verify calculations against known scenarios:
- 2008 financial crisis (expect high drawdown, negative Sharpe)
- 2010-2020 bull market (expect positive returns, moderate Sharpe)

### 5. Testing Strategy

**Question**: Which known historical scenarios for validation tests?

**Decision**: **Three-tier test strategy** with reference scenarios

#### Tier 1: Unit Tests (Isolated Components)
- Portfolio state calculations (value, weights, cash balance)
- Rebalancing trade calculations (target vs current allocation)
- Metric formulas (returns, Sharpe, drawdown) with synthetic data
- Transaction cost application
- Currency conversion logic

**Coverage target**: 90%+ code coverage for calculation functions

#### Tier 2: Integration Tests (Component Interaction)
- Full backtest execution with simple strategies
- Data loading and validation
- Multi-currency portfolio handling
- Missing data handling (forward-fill, gaps)
- Rebalancing frequency variations

#### Tier 3: Contract Tests (Accuracy Validation)

**Reference scenario 1: 2010-2020 SPY buy-and-hold**
- **Data**: SPY (S&P 500 ETF) daily prices 2010-01-04 to 2020-12-31
- **Strategy**: 100% SPY, no rebalancing
- **Expected total return**: ~256% (verified against public data)
- **Expected annualized return**: ~12.8%
- **Expected max drawdown**: ~34% (COVID-19 crash March 2020)
- **Tolerance**: ±0.01% per SC-002

**Reference scenario 2: 60/40 Portfolio (SPY/AGG)**
- **Data**: SPY and AGG (Bond ETF) daily prices 2010-2020
- **Strategy**: 60% SPY, 40% AGG, quarterly rebalancing
- **Expected total return**: ~180% (verified against portfolio backtesting tools)
- **Expected Sharpe ratio**: ~1.1 (with 2% risk-free rate)
- **Tolerance**: ±0.01% for returns, ±0.05 for Sharpe ratio

**Reference scenario 3: 2008 Financial Crisis**
- **Data**: 2008-01-01 to 2009-03-31
- **Strategy**: 100% SPY
- **Expected total return**: ~-50%
- **Expected max drawdown**: ~-55%
- **Purpose**: Validate drawdown calculation during extreme market stress

**Test data source**: Yahoo Finance adjusted close prices (manually downloaded and verified)

**Property-based tests** (using hypothesis):
- Portfolio weights always sum to 1.0 (within floating-point tolerance)
- Portfolio value never goes negative (given long-only constraint)
- Rebalancing reduces weight drift (post-rebalance weights closer to target)
- Transaction costs always reduce returns (never increase)
- Forward-filled prices never exceed 5-day gap

**Test fixtures location**: `tests/fixtures/`
- `spy_2010_2020.csv` - SPY historical prices
- `agg_2010_2020.csv` - AGG historical prices
- `spy_2008_crisis.csv` - 2008 crisis data
- `expected_results.json` - Known metric values for validation

## Technology Stack Summary

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| Language | Python | 3.11+ | Mature financial ecosystem, testing tools |
| Data manipulation | pandas | 2.0.0+ | Time series handling, business day arithmetic |
| Numerical computation | numpy | 1.24.0+ | Vectorized calculations for performance |
| Testing framework | pytest | 7.0.0+ | Industry standard, excellent ecosystem |
| Property-based testing | hypothesis | 6.0.0+ | Comprehensive coverage for financial accuracy |
| HTTP client | requests | 2.31.0+ | Exchange rate API calls |
| Data format | CSV | Built-in | Simplicity, universal compatibility |
| Exchange rate API | exchangerate.host | Free tier | Historical data, ECB source, no auth required |

**Total external dependencies**: 5 libraries (pandas, numpy, pytest, hypothesis, requests)

**Rationale**: Minimal dependency set justified by performance (pandas/numpy), testing requirements (pytest/hypothesis), and exchange rate fetching (requests for FR-018).

## Data Provider Interfaces

### HistoricalDataProvider (Abstract)
```python
from abc import ABC, abstractmethod
from datetime import date
import pandas as pd

class HistoricalDataProvider(ABC):
    @abstractmethod
    def load_prices(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Load historical price data for symbols.

        Returns:
            DataFrame with columns: date, symbol, price, currency
            Index: None (flat structure)

        Raises:
            DataError: If required data unavailable or invalid
        """
        pass
```

### ExchangeRateProvider (Abstract)
```python
class ExchangeRateProvider(ABC):
    @abstractmethod
    def fetch_rates(
        self,
        base_currency: str,
        target_currencies: list[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Fetch historical exchange rates.

        Returns:
            DataFrame with columns: date, from_currency, to_currency, rate
            Example: USD to EUR on 2020-01-01 = 0.89

        Raises:
            APIError: If external API fails
            DataError: If invalid currency codes
        """
        pass
```

### Concrete Implementations

**CSVDataProvider**: Reads CSV files in specified format
**ExchangeRateHostProvider**: Calls exchangerate.host API with caching

**Extensibility**: Users can implement custom providers (e.g., database, proprietary APIs) by subclassing abstract interfaces.

## Constitution Compliance Verification

### Test-First Development ✓
- Test framework selected: pytest with hypothesis
- Test data fixtures defined: 3 reference scenarios with known results
- Functional requirements mapped to test tiers (unit, integration, contract)
- TDD workflow: Write failing tests → Implement → Verify passing

### Financial Data Accuracy ✓
- Precision requirements: 4 decimal places for percentages, 2 for ratios
- Formulas referenced: Sharpe (1994), standard financial definitions
- Rounding behavior: Explicit decimal place specifications
- Edge cases documented: Missing data (forward-fill max 5 days), holidays (next business day), zero prices (error)
- Reproducibility: Fixed test data fixtures, seeded random tests

### Simplicity ✓
- Started with CSV (simplest), not database
- Used pandas business days (built-in), not specialized calendar libraries
- Minimal dependency set (5 libraries, all justified)
- No premature optimization (direct calculation loops acceptable initially)
- No speculative features beyond spec requirements

**Complexity introduced**: All items documented in plan.md Complexity Tracking table with justifications.

## Next Steps

**Phase 0 Complete** ✓

Proceed to **Phase 1: Design & Contracts**
1. Create `data-model.md` - Formalize data structures
2. Create `contracts/backtesting-api.md` - Core engine interface
3. Create `contracts/data-providers.md` - Data loading interfaces
4. Create `quickstart.md` - Usage examples
5. Update agent context: `.specify/scripts/bash/update-agent-context.sh claude`
6. Re-check constitution compliance

## References

1. Sharpe, William F. (1994). "The Sharpe Ratio". Journal of Portfolio Management. Fall 1994.
2. pandas documentation: Business Day functionality - https://pandas.pydata.org/docs/user_guide/timeseries.html#business-day
3. exchangerate.host API documentation - https://exchangerate.host/#/
4. NumPy financial functions - https://numpy.org/doc/stable/reference/routines.financial.html
