# Value Rebalancing Analysis Scripts

## Overview

This document describes the Value Rebalancing analysis scripts that demonstrate the Value Averaging strategy based on Michael Edleson's methodology with William Bernstein's recommended parameters.

## Files Included

### Analysis Utilities
- `src/analysis/value_rebalancing_simulator.py` - Reusable Value Rebalancing simulator with Decimal precision

### Analysis Scripts
- `examples/spy_value_rebalancing_analysis.py` - SPY analysis with 7% growth rate
- `examples/tqqq_value_rebalancing_analysis.py` - TQQQ analysis with 10% growth rate
- `examples/tqqq_simple_analysis.py` - TQQQ buy-and-hold baseline analysis
- `examples/yearly_comparison_analysis.py` - Yearly cohort analysis (2019-2024)

### Bug Fixes
- `src/backtesting/metrics.py` - Fixed edge cases for extreme values (inf/nan handling)

## Value Rebalancing Strategy

### Core Concept
Value Rebalancing (Value Averaging) is an investment strategy that:
- Sets a target value path based on expected growth rate
- Rebalances when portfolio deviates significantly from target
- Systematically buys low and sells high

### Parameters Used (Bernstein Recommendations)

**SPY (Stable ETF)**:
- **Growth rate**: 7% annual (William Bernstein's conservative estimate)
- **Rebalancing frequency**: 30 days (monthly)
- **Target allocation**: 80% stocks, 20% cash

**TQQQ (3x Leveraged ETF)**:
- **Growth rate**: 10% annual (Bernstein 7% baseline + leverage adjustment)
- **Rebalancing frequency**: 30 days (monthly)
- **Target allocation**: 80% stocks, 20% cash

## Running the Analysis

### Prerequisites
```bash
# Install dependencies
uv sync

# yfinance is already included in dependencies
```

### Run Individual Analyses
```bash
# SPY Value Rebalancing
uv run python examples/spy_value_rebalancing_analysis.py

# TQQQ Value Rebalancing
uv run python examples/tqqq_value_rebalancing_analysis.py

# TQQQ Simple (Buy-and-Hold)
uv run python examples/tqqq_simple_analysis.py

# Yearly Comparison
uv run python examples/yearly_comparison_analysis.py
```

## Key Results (2019-2024, 6 years)

### TQQQ Analysis
**Buy & Hold**:
- Return: +797.5% ($10k → $89.7k)
- Volatility: 72.0%
- Max Drawdown: -81.7%

**Value Rebalancing (10% growth target)**:
- Return: +335.9% ($10k → $43.6k)
- Volatility: 32.1% (**-39.9%p reduction**)
- Max Drawdown: -44.4% (**+37.3%p improvement**)
- Rebalances: 29 trades

**Trade-off**: -461.6%p return for significantly reduced risk

### SPY Analysis
**Buy & Hold**:
- Return: +158.4% ($10k → $25.8k)
- Volatility: 19.8%
- Max Drawdown: -33.7%

**Value Rebalancing (7% growth target)**:
- Return: +106.4% ($10k → $20.6k)
- Volatility: 14.5% (**-5.4%p reduction**)
- Max Drawdown: -26.6% (**+7.1%p improvement**)
- Rebalances: 11 trades

**Trade-off**: -52.0%p return for modest risk reduction

### Yearly Cohort Analysis

**Value Rebalancing Outperformed** in volatile/bear markets:
- **2021 start**: +30.2%p excess (VR: +124.0% vs BH: +93.8%)
- **2022 start**: +8.6%p excess (VR: +7.0% vs BH: -1.6% **loss**)

**Buy-and-Hold Outperformed** in strong bull markets:
- **2019 start**: -461.6%p (long bull run)
- **2023 start**: -220.3%p (strong recovery)

## Risk Management Benefits

### Average Across All Cohorts (2019-2024)
- **Volatility reduction**: 21.0%p for TQQQ, 5.3%p for SPY
- **Max drawdown improvement**: 17.5%p for TQQQ, 7.1%p for SPY

### Best Case (2019 start, TQQQ)
- Volatility: 72.0% → 32.1% (**cut in half**)
- Max Drawdown: -81.7% → -44.4% (**37.3%p improvement**)

## Use Cases

### Value Rebalancing Recommended For:
✅ Risk-conscious investors prioritizing stability
✅ Volatile/sideways markets (2020-2022 COVID + bear market)
✅ Medium-term horizons (3-5 years)
✅ Leveraged ETFs with high volatility

### Buy-and-Hold Recommended For:
✅ Aggressive investors prioritizing maximum returns
✅ Strong bull markets (2019, 2023)
✅ Long-term horizons (5+ years)
✅ High risk tolerance

## Using the Simulator

The Value Rebalancing simulator can be reused for other analyses:

```python
from decimal import Decimal
from src.analysis.value_rebalancing_simulator import (
    ValueRebalancingSimulator,
    ValueRebalancingParameters,
)
import yfinance as yf

# Download price data
data = yf.download("SPY", start="2019-01-01", end="2024-12-31", auto_adjust=True)

# Configure parameters
params = ValueRebalancingParameters(
    value_growth_rate=Decimal("0.07"),  # 7% annual growth
    rebalance_frequency_days=30,  # Monthly rebalancing
    initial_capital=Decimal("10000"),  # $10,000 starting capital
)

# Run simulation
simulator = ValueRebalancingSimulator(params)
result = simulator.simulate(data)

print(f"Final value: ${result.final_value}")
print(f"Return: {(result.final_value / params.initial_capital - 1) * 100:.2f}%")
print(f"Rebalances: {result.rebalance_count}")
```

## References

- Michael Edleson - [Value Averaging: The Safe and Easy Strategy for Higher Investment Returns](https://www.bogleheads.org/wiki/Value_averaging)
- William Bernstein - [Value Averaging Guide](https://humbledollar.com/money-guide/value-averaging/)
- Bogleheads Wiki - [Value Averaging](https://www.bogleheads.org/wiki/Value_averaging)

## Future Work

1. Parameter sensitivity analysis
2. Multi-asset Value Rebalancing
3. Integration with existing BacktestEngine framework
4. Real-time portfolio tracking
