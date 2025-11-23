# Tasks: Backtesting Logic

**Input**: Design documents from `/specs/001-backtesting-logic/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: All test tasks are REQUIRED per constitution (Test-First Development is NON-NEGOTIABLE)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `src/`, `tests/` at repository root
- All paths are absolute from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization with uv and basic structure

- [X] T001 Initialize Python project with uv (uv init)
- [X] T002 Configure pyproject.toml with dependencies (pandas>=2.0.0, numpy>=1.24.0, pytest>=7.0.0, hypothesis>=6.0.0, requests>=2.31.0)
- [X] T003 [P] Create project structure: src/backtesting/, src/data/, src/models/, src/cli/
- [X] T004 [P] Create test structure: tests/unit/, tests/integration/, tests/contract/, tests/fixtures/
- [X] T005 [P] Configure pytest.ini with test discovery and coverage settings
- [X] T006 [P] Add .gitignore for Python (.venv/, __pycache__/, *.pyc, .pytest_cache/)
- [X] T007 Create README.md with project overview and setup instructions

**Checkpoint**: Project structure ready, uv environment configured

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and provider interfaces that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Data Models (Required by all stories)

- [X] T008 [P] Create RebalancingFrequency enum in src/models/__init__.py
- [X] T009 [P] Create TransactionCosts dataclass in src/models/backtest_config.py
- [X] T010 [P] Create BacktestConfiguration dataclass with validation in src/models/backtest_config.py
- [X] T011 [P] Create AllocationStrategy dataclass with weight validation in src/models/strategy.py
- [X] T012 [P] Create PortfolioState dataclass with computed total_value in src/models/portfolio_state.py
- [X] T013 [P] Create Trade dataclass with validation in src/models/trade.py
- [X] T014 [P] Create PerformanceMetrics dataclass in src/models/performance.py

### Custom Exceptions

- [X] T015 [P] Create custom exceptions (BacktestError, DataError, CurrencyError, APIError) in src/backtesting/exceptions.py

### Provider Interfaces (Abstract base classes)

- [X] T016 [P] Create HistoricalDataProvider abstract interface in src/data/providers.py
- [X] T017 [P] Create ExchangeRateProvider abstract interface in src/data/providers.py

### Data Validation Utilities

- [X] T018 [P] Implement validate_price_data() function in src/data/validation.py
- [X] T019 [P] Implement validate_exchange_rate_data() function in src/data/validation.py

**Checkpoint**: Foundation ready - all data models and interfaces defined, user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Run Basic Backtest on Historical Data (Priority: P1) 🎯 MVP

**Goal**: Users can run a backtest on historical data for a portfolio and receive performance metrics (returns, Sharpe ratio, drawdown)

**Independent Test**: Load sample 60/40 portfolio data, run backtest for 2010-2020, verify returns match manual calculations within 0.01%

### Tests for User Story 1 (Write FIRST, ensure they FAIL)

- [X] T020 [P] [US1] Create test fixtures: tests/fixtures/spy_2010_2020.csv (SPY historical prices)
- [X] T021 [P] [US1] Create test fixtures: tests/fixtures/agg_2010_2020.csv (AGG historical prices)
- [X] T022 [P] [US1] Create test fixtures: tests/fixtures/expected_results.json (known metric values)
- [X] T023 [P] [US1] Unit test for portfolio initialization in tests/unit/test_portfolio.py
- [X] T024 [P] [US1] Unit test for performance metric calculations in tests/unit/test_metrics.py
- [X] T025 [P] [US1] Contract test for SPY buy-and-hold 2010-2020 in tests/contract/test_calculation_accuracy.py
- [X] T026 [P] [US1] Contract test for 60/40 SPY/AGG portfolio in tests/contract/test_calculation_accuracy.py
- [X] T027 [P] [US1] Integration test for end-to-end backtest execution in tests/integration/test_backtest_engine.py

**⚠️ VERIFY**: All tests above should FAIL (Red phase) before proceeding to implementation

### Implementation for User Story 1

- [X] T028 [P] [US1] Implement CSVDataProvider.load_prices() in src/data/loaders.py
- [X] T029 [P] [US1] Implement CSVDataProvider.validate_data() in src/data/loaders.py
- [X] T030 [US1] Implement BacktestEngine._initialize_portfolio() in src/backtesting/engine.py
- [X] T031 [US1] Implement BacktestEngine._get_prices_for_date() with forward-fill in src/backtesting/engine.py
- [X] T032 [US1] Implement performance metric calculations in src/backtesting/metrics.py (total_return, annualized_return, volatility, max_drawdown, sharpe_ratio per research.md formulas)
- [X] T033 [US1] Implement BacktestEngine.run_backtest() basic flow (no rebalancing, no transaction costs) in src/backtesting/engine.py
- [X] T034 [US1] Create BacktestResult dataclass in src/models/__init__.py
- [X] T035 [US1] Add PerformanceMetrics.to_dict() formatting method in src/models/performance.py

**⚠️ VERIFY**: All US1 tests should now PASS (Green phase)

**Checkpoint**: At this point, basic backtesting works - users can load CSV data, run buy-and-hold backtest, get accurate performance metrics

---

## Phase 4: User Story 2 - Simulate Periodic Rebalancing (Priority: P2)

**Goal**: Users can configure rebalancing frequency (monthly, quarterly, annually) and observe portfolio rebalancing to target weights

**Independent Test**: Run 60/40 portfolio with quarterly rebalancing, verify rebalancing occurs at expected dates and weights return to target (60/40)

### Tests for User Story 2 (Write FIRST, ensure they FAIL)

- [X] T036 [P] [US2] Unit test for rebalancing trade calculations in tests/unit/test_rebalancer.py
- [X] T037 [P] [US2] Unit test for rebalancing date generation (quarterly, monthly, annually) in tests/unit/test_rebalancer.py
- [X] T038 [P] [US2] Integration test for quarterly rebalancing backtest in tests/integration/test_backtest_engine.py
- [X] T039 [P] [US2] Property-based test: portfolio weights sum to 1.0 after rebalancing in tests/unit/test_rebalancer.py

**⚠️ VERIFY**: All tests above should FAIL (Red phase)

### Implementation for User Story 2

- [X] T040 [P] [US2] Implement rebalancing date generation based on RebalancingFrequency in src/backtesting/rebalancer.py
- [X] T041 [US2] Implement BacktestEngine._rebalance_portfolio() to calculate required trades in src/backtesting/engine.py
- [X] T042 [US2] Integrate rebalancing logic into BacktestEngine.run_backtest() main loop in src/backtesting/engine.py
- [X] T043 [US2] Update portfolio state after rebalancing (adjust holdings and cash) in src/backtesting/engine.py

**⚠️ VERIFY**: All US2 tests should now PASS (Green phase)

**Checkpoint**: At this point, User Stories 1 AND 2 both work - users can run buy-and-hold OR periodic rebalancing backtests

---

## Phase 5: User Story 3 - Apply Transaction Costs and Slippage (Priority: P3)

**Goal**: Users can configure transaction costs (fixed and percentage-based) and see realistic net performance after trading costs

**Independent Test**: Run same backtest with and without transaction costs, verify version with costs shows lower net returns by expected amount

### Tests for User Story 3 (Write FIRST, ensure they FAIL)

- [X] T044 [P] [US3] Unit test for transaction cost calculation (fixed + percentage) in tests/unit/test_portfolio.py
- [X] T045 [P] [US3] Integration test comparing backtest with/without transaction costs in tests/integration/test_backtest_engine.py
- [X] T046 [P] [US3] Property-based test: transaction costs always reduce returns in tests/unit/test_portfolio.py

**⚠️ VERIFY**: All tests above should FAIL (Red phase)

### Implementation for User Story 3

- [X] T047 [US3] Implement transaction cost calculation in BacktestEngine._calculate_trade_cost() in src/backtesting/engine.py
- [X] T048 [US3] Apply transaction costs during rebalancing in BacktestEngine._rebalance_portfolio() in src/backtesting/engine.py
- [X] T049 [US3] Update Trade dataclass to include transaction_cost field populated during execution in src/models/trade.py

**⚠️ VERIFY**: All US3 tests should now PASS (Green phase)

**Checkpoint**: All user stories (1, 2, 3) work independently - backtests now include realistic trading costs

---

## Phase 6: User Story 4 - Handle Missing Data and Market Holidays (Priority: P3)

**Goal**: Backtests handle missing price data and market holidays gracefully without failing or producing incorrect results

**Independent Test**: Provide historical data with intentional gaps (10% missing), verify backtest completes with forward-fill and logs warnings appropriately

### Tests for User Story 4 (Write FIRST, ensure they FAIL)

- [X] T050 [P] [US4] Unit test for forward-fill logic (max 5 days) in tests/unit/test_data_providers.py
- [X] T051 [P] [US4] Unit test for market holiday handling (rebalance on next business day) in tests/unit/test_rebalancer.py
- [X] T052 [P] [US4] Integration test with intentionally missing data (5% gaps) in tests/integration/test_data_providers.py
- [X] T053 [P] [US4] Integration test for backtest period including weekends and holidays in tests/integration/test_backtest_engine.py

**⚠️ VERIFY**: All tests above should FAIL (Red phase)

### Implementation for User Story 4

- [X] T054 [US4] Implement forward-fill logic in BacktestEngine._get_prices_for_date() with 5-day limit in src/backtesting/engine.py
- [X] T055 [US4] Implement business day handling using pandas BDay in src/backtesting/rebalancer.py
- [X] T056 [US4] Add logging for missing data warnings in src/backtesting/engine.py
- [X] T057 [US4] Raise DataError if forward-fill exceeds 5 days in src/backtesting/engine.py

**⚠️ VERIFY**: All US4 tests should now PASS (Green phase)

**Checkpoint**: All core user stories complete and independently functional

---

## Phase 7: Multi-Currency Support (Extended Functionality)

**Goal**: Support portfolios with assets in different currencies with automatic exchange rate conversion

**Independent Test**: Run backtest with USD and EUR assets, verify all portfolio values converted to base currency correctly

### Tests for Multi-Currency (Write FIRST, ensure they FAIL)

- [ ] T058 [P] Create test fixtures: tests/fixtures/sample_exchange_rates.csv
- [ ] T059 [P] Unit test for currency conversion logic in tests/unit/test_exchange_rates.py
- [ ] T060 [P] Integration test for multi-currency portfolio backtest in tests/integration/test_backtest_engine.py
- [ ] T061 [P] Unit test for ExchangeRateHostProvider API parsing in tests/unit/test_data_providers.py

**⚠️ VERIFY**: All tests above should FAIL (Red phase)

### Implementation for Multi-Currency

- [ ] T062 [P] Implement ExchangeRateHostProvider.fetch_rates() with API call in src/data/exchange_rates.py
- [ ] T063 [P] Implement CSVExchangeRateProvider.fetch_rates() for offline use in src/data/exchange_rates.py
- [ ] T064 [US1] Implement BacktestEngine._convert_to_base_currency() in src/backtesting/engine.py
- [ ] T065 [US1] Integrate currency conversion into _get_prices_for_date() in src/backtesting/engine.py
- [ ] T066 [US1] Update run_backtest() to accept optional exchange_rates parameter in src/backtesting/engine.py

**⚠️ VERIFY**: All multi-currency tests should now PASS (Green phase)

**Checkpoint**: Multi-currency portfolios fully supported

---

## Phase 8: CLI Interface

**Purpose**: Provide command-line interface for running backtests

### Tests for CLI (Write FIRST, ensure they FAIL)

- [ ] T067 [P] Integration test for CLI execution with sample CSV in tests/integration/test_cli.py

### Implementation for CLI

- [ ] T068 Implement CLI argument parsing (config file, strategy file, output format) in src/cli/main.py
- [ ] T069 Implement backtest execution from CLI in src/cli/main.py
- [ ] T070 Implement results display (formatted output) in src/cli/main.py
- [ ] T071 Add CLI entry point to pyproject.toml

**Checkpoint**: Users can run backtests from command line

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T072 [P] Add comprehensive docstrings to all public methods per contracts/
- [ ] T073 [P] Update README.md with installation instructions (uv sync) and quickstart example
- [ ] T074 [P] Create example CSV data files in examples/ directory
- [ ] T075 [P] Create example configuration files (sample_strategy.json) in examples/
- [ ] T076 [P] Add type hints throughout codebase
- [ ] T077 [P] Run pytest with coverage report (target: 90%+ for calculation functions)
- [ ] T078 Refactor common code patterns identified during implementation
- [ ] T079 [P] Add logging configuration with different levels (DEBUG, INFO, WARNING)
- [ ] T080 Performance profiling for 10 years × 5 assets (verify SC-001: <30 seconds)
- [ ] T081 Validate quickstart.md examples actually work
- [ ] T082 Create CHANGELOG.md documenting v1.0.0 features

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) AND User Story 1 (extends basic backtest with rebalancing)
- **User Story 3 (Phase 5)**: Depends on User Story 2 (adds costs to rebalancing)
- **User Story 4 (Phase 6)**: Depends on User Story 1 (enhances data handling)
- **Multi-Currency (Phase 7)**: Depends on User Story 1 (extends basic backtest)
- **CLI (Phase 8)**: Depends on all core user stories (US1-US4)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation only - core backtesting capability
- **User Story 2 (P2)**: Requires US1 (rebalancing builds on basic backtest)
- **User Story 3 (P3)**: Requires US2 (costs apply to rebalancing trades)
- **User Story 4 (P3)**: Independent of US2/US3 - can be done in parallel after US1

### Within Each User Story (TDD Workflow)

1. Write ALL tests for the story (marked with story label)
2. Run tests → Verify they FAIL (Red phase)
3. Implement models (can be parallel)
4. Implement core logic
5. Run tests → Verify they PASS (Green phase)
6. Refactor for clarity (maintain passing tests)
7. Story complete → move to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003, T004, T005, T006 can all run in parallel

**Phase 2 (Foundational)**:
- All data model tasks (T008-T014) can run in parallel
- T015, T016, T017, T018, T019 can run in parallel

**Within User Story 1**:
- All test fixture creation (T020-T022) in parallel
- All test writing (T023-T027) in parallel
- T028 and T029 in parallel (CSVDataProvider methods)

**Within User Story 2**:
- All test tasks (T036-T039) in parallel
- T040 can start in parallel with test writing

**Within User Story 3**:
- All test tasks (T044-T046) in parallel

**Within User Story 4**:
- All test tasks (T050-T053) in parallel

**Multi-Currency Phase**:
- T058, T059, T060, T061 (all tests) in parallel
- T062 and T063 (different providers) in parallel

**Polish Phase**:
- T072, T073, T074, T075, T076, T077, T079 can all run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all test fixtures together:
Task: "Create test fixtures: tests/fixtures/spy_2010_2020.csv"
Task: "Create test fixtures: tests/fixtures/agg_2010_2020.csv"
Task: "Create test fixtures: tests/fixtures/expected_results.json"

# Launch all unit/contract tests together:
Task: "Unit test for portfolio initialization in tests/unit/test_portfolio.py"
Task: "Unit test for performance metric calculations in tests/unit/test_metrics.py"
Task: "Contract test for SPY buy-and-hold 2010-2020 in tests/contract/test_calculation_accuracy.py"
Task: "Contract test for 60/40 SPY/AGG portfolio in tests/contract/test_calculation_accuracy.py"
Task: "Integration test for end-to-end backtest execution in tests/integration/test_backtest_engine.py"

# Launch CSVDataProvider methods together:
Task: "Implement CSVDataProvider.load_prices() in src/data/loaders.py"
Task: "Implement CSVDataProvider.validate_data() in src/data/loaders.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup with uv → `uv sync`
2. Complete Phase 2: Foundational → All data models ready
3. Complete Phase 3: User Story 1 → Basic backtesting works
4. **STOP and VALIDATE**:
   - Run pytest on US1 tests
   - Manually test with quickstart.md Example 1
   - Verify SC-001 (performance), SC-002 (accuracy)
5. Deploy/demo MVP if ready

### Incremental Delivery

1. **Phase 1+2** → Foundation ready ✓
2. **Phase 3 (US1)** → Test independently → Deploy/Demo (MVP! 🎯)
   - Users can now run basic backtests and get performance metrics
3. **Phase 4 (US2)** → Test independently → Deploy/Demo
   - Users can now configure rebalancing frequency
4. **Phase 5 (US3)** → Test independently → Deploy/Demo
   - Users can now model realistic transaction costs
5. **Phase 6 (US4)** → Test independently → Deploy/Demo
   - Backtests now handle messy real-world data
6. **Phase 7** → Multi-currency support
7. **Phase 8** → CLI for easy usage
8. **Phase 9** → Polish and documentation

### Sequential Strategy (Single Developer)

Recommended order for solo development:

1. Setup (Phase 1) - 1 day
2. Foundational (Phase 2) - 2 days
3. User Story 1 (Phase 3) - 3 days → **MVP COMPLETE**
4. User Story 2 (Phase 4) - 2 days
5. User Story 3 (Phase 5) - 1 day
6. User Story 4 (Phase 6) - 1 day
7. Multi-Currency (Phase 7) - 2 days
8. CLI (Phase 8) - 1 day
9. Polish (Phase 9) - 1 day

Total: ~14 days for full implementation

### Parallel Team Strategy

With 3 developers:

1. **All together**: Complete Setup + Foundational (Phases 1+2) - 2-3 days
2. **Once Foundational done, split**:
   - Developer A: User Story 1 (Phase 3) - 3 days
   - Developer B: Start on User Story 4 (Phase 6) in parallel - 2 days
   - Developer C: Multi-Currency (Phase 7) - 2 days
3. **After US1 complete**:
   - Developer A: User Story 2 (Phase 4) - 2 days
   - Developer B: User Story 3 (Phase 5) - 1 day
   - Developer C: CLI (Phase 8) - 1 day
4. **All together**: Polish (Phase 9) - 1 day

Total: ~8 days with parallel execution

---

## Environment Setup (uv)

### Initial Setup

```bash
# Initialize project with uv
uv init

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_portfolio.py

