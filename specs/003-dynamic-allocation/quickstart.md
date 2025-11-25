# Quickstart: Dynamic Asset Allocation Strategies

**Feature**: 003-dynamic-allocation
**Date**: 2025-11-24
**Purpose**: Practical usage examples for each dynamic allocation strategy type

## Overview

This guide provides copy-paste ready examples for using dynamic allocation strategies with the backtesting engine. Each example demonstrates strategy configuration, parameter tuning, and result interpretation.

---

## Example 1: Momentum Strategy

### Basic Usage (120-day Momentum)

```python
from datetime import date
from decimal import Decimal
from src.strategies.momentum import MomentumStrategy, MomentumParameters
from src.backtesting.engine import BacktestEngine
from src.models.backtest_config import BacktestConfiguration
from src.data.loaders import CSVDataProvider

# Load historical price data
data_provider = CSVDataProvider("data/prices.csv")
price_data = data_provider.load_prices(
    start_date=date(2015, 1, 1),
    end_date=date(2020, 12, 31)
)

# Configure momentum strategy
momentum_params = MomentumParameters(
    lookback_days=120,  # 6-month momentum
    assets=["SPY", "AGG", "GLD"],
    exclude_negative=True  # Move to cash if negative
)

strategy = MomentumStrategy(
    name="Momentum 120-day",
    parameters=momentum_params
)

# Run backtest
config = BacktestConfiguration(
    start_date=date(2015, 6, 1),  # Allow 120 days for initial calculation
    end_date=date(2020, 12, 31),
    initial_capital=Decimal("100000"),
    rebalancing_frequency="MONTHLY"
)

engine = BacktestEngine()
result = engine.run_backtest(strategy, config, price_data)

# View results
print(f"Total Return: {result.metrics.total_return:.2%}")
print(f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.metrics.max_drawdown:.2%}")
```

### Parameter Tuning Example

```python
# Test multiple lookback periods
lookback_periods = [60, 90, 120, 180, 252]
results = {}

for lookback in lookback_periods:
    params = MomentumParameters(
        lookback_days=lookback,
        assets=["SPY", "AGG", "GLD"],
        exclude_negative=True
    )

    strategy = MomentumStrategy(
        name=f"Momentum {lookback}d",
        parameters=params
    )

    result = engine.run_backtest(strategy, config, price_data)
    results[lookback] = result.metrics.sharpe_ratio

# Find optimal lookback period
best_lookback = max(results, key=results.get)
print(f"Best lookback period: {best_lookback} days")
print(f"Sharpe ratio: {results[best_lookback]:.2f}")
```

### Using Minimum Momentum Threshold

```python
# Only allocate to assets with at least 5% momentum
momentum_params = MomentumParameters(
    lookback_days=120,
    assets=["SPY", "AGG", "GLD", "TLT", "VNQ"],
    exclude_negative=False,  # Keep negative if above min
    min_momentum=Decimal("0.05")  # 5% minimum threshold
)

strategy = MomentumStrategy(
    name="Momentum 120d (5% min)",
    parameters=momentum_params
)

result = engine.run_backtest(strategy, config, price_data)
```

---

## Example 2: Risk Parity Strategy

### Basic Usage (Inverse Volatility)

```python
from src.strategies.risk_parity import RiskParityStrategy, RiskParityParameters

# Configure risk parity strategy
risk_parity_params = RiskParityParameters(
    lookback_days=120,  # 6-month volatility estimation
    assets=["SPY", "AGG", "GLD"],
    target_volatility=None,  # No leverage, unlevered weights
    min_volatility_threshold=Decimal("0.0001"),  # 0.01% minimum
    annualization_factor=252  # Daily data
)

strategy = RiskParityStrategy(
    name="Risk Parity 120-day",
    parameters=risk_parity_params
)

# Run backtest
result = engine.run_backtest(strategy, config, price_data)

print(f"Portfolio Volatility: {result.metrics.volatility:.2%}")
print(f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
```

### With Risk Target (Levered)

```python
# Target 10% annual volatility
risk_parity_params = RiskParityParameters(
    lookback_days=120,
    assets=["SPY", "AGG", "GLD"],
    target_volatility=Decimal("0.10"),  # 10% target
    min_volatility_threshold=Decimal("0.0001"),
    annualization_factor=252
)

strategy = RiskParityStrategy(
    name="Risk Parity 10% Vol Target",
    parameters=risk_parity_params
)

result = engine.run_backtest(strategy, config, price_data)

# Verify portfolio volatility near target
actual_vol = result.metrics.volatility
target_vol = float(risk_parity_params.target_volatility)
print(f"Target volatility: {target_vol:.2%}")
print(f"Actual volatility: {actual_vol:.2%}")
print(f"Difference: {abs(actual_vol - target_vol):.2%}")
```

