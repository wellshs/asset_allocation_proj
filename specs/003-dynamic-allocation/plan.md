# Implementation Plan: Dynamic Asset Allocation with Historical Data Analysis

**Branch**: `003-dynamic-allocation` | **Date**: 2025-11-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-dynamic-allocation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature extends the existing static allocation strategy framework to support dynamic allocation strategies that calculate asset weights based on historical data analysis. Three strategy types will be implemented: momentum-based (returns lookback), volatility-adjusted (risk parity), and dual moving average (trend following). The system must integrate seamlessly with the existing BacktestEngine while supporting parameter configuration, data validation, and edge case handling (insufficient data, missing values, negative returns, zero volatility).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: pandas (≥2.0), numpy (≥1.24), existing dataclasses/Decimal for precision
**Storage**: CSV-based historical price data (existing CSVDataProvider)
**Testing**: pytest (≥7.0) with existing unit/integration/contract test structure
**Target Platform**: Local execution (backtesting simulation)
**Project Type**: Single project (src/, tests/ structure)
**Performance Goals**:
- Weight calculation: <100ms per date for 10 assets with 250-day lookback
- Backtest execution: ≤2x static strategy time for equivalent date ranges
- Parameter optimization: 50 combinations for 5-year backtest in <30 minutes
**Constraints**:
- No look-ahead bias (only use data before calculation date)
- Numerical precision using Decimal type for weight calculations
- Weights must sum to exactly 1.0 (0.0001 tolerance)
**Scale/Scope**:
- Support 5-20 assets per portfolio
- Lookback windows: 30-250 trading days
- Backtest date ranges: 1-10 years
- Parameter combinations for optimization: 10-100

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Test-First Development (NON-NEGOTIABLE)

**Status**: ✅ PASS

**Plan Alignment**:
- Phase 0 includes test strategy definition in research.md
- Phase 1 includes contract test specifications for weight calculations
- Phase 2 (tasks.md) will follow Red-Green-Refactor cycle:
  1. Write failing tests for each strategy type
  2. Implement strategy to pass tests
  3. Refactor with tests as safety net
- All three strategy types (momentum, risk parity, dual MA) will have unit tests before implementation
- Integration tests will verify engine integration before merging

**Test Coverage Plan**:
- Unit tests: Strategy weight calculation logic (momentum scores, volatility calculations, MA crossovers)
- Integration tests: Dynamic strategies with BacktestEngine
- Contract tests: Numerical accuracy for financial calculations (returns, volatility, weight normalization)
- Edge case tests: Insufficient data, missing values, negative returns, zero volatility

### II. Financial Data Accuracy (NON-NEGOTIABLE)

**Status**: ✅ PASS

**Accuracy Requirements**:
- **Momentum calculation**: Cumulative return = (price_end / price_start) - 1.0, documented with reference to standard momentum literature
- **Volatility calculation**: Annualized standard deviation = daily_std * sqrt(252), using pandas std() with ddof=1 (sample standard deviation)
- **Risk parity weights**: Inverse volatility weighting, normalized to sum = 1.0
- **Moving averages**: Simple moving average (SMA) = mean(prices over window), using pandas rolling().mean()
- **Weight normalization**: Sum must equal 1.0 within 0.0001 tolerance (existing validation)
- **Rounding**: Decimal type for all calculations, round to 4 decimal places for weights
- **Reproducibility**: All calculations deterministic given same input data and parameters

**Edge Case Documentation** (from clarifications):
- Insufficient data: Skip calculation, use previous weights
- Missing data points: Exclude asset from calculation
- All negative returns: Allocate 100% to cash
- Zero volatility: Exclude asset from volatility-based calculations

**References**:
- Momentum: Jegadeesh & Titman (1993), "Returns to Buying Winners and Selling Losers"
- Risk Parity: Qian (2005), "Risk Parity Portfolios"
- Dual Momentum: Antonacci (2014), "Dual Momentum Investing"

### III. Simplicity (Start Simple, Justify Complexity)

**Status**: ✅ PASS - No violations requiring justification

**Simplicity Adherence**:
- **Extends existing AllocationStrategy model**: No new framework, builds on proven pattern
- **Uses existing pandas/numpy**: No new numerical libraries needed
- **Standard algorithm implementations**: Direct calculations, no ML frameworks
- **Reuses existing validation**: Weight sum validation, price data validation
- **Minimal abstraction**: Three concrete strategy classes, not a complex hierarchy
- **No premature optimization**: Straightforward calculations, optimize only if performance gates fail

**No Complexity Violations**: This feature adds domain logic (strategy calculations) to existing architecture without introducing new frameworks, patterns, or abstractions that require justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-dynamic-allocation/
├── plan.md              # This file
├── research.md          # Phase 0: Algorithm research, best practices
├── data-model.md        # Phase 1: Strategy entities, parameters, weights
├── quickstart.md        # Phase 1: Usage examples for each strategy type
├── contracts/           # Phase 1: Weight calculation accuracy specs
│   ├── momentum.md      # Momentum calculation contract
│   ├── risk-parity.md   # Volatility calculation contract
│   └── dual-ma.md       # Moving average calculation contract
└── tasks.md             # Phase 2: Implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── strategy.py                    # [EXTEND] Add DynamicAllocationStrategy base
│   ├── strategy_params.py             # [NEW] Strategy parameter configurations
│   └── calculated_weights.py          # [NEW] Weight calculation result with metadata
├── strategies/                        # [NEW] Dynamic strategy implementations
│   ├── __init__.py
│   ├── base.py                        # [NEW] Abstract base for dynamic strategies
│   ├── momentum.py                    # [NEW] MomentumStrategy implementation
│   ├── risk_parity.py                 # [NEW] RiskParityStrategy implementation
│   ├── dual_momentum.py               # [NEW] DualMomentumStrategy implementation
│   └── utils.py                       # [NEW] Shared calculation utilities
├── backtesting/
│   ├── engine.py                      # [EXTEND] Support dynamic weight calculation
│   ├── rebalancer.py                  # [MINOR] Accept dynamic weights
│   └── price_window.py                # [NEW] Historical data window extraction
└── data/
    └── validation.py                  # [EXTEND] Validate lookback data completeness

tests/
├── unit/
│   ├── strategies/                    # [NEW] Strategy calculation tests
│   │   ├── test_momentum.py
│   │   ├── test_risk_parity.py
│   │   ├── test_dual_momentum.py
│   │   └── test_strategy_utils.py
│   ├── test_price_window.py           # [NEW] Window extraction tests
│   └── test_strategy_params.py        # [NEW] Parameter validation tests
├── integration/
│   ├── test_dynamic_backtest.py       # [NEW] End-to-end dynamic strategy tests
│   └── test_strategy_comparison.py    # [NEW] Static vs dynamic comparison
├── contract/
│   ├── test_momentum_accuracy.py      # [NEW] Momentum calculation accuracy
│   ├── test_risk_parity_accuracy.py   # [NEW] Volatility calculation accuracy
│   └── test_dual_ma_accuracy.py       # [NEW] Moving average accuracy
└── fixtures/
    └── multi_asset_2015_2020.csv      # [NEW] Extended test data for strategies
```

**Structure Decision**: Single project structure maintained. Dynamic strategies organized in new `src/strategies/` package to separate domain logic from infrastructure (backtesting, data loading). This aligns with existing pattern where `src/models/` contains data structures and `src/backtesting/` contains execution logic. New `strategies/` package sits between them, consuming models and providing calculated weights to the backtesting engine.

## Complexity Tracking

No violations - complexity tracking table not required. All additions are domain logic extending existing architecture patterns.
