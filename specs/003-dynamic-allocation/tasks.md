# Tasks: Dynamic Asset Allocation with Historical Data Analysis

**Input**: Design documents from `/specs/003-dynamic-allocation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: This feature follows Test-Driven Development (TDD) per the project constitution. All test tasks are REQUIRED before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Test structure: `tests/unit/`, `tests/integration/`, `tests/contract/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure for dynamic strategies

- [X] T001 Create src/strategies/ package directory with __init__.py
- [X] T002 Create tests/unit/strategies/ directory for strategy unit tests
- [X] T003 [P] Create tests/contract/ directory for calculation accuracy tests
- [X] T004 [P] Create tests/integration/ directory enhancements for dynamic strategy tests
- [X] T005 [P] Create tests/fixtures/ directory and add multi_asset_2015_2020.csv test data

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Foundational Models & Utilities

- [ ] T006 [P] Create CalculatedWeights model in src/models/calculated_weights.py
- [ ] T007 [P] Create StrategyParameters base class in src/models/strategy_params.py
- [ ] T008 [P] Create PriceWindow utility in src/backtesting/price_window.py
- [ ] T009 Extend AllocationStrategy to support dynamic strategies in src/models/strategy.py
- [ ] T010 [P] Create strategy utilities module src/strategies/utils.py for weight normalization
- [ ] T011 [P] Extend data validation in src/data/validation.py for lookback window checks

### Foundational Tests

- [ ] T012 [P] Write unit tests for CalculatedWeights in tests/unit/test_calculated_weights.py
- [ ] T013 [P] Write unit tests for StrategyParameters in tests/unit/test_strategy_params.py
- [ ] T014 [P] Write unit tests for PriceWindow in tests/unit/test_price_window.py
- [ ] T015 [P] Write unit tests for strategy utilities in tests/unit/test_strategy_utils.py

### BacktestEngine Integration Support

- [ ] T016 Extend BacktestEngine to detect and call calculate_weights() in src/backtesting/engine.py
- [ ] T017 Write integration test for BacktestEngine dynamic strategy detection in tests/integration/test_dynamic_backtest.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Momentum-Based Dynamic Allocation (Priority: P1) 🎯 MVP

**Goal**: Implement momentum strategy that calculates weights based on historical returns over lookback period, with support for excluding negative momentum assets and allocating to cash when all assets decline.

**Independent Test**: Run backtest with historical price data spanning 12 months, configure 120-day lookback, verify weights change over time based on relative performance, and that all-negative returns scenario allocates 100% to cash.

### Tests for User Story 1 (TDD - Write First, Verify They Fail)

- [ ] T018 [P] [US1] Write contract test for momentum calculation accuracy in tests/contract/test_momentum_accuracy.py
- [ ] T019 [P] [US1] Write unit test for MomentumParameters validation in tests/unit/strategies/test_momentum_params.py
- [ ] T020 [P] [US1] Write unit tests for momentum score calculation in tests/unit/strategies/test_momentum.py (Test Cases 1-5 from contract)
- [ ] T021 [P] [US1] Write integration test for momentum strategy with BacktestEngine in tests/integration/test_momentum_integration.py

### Implementation for User Story 1

- [ ] T022 [P] [US1] Create MomentumParameters class in src/models/strategy_params.py
- [ ] T023 [US1] Create DynamicAllocationStrategy base class in src/strategies/base.py
- [ ] T024 [US1] Implement MomentumStrategy.calculate_weights() in src/strategies/momentum.py
- [ ] T025 [US1] Implement momentum score calculation logic in src/strategies/momentum.py
- [ ] T026 [US1] Implement negative momentum filtering in src/strategies/momentum.py
- [ ] T027 [US1] Implement all-negative-returns cash allocation in src/strategies/momentum.py
- [ ] T028 [US1] Add insufficient data handling (use previous weights) in src/strategies/momentum.py
- [ ] T029 [US1] Add missing data handling (exclude assets) in src/strategies/momentum.py
- [ ] T030 [US1] Verify all Unit Story 1 tests pass (run tests/unit/strategies/test_momentum*.py)
- [ ] T031 [US1] Verify momentum contract test passes (run tests/contract/test_momentum_accuracy.py)
- [ ] T032 [US1] Verify momentum integration test passes (run tests/integration/test_momentum_integration.py)