---

## Example 3: Dual Moving Average Strategy

### Basic Usage (50/200 Golden Cross)

```python
from src.strategies.dual_momentum import DualMomentumStrategy, DualMomentumParameters

# Configure dual MA strategy
dual_ma_params = DualMomentumParameters(
    lookback_days=200,  # Must be >= long_window
    assets=["SPY", "AGG", "GLD"],
    short_window=50,
    long_window=200,
    use_signal_strength=False  # Binary signals (MVP)
)

strategy = DualMomentumStrategy(
    name="Dual MA 50/200",
    parameters=dual_ma_params
)

# Run backtest
config = BacktestConfiguration(
    start_date=date(2015, 9, 1),  # Allow 200 days for MA calculation
    end_date=date(2020, 12, 31),
    initial_capital=Decimal("100000"),
    rebalancing_frequency="WEEKLY"  # More responsive to trend changes
)

result = engine.run_backtest(strategy, config, price_data)
print(f"Total Return: {result.metrics.total_return:.2%}")
```

### Shorter-term Trend Following (20/60)

```python
# Faster-moving strategy
dual_ma_params = DualMomentumParameters(
    lookback_days=60,
    assets=["SPY", "AGG", "GLD"],
    short_window=20,
    long_window=60,
    use_signal_strength=False
)

strategy = DualMomentumStrategy(
    name="Dual MA 20/60",
    parameters=dual_ma_params
)

# Use daily rebalancing for more responsive execution
config.rebalancing_frequency = "DAILY"
result = engine.run_backtest(strategy, config, price_data)
```

---

## Example 4: Comparing Strategies

### Static vs Dynamic Comparison

```python
from src.models.strategy import AllocationStrategy

# Static 60/40 benchmark
static_strategy = AllocationStrategy(
    name="60/40 Portfolio",
    asset_weights={
        "SPY": Decimal("0.6"),
        "AGG": Decimal("0.4")
    }
)

# Dynamic momentum strategy
momentum_params = MomentumParameters(
    lookback_days=120,
    assets=["SPY", "AGG"],
    exclude_negative=True
)
momentum_strategy = MomentumStrategy(
    name="Dynamic Momentum",
    parameters=momentum_params
)

# Run both backtests
static_result = engine.run_backtest(static_strategy, config, price_data)
dynamic_result = engine.run_backtest(momentum_strategy, config, price_data)

# Compare results
comparison = {
    "Strategy": ["Static 60/40", "Dynamic Momentum"],
    "Total Return": [
        f"{static_result.metrics.total_return:.2%}",
        f"{dynamic_result.metrics.total_return:.2%}"
    ],
    "Sharpe Ratio": [
        f"{static_result.metrics.sharpe_ratio:.2f}",
        f"{dynamic_result.metrics.sharpe_ratio:.2f}"
    ],
    "Max Drawdown": [
        f"{static_result.metrics.max_drawdown:.2%}",
        f"{dynamic_result.metrics.max_drawdown:.2%}"
    ],
    "Num Trades": [
        static_result.metrics.num_trades,
        dynamic_result.metrics.num_trades
    ]
}

import pandas as pd
df = pd.DataFrame(comparison)
print(df.to_string(index=False))
```

### Multi-Strategy Comparison

```python
strategies = {
    "Momentum 60d": MomentumStrategy(
        name="Momentum 60d",
        parameters=MomentumParameters(lookback_days=60, assets=["SPY", "AGG", "GLD"], exclude_negative=True)
    ),
    "Momentum 120d": MomentumStrategy(
        name="Momentum 120d",
        parameters=MomentumParameters(lookback_days=120, assets=["SPY", "AGG", "GLD"], exclude_negative=True)
    ),
    "Risk Parity": RiskParityStrategy(
        name="Risk Parity",
        parameters=RiskParityParameters(lookback_days=120, assets=["SPY", "AGG", "GLD"])
    ),
    "Dual MA 50/200": DualMomentumStrategy(
        name="Dual MA 50/200",
        parameters=DualMomentumParameters(lookback_days=200, assets=["SPY", "AGG", "GLD"], short_window=50, long_window=200)
    )
}

results = {}
for name, strategy in strategies.items():
    result = engine.run_backtest(strategy, config, price_data)
    results[name] = {
        "Return": result.metrics.total_return,
        "Sharpe": result.metrics.sharpe_ratio,
        "MaxDD": result.metrics.max_drawdown
    }

# Print comparison table
df = pd.DataFrame(results).T
print(df)
```

