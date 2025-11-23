# Implementation Plan: Backtesting Logic

**Branch**: `001-backtesting-logic` | **Date**: 2025-11-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-backtesting-logic/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement backtesting logic to simulate asset allocation strategies against historical market data. The system will accept time periods, historical price data, and allocation strategies, then execute the strategy rules to calculate portfolio performance metrics (returns, drawdowns, Sharpe ratio). Core functionality includes periodic rebalancing, transaction cost modeling, and handling of real-world data issues (missing prices, delisted assets, market holidays).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: pandas (≥2.0), numpy (≥1.24), pytest (≥7.0), hypothesis (≥6.0), requests (≥2.31)
**Storage**: CSV files for historical price data (initial implementation), exchangerate.host API for exchange rates
**Testing**: pytest with three-tier structure (unit, integration, contract tests), hypothesis for property-based testing
**Target Platform**: CLI application / Python library, cross-platform (Linux/macOS/Windows)
**Project Type**: single (backtesting engine library/service)
**Performance Goals**: Backtest 10 years of data for 5 assets within 30 seconds (SC-001)
**Constraints**: Calculation accuracy within 0.01% of manual calculations (SC-002), 95% success rate for valid inputs (SC-004)
**Scale/Scope**: Support portfolios with 5-10 assets, 10 years of daily historical data, handle datasets with up to 10% missing data (SC-007)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Test-First Development (NON-NEGOTIABLE)
- ✅ **PASS**: Feature spec includes comprehensive user stories with acceptance scenarios
- ✅ **PASS**: Plan includes test strategy requirement before implementation
- ✅ **PASS**: Three-tier test strategy defined (unit, integration, contract) in research.md
- ✅ **PASS**: Test fixtures and reference scenarios documented (SPY 2010-2020, 60/40 portfolio, 2008 crisis)
- ✅ **PASS**: Property-based testing with hypothesis for comprehensive coverage
- ⏳ **PENDING**: Tests will be written and approved before implementation begins (Phase 2)

### II. Financial Data Accuracy (NON-NEGOTIABLE)
- ✅ **PASS**: Spec defines accuracy requirements (0.01% tolerance in SC-002)
- ✅ **PASS**: Spec requires reproducible results and documented formulas
- ✅ **PASS**: Edge cases explicitly documented (missing data, delistings, holidays)
- ✅ **PASS**: Calculation formulas documented with authoritative references (Sharpe 1994, standard financial definitions)
- ✅ **PASS**: Explicit rounding behavior defined in data-model.md (4 decimal places for percentages, 2 for currency)
- ✅ **PASS**: Decimal precision specified to avoid floating-point errors
- ✅ **PASS**: Audit trail via Trade records and PortfolioState history

### III. Simplicity (Start Simple, Justify Complexity)
- ✅ **PASS**: Feature implements minimal viable backtesting (no optimization, ML, or advanced features)
- ✅ **PASS**: Out-of-scope section clearly excludes speculative features
- ✅ **PASS**: Technology choices justified in research.md (Python ecosystem, pandas/numpy, CSV files)
- ✅ **PASS**: Minimal dependency set (5 libraries, all justified)
- ✅ **PASS**: Started with CSV files (simplest), not database
- ✅ **PASS**: No unnecessary abstractions - direct implementations

**GATE STATUS POST-DESIGN**: ✅ PASS - All constitution principles satisfied. Ready for Phase 2 (Task Generation).

### Complexity Tracking Post-Design

No violations detected. All complexity justified:

| Component | Justification |
|-----------|---------------|
| pandas/numpy | Required for time-series handling and performance (SC-001: 30-second requirement) |
| pytest/hypothesis | Required for Test-First Development principle compliance |
| requests library | Required for FR-018 (automatic exchange rate fetching) |
| exchangerate.host API | External dependency justified - manual entry too error-prone for multi-currency |
| CSV format | Simplest possible storage, no database overhead |

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── backtesting/
│   ├── engine.py           # Core backtest execution logic
│   ├── portfolio.py        # Portfolio state management
│   ├── rebalancer.py       # Rebalancing logic
│   ├── metrics.py          # Performance calculation (returns, Sharpe, drawdown)
│   └── data_loader.py      # Historical price data loading/validation
├── models/
│   ├── backtest_config.py  # Backtest configuration
│   ├── trade.py            # Trade representation
│   └── allocation.py       # Allocation strategy definition
└── utils/
    ├── date_utils.py       # Market calendar, business day logic
    └── currency.py         # Multi-currency support

tests/
├── unit/
│   ├── test_portfolio.py
│   ├── test_rebalancer.py
│   ├── test_metrics.py
│   └── test_data_loader.py
├── integration/
│   └── test_backtest_engine.py
└── contract/
    └── test_acceptance_scenarios.py  # User story acceptance tests
```

**Structure Decision**: Single project structure selected. This is a pure calculation/simulation engine without UI requirements. The backtesting module contains core logic, models define data structures, and utils provide supporting functionality. Tests follow the three-tier structure (unit, integration, contract) per TDD requirements.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