**Checkpoint**: At this point, Momentum Strategy (User Story 1) should be fully functional and testable independently. MVP complete!

---

## Phase 4: User Story 4 - Strategy Parameter Configuration (Priority: P1)

**Goal**: Enable users to configure strategy parameters (lookback periods, risk targets, MA windows) with validation, and ensure parameters are applied consistently throughout backtests with clear parameter tracking in results.

**Independent Test**: Run same strategy with different parameter values (60-day vs 120-day lookback), verify allocations differ appropriately, and confirm parameter snapshot is recorded in CalculatedWeights.

### Tests for User Story 4 (TDD - Write First, Verify They Fail)

- [ ] T033 [P] [US4] Write unit tests for parameter validation (negative lookback, duplicate assets) in tests/unit/test_strategy_params.py
- [ ] T034 [P] [US4] Write integration test for parameter changes producing different results in tests/integration/test_parameter_changes.py
- [ ] T035 [P] [US4] Write test for invalid parameter rejection in tests/unit/strategies/test_momentum_params.py

### Implementation for User Story 4

- [ ] T036 [P] [US4] Implement StrategyParameters.validate() method in src/models/strategy_params.py
- [ ] T037 [P] [US4] Implement MomentumParameters.validate() with lookback range checks in src/models/strategy_params.py
- [ ] T038 [US4] Add parameter validation call in strategy __init__ methods in src/strategies/base.py
- [ ] T039 [US4] Ensure CalculatedWeights captures parameters_snapshot in src/models/calculated_weights.py
- [ ] T040 [US4] Add parameter validation warnings for lookback < 30 or > 252 days in src/models/strategy_params.py
- [ ] T041 [US4] Verify all User Story 4 tests pass (run tests/unit/test_strategy_params.py and tests/integration/test_parameter_changes.py)

**Checkpoint**: At this point, User Stories 1 AND 4 should both work independently. Users can configure and validate momentum strategy parameters.

---

## Phase 5: User Story 2 - Volatility-Based Risk Adjustment (Priority: P2)

**Goal**: Implement risk parity strategy that allocates inversely proportional to volatility, excludes zero-volatility assets, and optionally applies leverage to target portfolio volatility.

**Independent Test**: Run backtests with assets showing different volatility profiles, verify strategy allocates smaller weights to high-volatility assets, and demonstrate reduced portfolio volatility compared to equal-weight strategies.

### Tests for User Story 2 (TDD - Write First, Verify They Fail)

- [ ] T042 [P] [US2] Write contract test for volatility calculation accuracy in tests/contract/test_risk_parity_accuracy.py
- [ ] T043 [P] [US2] Write unit test for RiskParityParameters validation in tests/unit/strategies/test_risk_parity_params.py
- [ ] T044 [P] [US2] Write unit tests for volatility calculation and inverse weighting in tests/unit/strategies/test_risk_parity.py
- [ ] T045 [P] [US2] Write unit test for zero-volatility exclusion in tests/unit/strategies/test_risk_parity.py
- [ ] T046 [P] [US2] Write integration test for risk parity strategy with BacktestEngine in tests/integration/test_risk_parity_integration.py

### Implementation for User Story 2

- [ ] T047 [P] [US2] Create RiskParityParameters class in src/models/strategy_params.py
- [ ] T048 [US2] Implement RiskParityStrategy.calculate_weights() in src/strategies/risk_parity.py
- [ ] T049 [US2] Implement volatility calculation (annualized std dev) in src/strategies/risk_parity.py
- [ ] T050 [US2] Implement inverse volatility weighting in src/strategies/risk_parity.py
- [ ] T051 [US2] Implement zero/near-zero volatility exclusion in src/strategies/risk_parity.py
- [ ] T052 [US2] Implement optional risk target adjustment (leverage) in src/strategies/risk_parity.py
- [ ] T053 [US2] Add insufficient data handling (use previous weights) in src/strategies/risk_parity.py
- [ ] T054 [US2] Add missing data handling (exclude assets) in src/strategies/risk_parity.py
- [ ] T055 [US2] Verify all User Story 2 tests pass (run tests/unit/strategies/test_risk_parity*.py)
- [ ] T056 [US2] Verify risk parity contract test passes (run tests/contract/test_risk_parity_accuracy.py)
- [ ] T057 [US2] Verify risk parity integration test passes (run tests/integration/test_risk_parity_integration.py)