# Run tests with coverage
uv run pytest --cov=src --cov-report=html
```

### Development Workflow

```bash
# Add new dependency
uv add <package-name>

# Add development dependency
uv add --dev <package-name>

# Update dependencies
uv lock

# Run CLI
uv run python -m backtesting.cli.main --help
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label (US1, US2, US3, US4) maps task to specific user story
- Each user story should be independently testable
- **TDD is MANDATORY**: Write tests FIRST, verify FAIL, implement, verify PASS
- Commit after each task or logical group
- Use `uv run pytest` to run tests throughout development
- Stop at any checkpoint to validate story independently
- All calculations use `Decimal` for financial accuracy
- Performance metrics must match research.md formulas exactly
- Constitution compliance checked at each phase
- Precision requirements from data-model.md must be enforced

---

## Constitution Compliance Checkpoints

### Test-First Development ✓

- [ ] Phase 3: US1 tests written and fail before implementation
- [ ] Phase 4: US2 tests written and fail before implementation
- [ ] Phase 5: US3 tests written and fail before implementation
- [ ] Phase 6: US4 tests written and fail before implementation
- [ ] Each phase: Tests pass after implementation (Green)

### Financial Data Accuracy ✓

- [ ] T032: Formulas match research.md references (Sharpe ratio, drawdown, etc.)
- [ ] T032: Precision requirements enforced (4 decimal places for percentages, 2 for ratios)
- [ ] T025-T027: Contract tests validate against known scenarios
- [ ] T050-T053: Edge cases (missing data, holidays) handled per spec