---

## Example 5: Parameter Optimization

### Grid Search for Momentum

```python
import itertools

# Define parameter grid
lookback_days = [60, 90, 120, 180]
exclude_negative_options = [True, False]

param_grid = list(itertools.product(lookback_days, exclude_negative_options))

optimization_results = []

for lookback, exclude_neg in param_grid:
    params = MomentumParameters(
        lookback_days=lookback,
        assets=["SPY", "AGG", "GLD"],
        exclude_negative=exclude_neg
    )

    strategy = MomentumStrategy(
        name=f"Momentum_{lookback}d_exclude{exclude_neg}",
        parameters=params
    )

    result = engine.run_backtest(strategy, config, price_data)

    optimization_results.append({
        "lookback_days": lookback,
        "exclude_negative": exclude_neg,
        "sharpe_ratio": result.metrics.sharpe_ratio,
        "total_return": result.metrics.total_return,
        "max_drawdown": result.metrics.max_drawdown
    })

# Find best parameters by Sharpe ratio
df = pd.DataFrame(optimization_results)
best = df.loc[df["sharpe_ratio"].idxmax()]
print("Best parameters:")
print(best)
```

---

## Example 6: Handling Edge Cases

### Monitoring Data Availability

```python
# Access calculated weights to see excluded assets
result = engine.run_backtest(strategy, config, price_data)

# Examine specific rebalancing date
for state in result.portfolio_history:
    if hasattr(state, 'calculated_weights'):
        weights = state.calculated_weights
        if weights.excluded_assets:
            print(f"Date: {weights.calculation_date}")
            print(f"Excluded: {weights.excluded_assets}")
            print(f"Reason: Missing data or threshold violation")
```

### Detecting Previous Weight Usage

```python
# Check if strategy frequently used previous weights (data issues)
rebalance_count = 0
previous_weight_count = 0

for state in result.portfolio_history:
    if hasattr(state, 'calculated_weights'):
        rebalance_count += 1
        if state.calculated_weights.used_previous_weights:
            previous_weight_count += 1

usage_rate = previous_weight_count / rebalance_count if rebalance_count > 0 else 0
print(f"Previous weight usage rate: {usage_rate:.1%}")

if usage_rate > 0.10:  # More than 10%
    print("WARNING: High previous weight usage indicates data quality issues")
```

---

## Common Pitfalls & Tips

### 1. Insufficient Historical Data

**Problem**: Backtest starts before enough data available for lookback

**Solution**: Adjust start date to allow for lookback period

```python
# For 120-day momentum, start at least 120 days after data begins
data_start = price_data['date'].min()
backtest_start = data_start + timedelta(days=150)  # Add buffer

config.start_date = backtest_start
```

### 2. Rebalancing Frequency Mismatch

**Problem**: Daily rebalancing with weekly price data causes errors

**Solution**: Match rebalancing frequency to data granularity

```python
# Daily data → Can use DAILY, WEEKLY, MONTHLY
# Weekly data → Use WEEKLY or MONTHLY only
# Monthly data → Use MONTHLY only

config.rebalancing_frequency = "MONTHLY"  # Safe for most data
```

### 3. High Turnover with Short Lookbacks

**Problem**: Short lookback periods (< 60 days) create excessive trading

**Solution**: Use longer lookback or less frequent rebalancing

```python
# Option 1: Increase lookback
params.lookback_days = 120  # Instead of 30

# Option 2: Reduce rebalancing frequency
config.rebalancing_frequency = "QUARTERLY"  # Instead of MONTHLY
```

### 4. Strategy Parameter Validation

**Problem**: Invalid parameters cause runtime errors

**Solution**: Validate parameters before running backtest

```python
try:
    strategy.validate_parameters()
    print("Parameters valid ✓")
except ValueError as e:
    print(f"Parameter validation failed: {e}")
    # Fix parameters before proceeding
```

---

## Next Steps

1. **Read research.md**: Understand algorithm theory and academic references
2. **Review data-model.md**: Study entity relationships and validation rules
3. **Check contracts/**: See exact calculation specifications for each strategy
4. **Run tests**: Execute contract tests to verify numerical accuracy
5. **Experiment**: Try different parameters and compare results

---

**Quickstart Complete**: Ready for implementation and testing