**Checkpoint**: At this point, User Stories 1, 2, AND 4 should all work independently. Risk parity strategy is fully functional.

---

## Phase 6: User Story 3 - Dual Moving Average Strategy (Priority: P3)

**Goal**: Implement dual moving average strategy using short/long-term trend signals, with binary signal weighting (MVP) and support for all-downtrend cash allocation.

**Independent Test**: Provide historical data with clear trend reversals, configure 50/200-day MA periods, verify strategy increases weight when short MA crosses above long MA, and decreases when it crosses below.

### Tests for User Story 3 (TDD - Write First, Verify They Fail)

- [ ] T058 [P] [US3] Write contract test for moving average calculation accuracy in tests/contract/test_dual_ma_accuracy.py
- [ ] T059 [P] [US3] Write unit test for DualMomentumParameters validation in tests/unit/strategies/test_dual_momentum_params.py
- [ ] T060 [P] [US3] Write unit tests for MA calculation and trend signals in tests/unit/strategies/test_dual_momentum.py
- [ ] T061 [P] [US3] Write unit test for all-downtrend cash allocation in tests/unit/strategies/test_dual_momentum.py
- [ ] T062 [P] [US3] Write integration test for dual MA strategy with BacktestEngine in tests/integration/test_dual_ma_integration.py

### Implementation for User Story 3

- [ ] T063 [P] [US3] Create DualMomentumParameters class in src/models/strategy_params.py
- [ ] T064 [US3] Implement DualMomentumStrategy.calculate_weights() in src/strategies/dual_momentum.py
- [ ] T065 [US3] Implement short/long moving average calculation in src/strategies/dual_momentum.py
- [ ] T066 [US3] Implement binary trend signal generation in src/strategies/dual_momentum.py
- [ ] T067 [US3] Implement binary signal weighting (equal weight to positive signals) in src/strategies/dual_momentum.py
- [ ] T068 [US3] Implement all-downtrend cash allocation in src/strategies/dual_momentum.py
- [ ] T069 [US3] Add insufficient data handling (use previous weights) in src/strategies/dual_momentum.py
- [ ] T070 [US3] Validate short_window < long_window in DualMomentumParameters in src/models/strategy_params.py
- [ ] T071 [US3] Verify all User Story 3 tests pass (run tests/unit/strategies/test_dual_momentum*.py)
- [ ] T072 [US3] Verify dual MA contract test passes (run tests/contract/test_dual_ma_accuracy.py)
- [ ] T073 [US3] Verify dual MA integration test passes (run tests/integration/test_dual_ma_integration.py)

**Checkpoint**: All user stories (1, 2, 3, 4) should now be independently functional. All three strategy types implemented!

---

## Phase 7: Strategy Comparison & Optimization

**Goal**: Enable users to compare static vs dynamic strategies and run parameter optimization with multiple combinations.

**Tests for Strategy Comparison**

- [ ] T074 [P] Write integration test comparing static 60/40 vs dynamic momentum in tests/integration/test_strategy_comparison.py
- [ ] T075 [P] Write integration test for multi-strategy comparison in tests/integration/test_strategy_comparison.py
- [ ] T076 [P] Write performance test for parameter optimization (50 combinations in <30 min) in tests/integration/test_parameter_optimization.py

**Implementation for Strategy Comparison**

- [ ] T077 Verify BacktestEngine produces comparable results for static and dynamic strategies in tests/integration/test_strategy_comparison.py
- [ ] T078 Ensure PerformanceMetrics includes strategy parameter information in src/models/performance.py
- [ ] T079 Add parameter grid search utility example to quickstart.md
- [ ] T080 Run all strategy comparison tests and verify performance targets met

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [ ] T081 [P] Add docstrings to all strategy classes following numpy style in src/strategies/
- [ ] T082 [P] Add logging for weight calculation events in src/strategies/base.py
- [ ] T083 [P] Add calculation metadata to CalculatedWeights for debugging in src/models/calculated_weights.py
- [ ] T084 [P] Review and optimize pandas operations for performance in src/strategies/utils.py
- [ ] T085 Run full test suite and verify 95%+ coverage for strategy code
- [ ] T086 Create comprehensive example scripts based on quickstart.md in examples/
- [ ] T087 [P] Update CLAUDE.md with dynamic strategy usage patterns
- [ ] T088 Run end-to-end backtest scenarios from quickstart.md and verify results
- [ ] T089 Code review: Verify constitution compliance (TDD, financial accuracy, simplicity)
- [ ] T090 Performance validation: Verify weight calc <100ms, backtest ≤2x static time

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1 - Momentum): Can start after Foundational
  - User Story 4 (P1 - Parameters): Can start after Foundational
  - User Story 2 (P2 - Risk Parity): Can start after Foundational
  - User Story 3 (P3 - Dual MA): Can start after Foundational