### Simplicity ✓

- [ ] T001-T002: Start with CSV files (not database)
- [ ] T055: Use pandas BDay (not specialized calendar library)
- [ ] All complexity justified in plan.md Complexity Tracking table
- [ ] No premature optimization until SC-001 fails

---

## Success Criteria Validation

Map tasks to spec.md success criteria:

- **SC-001** (10 years × 5 assets < 30s): Validate in T080
- **SC-002** (0.01% accuracy): Validate in T025, T026 (contract tests)
- **SC-003** (Compare 3+ strategies): Enabled by T033 (run_backtest API)
- **SC-004** (95% success rate): Validated throughout integration tests
- **SC-005** (Industry-standard metrics): Validated in T032 (formula implementation)
- **SC-006** (Transaction cost impact): Validated in T045
- **SC-007** (Handle 10% missing data): Validated in T052

---

**Total Task Count**: 82 tasks
- Setup: 7 tasks
- Foundational: 12 tasks
- User Story 1: 16 tasks (8 tests + 8 implementation)
- User Story 2: 8 tasks (4 tests + 4 implementation)
- User Story 3: 6 tasks (3 tests + 3 implementation)
- User Story 4: 8 tasks (4 tests + 4 implementation)
- Multi-Currency: 9 tasks (4 tests + 5 implementation)
- CLI: 5 tasks (1 test + 4 implementation)
- Polish: 11 tasks

**Parallel Opportunities**: 45 tasks marked [P] can run in parallel within their phases

**Independent Test Criteria**: Each user story (US1-US4) has specific acceptance tests that verify functionality independently

**Suggested MVP Scope**: Phases 1 + 2 + 3 (User Story 1 only) = 35 tasks for basic backtesting capability
