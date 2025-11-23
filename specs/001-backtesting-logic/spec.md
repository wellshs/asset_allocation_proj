# Feature Specification: Backtesting Logic

**Feature Branch**: `001-backtesting-logic`
**Created**: 2025-11-23
**Status**: Draft
**Input**: User description: "I want to implement backtesting logic."

## Clarifications

### Session 2025-11-23

- Q: What happens when the backtest period is shorter than the rebalancing frequency (e.g., 1-month backtest with quarterly rebalancing)? → A: Complete the backtest without rebalancing and log a warning to the user
- Q: What happens when transaction costs exceed available cash in the portfolio? → A: Complete rebalancing with available cash only and log a warning about partial execution
- Q: What happens when a required asset has no price data at the backtest start date? → A: Abort backtest with clear error indicating which asset is missing data at start date
- Q: What happens when a strategy specifies an allocation to an asset that doesn't exist in the historical data? → A: Validate all strategy assets exist in data before starting and abort with error if missing
- Q: When an asset is delisted during the backtest period, how should the proceeds from liquidation be reallocated? → A: Hold delisted asset proceeds as cash (no reallocation to other assets)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Basic Backtest on Historical Data (Priority: P1)

A portfolio manager wants to validate an asset allocation strategy by running it against historical market data to see how it would have performed in the past.

**Why this priority**: This is the core functionality of backtesting - the ability to simulate a strategy against historical data. Without this, there's no backtesting capability at all. This provides immediate value by allowing users to validate strategies before deploying real capital.

**Independent Test**: Can be fully tested by loading a sample asset allocation strategy, providing historical price data, and verifying that the backtest produces performance metrics (returns, drawdowns, etc.) that match manual calculations.

**Acceptance Scenarios**:

1. **Given** a user has defined an asset allocation strategy and has access to historical price data, **When** they initiate a backtest for a specific time period, **Then** the system executes the strategy rules across the historical period and generates performance results
2. **Given** a backtest is running, **When** the backtest completes, **Then** the system displays key performance metrics including total return, annualized return, maximum drawdown, and Sharpe ratio
3. **Given** historical data with known price movements, **When** a simple buy-and-hold strategy is backtested, **Then** the calculated returns match the expected percentage change from start to end

---

### User Story 2 - Simulate Periodic Rebalancing (Priority: P2)

A user wants to test how their asset allocation strategy performs when portfolios are rebalanced at regular intervals (monthly, quarterly, annually) to maintain target weightings.

**Why this priority**: Rebalancing is a fundamental aspect of asset allocation strategies. While basic backtesting (P1) can show performance, realistic strategies require periodic rebalancing to maintain target allocations. This significantly improves the accuracy and realism of backtest results.

**Independent Test**: Can be tested independently by configuring a rebalancing frequency (e.g., monthly), running a backtest, and verifying that the system adjusts portfolio weightings back to target allocations at the expected intervals.

**Acceptance Scenarios**:

1. **Given** a user has configured a rebalancing frequency (daily, weekly, monthly, quarterly, annually), **When** a backtest runs, **Then** the portfolio is automatically rebalanced to target weights at each rebalancing date
2. **Given** a portfolio has drifted from target allocations due to market movements, **When** a rebalancing date occurs, **Then** the system calculates required trades to restore target weights and applies transaction costs
3. **Given** a user wants to compare strategies, **When** they run backtests with different rebalancing frequencies, **Then** they can observe the performance impact of rebalancing frequency

---

### User Story 3 - Apply Transaction Costs and Slippage (Priority: P3)

A user wants to incorporate realistic trading costs (commissions, bid-ask spreads, slippage) to understand the actual net performance of their strategy after expenses.

**Why this priority**: While important for accurate performance estimation, transaction costs are secondary to getting basic backtesting working. Users can get initial insights without cost modeling, then refine their analysis by adding this layer.

**Independent Test**: Can be tested by running the same backtest with and without transaction costs enabled, then verifying that the version with costs shows lower net returns by the expected amount based on number of trades and cost parameters.

**Acceptance Scenarios**:

1. **Given** a user has defined transaction cost parameters (commission per trade, bid-ask spread percentage), **When** a backtest executes trades, **Then** each trade incurs the specified costs which reduce portfolio value
2. **Given** a high-frequency rebalancing strategy that generates many trades, **When** transaction costs are applied, **Then** the net returns are significantly lower than gross returns, reflecting the cost of trading
3. **Given** a user wants to model market impact, **When** they configure slippage parameters, **Then** larger trades incur proportionally higher execution costs

---

### User Story 4 - Handle Missing Data and Market Holidays (Priority: P3)

A user wants the backtest to handle real-world data issues like missing prices, delisted assets, and market closures without failing or producing incorrect results.

**Why this priority**: Data quality issues are important for robustness but don't prevent initial backtesting functionality. Users can start with clean, complete datasets and add data handling sophistication later.

**Independent Test**: Can be tested by providing historical data with intentional gaps (missing dates, missing symbols) and verifying that the backtest either fills gaps appropriately or skips those periods with clear logging.

**Acceptance Scenarios**:

1. **Given** historical data contains missing prices for certain dates, **When** a backtest runs, **Then** the system uses the most recent available price (forward-fill) or skips that rebalancing period with a warning
2. **Given** an asset was delisted during the backtest period, **When** the backtest reaches the delisting date, **Then** the position is liquidated at the final available price and proceeds are held as cash (not reallocated to other assets)
3. **Given** the backtest period includes market holidays, **When** a rebalancing date falls on a holiday, **Then** the rebalancing occurs on the next trading day

---

### Edge Cases

- **Backtest period shorter than rebalancing frequency**: When the backtest period is shorter than the configured rebalancing frequency (e.g., 1-month backtest with quarterly rebalancing), the system completes the backtest without performing any rebalancing and logs a warning to inform the user that no rebalancing occurred
- How does the system handle a scenario where all assets in the portfolio have zero or negative values?
- **Transaction costs exceed available cash**: When transaction costs for a rebalancing operation would exceed the available cash balance, the system completes rebalancing using only the available cash (partial execution) and logs a warning about the insufficient funds
- How does the system handle extreme market volatility that causes asset prices to drop to zero?
- **Missing asset data at backtest start**: When a required asset has no price data at the backtest start date, the system aborts the backtest and returns a clear error message indicating which asset is missing data and the requested start date
- How does the system handle fractional shares vs. whole shares during rebalancing?
- **Strategy asset not in historical data**: When a strategy specifies an allocation to an asset that doesn't exist in the provided historical data, the system validates all strategy assets before starting the backtest and aborts with a clear error message identifying which assets are missing from the dataset

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a time period (start date and end date) for the backtest simulation
- **FR-002**: System MUST accept historical price data for all assets in the allocation strategy
- **FR-003**: System MUST apply the asset allocation rules to determine portfolio weights at each decision point
- **FR-004**: System MUST calculate portfolio value at each time step based on asset prices and holdings
- **FR-005**: System MUST support configurable rebalancing frequencies (daily, weekly, monthly, quarterly, annually, or never)
- **FR-006**: System MUST calculate required trades to rebalance the portfolio to target weights
- **FR-007**: System MUST track cash holdings separately from asset positions
- **FR-008**: System MUST generate performance metrics including: total return, annualized return, volatility (standard deviation of returns), maximum drawdown, and Sharpe ratio
- **FR-009**: System MUST handle cases where asset price data is missing by using forward-fill or skipping the period with appropriate logging
- **FR-010**: System MUST support configurable initial capital amount for the backtest
- **FR-011**: System MUST optionally apply transaction costs (fixed per-trade and/or percentage-based) to each trade
- **FR-012**: System MUST produce a time series of portfolio values throughout the backtest period
- **FR-013**: System MUST log all trades executed during the backtest with dates, assets, quantities, and prices
- **FR-014**: System MUST validate that the sum of target allocation weights equals 100% before running a backtest
- **FR-015**: System MUST handle zero or negative asset prices by treating them as data errors and halting the backtest with a clear error message
- **FR-016**: System MUST accept a configurable risk-free rate parameter for Sharpe ratio calculation, with a default value of 2%
- **FR-017**: System MUST support assets denominated in different currencies within the same portfolio
- **FR-018**: System MUST automatically fetch historical exchange rates when multi-currency portfolios are backtested
- **FR-019**: System MUST convert all portfolio values and returns to a base currency for consolidated performance reporting
- **FR-020**: System MUST abort the backtest with a clear error message if any required asset in the allocation strategy has no price data available at the backtest start date
- **FR-021**: System MUST validate that all assets specified in the allocation strategy exist in the provided historical price data before starting the backtest, and abort with a clear error message listing any missing assets
- **FR-022**: System MUST handle delisted assets by liquidating the position at the final available price and holding the proceeds as cash without reallocating to other assets