- **Strategy Comparison (Phase 7)**: Depends on at least User Story 1 (momentum) completion
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - Momentum)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P1 - Parameters)**: Can start after Foundational (Phase 2) - Enhances all strategies but can be implemented with US1
- **User Story 2 (P2 - Risk Parity)**: Can start after Foundational (Phase 2) - Independently testable
- **User Story 3 (P3 - Dual MA)**: Can start after Foundational (Phase 2) - Independently testable

### Within Each User Story (TDD Workflow)

1. **Write Tests FIRST** (all test tasks for the story)
2. **Verify tests FAIL** (Red phase)
3. **Implement models** (parallel where possible)
4. **Implement strategy calculate_weights()** (Green phase)
5. **Add edge case handling**
6. **Verify all tests PASS**
7. **Refactor if needed** (Refactor phase with test safety net)

### Parallel Opportunities

**Phase 1 (Setup)**: All 5 tasks can run in parallel

**Phase 2 (Foundational)**:
- Models (T006-T007) in parallel
- Utilities (T008, T010-T011) in parallel
- Tests (T012-T015) in parallel
- T016-T017 after models complete

**Phase 3 (US1 - Momentum)**:
- All test tasks (T018-T021) in parallel
- Models (T022) and base class (T023) in parallel
- Implementation tasks (T024-T029) must be sequential (same file)

**Phase 4 (US4 - Parameters)**:
- All test tasks (T033-T035) in parallel
- Implementation tasks (T036-T037) in parallel

**Phase 5 (US2 - Risk Parity)**:
- All test tasks (T042-T046) in parallel
- Model (T047) and implementation (T048-T054) sequential

**Phase 6 (US3 - Dual MA)**:
- All test tasks (T058-T062) in parallel
- Model (T063) and implementation (T064-T070) sequential

**Phase 7 (Comparison)**:
- All test tasks (T074-T076) in parallel

**Phase 8 (Polish)**:
- Documentation tasks (T081, T087) in parallel
- Logging/metadata tasks (T082-T083) in parallel

---

## Parallel Example: User Story 1 (Momentum Strategy)