### Key Entities

- **Backtest Configuration**: Represents the setup for a backtest simulation, including start/end dates, initial capital, rebalancing frequency, transaction cost parameters, and reference to the allocation strategy
- **Portfolio State**: Represents the portfolio at a specific point in time, including cash balance, asset holdings (quantities), current prices, and total portfolio value
- **Trade**: Represents a buy or sell transaction, including timestamp, asset identifier, quantity, price, and transaction costs incurred
- **Performance Metrics**: Represents calculated performance statistics for a completed backtest, including returns (total, annualized, period-by-period), risk metrics (volatility, maximum drawdown, Sharpe ratio), and number of trades
- **Historical Price Data**: Represents time-series pricing information for assets, including date, asset identifier, and price (closing price or adjusted closing price)
- **Allocation Strategy**: Represents the target weights for each asset in the portfolio (e.g., 60% stocks, 40% bonds)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can run a backtest on 10 years of historical data for a portfolio of 5 assets and receive results within 30 seconds
- **SC-002**: Backtest calculations for a simple 60/40 stock/bond portfolio match manually calculated returns within 0.01% accuracy
- **SC-003**: Users can compare the performance of at least 3 different allocation strategies side-by-side using the same historical period
- **SC-004**: The system successfully completes backtests for at least 95% of valid input combinations without errors
- **SC-005**: Performance metrics (Sharpe ratio, max drawdown) calculated by the system match industry-standard calculation methods within acceptable rounding tolerance
- **SC-006**: Users can observe the impact of transaction costs by running the same backtest with costs enabled vs. disabled and seeing measurable difference in net returns
- **SC-007**: The system correctly handles historical datasets with up to 10% missing data points without producing incorrect results

## Assumptions *(if applicable)*

- Historical price data is available in a consistent format (CSV, database, or API)
- Asset prices represent end-of-day closing prices or adjusted closing prices (accounting for splits and dividends)
- The initial implementation assumes long-only positions (no short selling or leverage)
- Cash holdings earn zero return (no interest on cash balances) unless explicitly configured
- Rebalancing occurs at market close prices on the specified rebalancing date
- All assets are perfectly divisible (fractional shares are allowed) unless otherwise specified
- The risk-free rate for Sharpe ratio calculation is user-configurable with a default value of 2% (representing typical long-term treasury rates)
- When historical data includes corporate actions (splits, dividends), the prices are assumed to be already adjusted - users must provide clean, adjusted price data
- For multi-currency portfolios, the system supports multiple currencies with automatic exchange rate fetching from a data provider

## Dependencies *(if applicable)*

- Access to historical price data for backtesting (either user-provided files or integration with data provider)
- Access to historical exchange rate data for multi-currency portfolios (integration with exchange rate data provider)
- Understanding of which asset allocation strategies will be tested (the strategy definitions must exist before backtesting can occur)
- Agreement on performance metric calculation methods to ensure consistency with industry standards

## Out of Scope

The following are explicitly NOT included in this feature:

- Live trading or execution of strategies in real markets
- Optimization of allocation strategies (finding optimal weights)
- Machine learning or predictive modeling
- Portfolio visualization or charting (beyond basic metrics display)
- Multi-portfolio comparison dashboards
- Risk attribution analysis (understanding which assets contributed to risk/return)
- Options, futures, or other derivative instruments
- Short selling or leveraged positions
- Tax-aware analysis (tax-loss harvesting, capital gains tracking)
- Monte Carlo simulation or scenario analysis
- Benchmark comparison (comparing portfolio to S&P 500, etc.)