```bash
# Phase 1: Write all tests in parallel (TDD Red phase)
Parallel Task Group 1 (Tests):
- T018: "Write contract test for momentum calculation accuracy"
- T019: "Write unit test for MomentumParameters validation"
- T020: "Write unit tests for momentum score calculation"
- T021: "Write integration test for momentum strategy with BacktestEngine"

# Phase 2: Implement models in parallel
Parallel Task Group 2 (Models):
- T022: "Create MomentumParameters class"
- T023: "Create DynamicAllocationStrategy base class"

# Phase 3: Implement strategy (sequential, same file)
Sequential Task Group:
- T024 → T025 → T026 → T027 → T028 → T029 (all in src/strategies/momentum.py)

# Phase 4: Verify tests pass (TDD Green phase)
Sequential Task Group:
- T030 → T031 → T032 (run tests, fix until all pass)
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 4 Only)

**Minimum Viable Product Scope**:
1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T017) - CRITICAL BLOCKER
3. Complete Phase 3: User Story 1 - Momentum Strategy (T018-T032)
4. Complete Phase 4: User Story 4 - Parameter Configuration (T033-T041)
5. **STOP and VALIDATE**:
   - Run full test suite for US1 and US4
   - Execute example from quickstart.md
   - Verify momentum strategy produces different results with different parameters
6. **MVP COMPLETE**: Users can run momentum-based backtests with configurable parameters

### Incremental Delivery

**Release 1: MVP (Momentum + Parameters)**
- Setup + Foundational → Foundation ready
- User Story 1 + User Story 4 → Test independently → Deploy/Demo
- **Value**: Users can run dynamic momentum strategies with parameter optimization

**Release 2: Add Risk Management (Risk Parity)**
- User Story 2 → Test independently → Deploy/Demo
- **Value**: Users can compare momentum vs risk-adjusted allocation

**Release 3: Add Trend Following (Dual MA)**
- User Story 3 → Test independently → Deploy/Demo
- **Value**: Complete strategy suite with three complementary approaches

**Release 4: Production Ready**
- Phase 7: Strategy Comparison → Test independently → Deploy/Demo
- Phase 8: Polish & Cross-Cutting Concerns
- **Value**: Production-ready with comprehensive testing and documentation

### Parallel Team Strategy

With multiple developers:

**Stage 1: Foundation (Week 1)**
- Entire team: Complete Setup (Phase 1) + Foundational (Phase 2) together
- **Blocker resolved**: Foundation complete, user stories can now proceed

**Stage 2: MVP Development (Week 2)**
- Developer A: User Story 1 (Momentum - T018-T032)
- Developer B: User Story 4 (Parameters - T033-T041)
- Stories complete and integrate independently

**Stage 3: Additional Strategies (Weeks 3-4)**
- Developer A: User Story 2 (Risk Parity - T042-T057)
- Developer B: User Story 3 (Dual MA - T058-T073)
- Developer C: Phase 7 (Strategy Comparison - T074-T080)

**Stage 4: Polish (Week 5)**
- Team: Phase 8 (Polish - T081-T090)
- Final validation and deployment

---

## Test-Driven Development Workflow

Per project constitution, this feature MUST follow TDD:

### Red Phase (Tests First)
For each user story:
1. Write all test tasks marked for that story
2. Run tests and **verify they FAIL**
3. Document expected failures

### Green Phase (Implementation)
For each user story:
1. Implement minimum code to make tests pass
2. Run tests frequently during implementation
3. Stop when all tests pass

### Refactor Phase (Improve Code)
For each user story:
1. Review implementation for clarity and simplicity
2. Refactor with tests as safety net
3. Ensure tests still pass after refactoring

### Example for User Story 1 (Momentum):

```bash
# Red Phase
Run: pytest tests/contract/test_momentum_accuracy.py tests/unit/strategies/test_momentum.py
Expected: All tests FAIL (implementation doesn't exist yet)

# Green Phase (iterate until passing)
Implement: src/strategies/momentum.py
Run: pytest tests/contract/test_momentum_accuracy.py tests/unit/strategies/test_momentum.py
Iterate: Fix failing tests one by one

# Refactor Phase
Review: src/strategies/momentum.py for simplicity
Refactor: Extract common logic to utils, improve naming
Run: pytest tests/contract/test_momentum_accuracy.py tests/unit/strategies/test_momentum.py
Verify: All tests still pass after refactoring
```

---

## Notes

- **[P] tasks** = different files, no dependencies - can run in parallel
- **[Story] label** maps task to specific user story for traceability
- **TDD Required**: Per constitution, tests MUST be written and verified to FAIL before implementation
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All financial calculations must maintain Decimal precision (4 decimal places for weights)
- Performance targets: <100ms weight calc, ≤2x backtest time, <30min for 50 parameter combinations

---

## Task Summary

**Total Tasks**: 90
- Phase 1 (Setup): 5 tasks
- Phase 2 (Foundational): 12 tasks
- Phase 3 (User Story 1 - Momentum): 15 tasks
- Phase 4 (User Story 4 - Parameters): 9 tasks
- Phase 5 (User Story 2 - Risk Parity): 16 tasks
- Phase 6 (User Story 3 - Dual MA): 16 tasks
- Phase 7 (Strategy Comparison): 7 tasks
- Phase 8 (Polish): 10 tasks

**MVP Scope** (Recommended first release):
- Phases 1, 2, 3, 4 = 41 tasks
- Estimated: ~2-3 weeks for single developer
- Delivers: Momentum strategy with parameter configuration

**Full Feature** (All user stories):
- All 90 tasks
- Estimated: ~4-6 weeks for single developer
- Delivers: Complete dynamic allocation suite with 3 strategies

**Parallel Opportunities Identified**: 47 tasks marked [P] can run in parallel within their phases

**Independent Test Criteria**:
- **US1**: Run backtest with momentum strategy, verify weights change based on returns
- **US2**: Run backtest with risk parity, verify lower weights to high-volatility assets
- **US3**: Run backtest with dual MA, verify weights respond to MA crossovers
- **US4**: Run same strategy with different parameters, verify different allocations
