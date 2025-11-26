# Implementation Tasks: Brokerage Account Integration

**Feature**: 002-account-integration | **Date**: 2025-11-24 | **Branch**: `002-account-integration`

## Overview

This document contains the complete implementation tasks for the Brokerage Account Integration feature, organized by user story to enable independent implementation and testing following Test-Driven Development (TDD) principles.

### User Stories Summary

| ID | Story | Priority | Status |
|----|-------|----------|--------|
| US1 | View Current Portfolio Holdings | P1 | Not Started |
| US2 | Authenticate with Brokerage Account | P1 | Not Started |
| US3 | Handle Multiple Brokerage Accounts | P2 | Not Started |
| US4 | Send Portfolio Status to Slack | P2 | Not Started |
| US5 | Automatic Periodic Data Refresh | P3 | Not Started |

### Implementation Strategy

**MVP Scope**: US1 + US2 (P1 stories) - These provide core value: authentication and holdings retrieval
**Incremental Delivery**: Each user story is independently testable and deliverable
**TDD Approach**: Tests written before implementation for all tasks

---

## Phase 1: Setup & Project Initialization

**Goal**: Prepare project structure and install dependencies

### Tasks

- [X] T001 Add new dependencies to pyproject.toml (cryptography>=41.0, pydantic>=2.0, PyYAML>=6.0, tenacity>=8.2)
- [X] T002 Run `uv sync` to install new dependencies
- [X] T003 Create src/account/ module directory structure
- [X] T004 Create src/account/__init__.py
- [X] T005 Create src/account/providers/ subdirectory
- [X] T006 Create src/account/providers/__init__.py
- [X] T007 Create src/notifications/ module directory
- [X] T008 Create src/notifications/__init__.py
- [X] T009 Create config/ directory for configuration files
- [X] T010 Add config/ to .gitignore to prevent credential leakage
- [X] T011 Create tests/unit/account/ directory
- [X] T012 Create tests/unit/notifications/ directory
- [X] T013 Create tests/integration/ directory (if not exists)
- [X] T014 Create tests/contract/ directory
- [X] T015 Create tests/fixtures/ directory
- [X] T016 Create config/config.sample.yaml from research.md structure

**Success Criteria**: Project structure matches plan.md, all directories created, dependencies installed

---

## Phase 2: Foundational Components

**Goal**: Build shared infrastructure needed by all user stories (TDD)

### Configuration & Encryption Foundation

**Tests First**:

- [ ] T017 [P] Write unit test for Fernet encryption/decryption in tests/unit/account/test_crypto.py
- [ ] T018 [P] Write unit test for PBKDF2 key derivation in tests/unit/account/test_crypto.py
- [ ] T019 [P] Write unit test for configuration parsing with pydantic in tests/unit/account/test_config.py
- [ ] T020 [P] Write unit test for encrypted credential loading in tests/unit/account/test_config.py

**Implementation**:

- [ ] T021 Implement crypto utilities in src/account/crypto.py (encrypt, decrypt, derive_key)
- [ ] T022 Implement AccountCredentials pydantic model in src/account/config.py
- [ ] T023 Implement BrokerageAccountConfig pydantic model in src/account/config.py
- [ ] T024 Implement SlackConfig pydantic model in src/account/config.py
- [ ] T025 Implement RefreshConfig pydantic model in src/account/config.py
- [ ] T026 Implement root Config pydantic model in src/account/config.py
- [ ] T027 Implement load_config() function in src/account/config.py
- [ ] T028 Implement decrypt_credentials() function in src/account/config.py

**Verification**:

- [ ] T029 Run `pytest tests/unit/account/test_crypto.py -v` (all tests pass)
- [ ] T030 Run `pytest tests/unit/account/test_config.py -v` (all tests pass)

### Core Data Models

**Tests First**:

- [ ] T031 [P] Write unit test for BrokerageAccount entity in tests/unit/account/test_models.py
- [ ] T032 [P] Write unit test for AccountHoldings entity in tests/unit/account/test_models.py
- [ ] T033 [P] Write unit test for SecurityPosition entity in tests/unit/account/test_models.py
- [ ] T034 [P] Write unit test for AccountHoldings.to_portfolio_state() conversion in tests/unit/account/test_models.py

**Implementation**:

- [ ] T035 Implement AccountStatus enum in src/account/models.py
- [ ] T036 Implement AssetType enum in src/account/models.py
- [ ] T037 Implement BrokerageAccount dataclass in src/account/models.py
- [ ] T038 Implement SecurityPosition dataclass in src/account/models.py
- [ ] T039 Implement AccountHoldings dataclass in src/account/models.py
- [ ] T040 Implement AccountHoldings.to_portfolio_state() method in src/account/models.py

**Verification**:

- [ ] T041 Run `pytest tests/unit/account/test_models.py -v` (all tests pass)

### Provider Interface

**Tests First**:

- [ ] T042 [P] Write unit test for AccountProvider abstract interface in tests/unit/account/providers/test_base.py

**Implementation**:

- [ ] T043 Implement AccountProvider ABC in src/account/providers/base.py
- [ ] T044 Implement BrokerageProvider dataclass in src/account/providers/base.py

**Verification**:

- [ ] T045 Run `pytest tests/unit/account/providers/test_base.py -v` (all tests pass)

### Rate Limiting & Retry

**Tests First**:

- [ ] T046 [P] Write unit test for RateLimiter in tests/unit/account/test_rate_limiter.py
- [ ] T047 [P] Write unit test for exponential backoff retry with tenacity in tests/unit/account/test_client.py

**Implementation**:

- [ ] T048 Implement RateLimiter class in src/account/rate_limiter.py
- [ ] T049 Implement retry decorators using tenacity in src/account/client.py

**Verification**:

- [ ] T050 Run `pytest tests/unit/account/test_rate_limiter.py -v` (all tests pass)

**Success Criteria**: All foundational tests pass, infrastructure ready for user story implementation

---

## Phase 3: US1+US2 (P1) - Authentication & Holdings Retrieval

**User Stories**: US2 (Authenticate) + US1 (View Holdings) - implemented together as tightly coupled

**Goal**: Enable users to authenticate with Korea Investment & Securities and retrieve current portfolio holdings

**Independent Test Criteria**:
- Can authenticate with valid credentials and get access token
- Can fetch holdings data with authenticated session
- Can convert holdings to PortfolioState format
- Can display cash balance and security positions
- Handles authentication failures gracefully
- Handles API errors with retry logic

### US2: Authentication Module

**Tests First**:

- [ ] T051 [P] [US2] Write unit test for authentication success in tests/unit/account/test_auth.py
- [ ] T052 [P] [US2] Write unit test for authentication failure (invalid credentials) in tests/unit/account/test_auth.py
- [ ] T053 [P] [US2] Write unit test for token expiry check in tests/unit/account/test_auth.py
- [ ] T054 [P] [US2] Write unit test for automatic re-authentication in tests/unit/account/test_auth.py

**Implementation**:

- [ ] T055 [US2] Implement authenticate() function in src/account/auth.py
- [ ] T056 [US2] Implement check_token_expiry() function in src/account/auth.py
- [ ] T057 [US2] Implement refresh_token() function in src/account/auth.py
- [ ] T058 [US2] Implement AccountAuthException in src/account/exceptions.py

**Contract Tests**:

- [ ] T059 [P] [US2] Write contract test for /oauth2/tokenP endpoint in tests/contract/test_korea_investment_auth.py
- [ ] T060 [US2] Verify contract test passes with mock responses

**Verification**:

- [ ] T061 [US2] Run `pytest tests/unit/account/test_auth.py -v` (all tests pass)
- [ ] T062 [US2] Run `pytest tests/contract/test_korea_investment_auth.py -v` (all tests pass)

### US1: Korea Investment Provider Implementation

**Tests First**:

- [ ] T063 [P] [US1] Write unit test for KoreaInvestmentProvider.authenticate() in tests/unit/account/providers/test_korea_investment.py
- [ ] T064 [P] [US1] Write unit test for KoreaInvestmentProvider.fetch_holdings() in tests/unit/account/providers/test_korea_investment.py
- [ ] T065 [P] [US1] Write unit test for API response parsing in tests/unit/account/providers/test_korea_investment.py
- [ ] T066 [P] [US1] Write unit test for error handling (network timeout, 500 error) in tests/unit/account/providers/test_korea_investment.py
- [ ] T067 [P] [US1] Write unit test for rate limiting integration in tests/unit/account/providers/test_korea_investment.py

**Implementation**:

- [ ] T068 [US1] Implement KoreaInvestmentProvider class in src/account/providers/korea_investment.py
- [ ] T069 [US1] Implement authenticate() method with OAuth2 flow in src/account/providers/korea_investment.py
- [ ] T070 [US1] Implement fetch_holdings() method in src/account/providers/korea_investment.py
- [ ] T071 [US1] Implement _parse_holdings_response() helper in src/account/providers/korea_investment.py
- [ ] T072 [US1] Implement _make_request() with rate limiting and retry in src/account/providers/korea_investment.py
- [ ] T073 [US1] Add KOREA_INVESTMENT provider constant in src/account/providers/base.py

**Contract Tests**:

- [ ] T074 [P] [US1] Write contract test for /uapi/domestic-stock/v1/trading/inquire-balance endpoint in tests/contract/test_korea_investment_holdings.py
- [ ] T075 [US1] Verify contract test passes with mock responses

**Verification**:

- [ ] T076 [US1] Run `pytest tests/unit/account/providers/test_korea_investment.py -v` (all tests pass)
- [ ] T077 [US1] Run `pytest tests/contract/test_korea_investment_holdings.py -v` (all tests pass)

### US1: API Client & Service Layer

**Tests First**:

- [ ] T078 [P] [US1] Write unit test for AccountService.get_holdings() in tests/unit/account/test_service.py
- [ ] T079 [P] [US1] Write unit test for incomplete data handling (missing prices) in tests/unit/account/test_service.py
- [ ] T080 [P] [US1] Write unit test for non-standard asset handling in tests/unit/account/test_service.py

**Implementation**:

- [ ] T081 [US1] Implement AccountService class in src/account/service.py
- [ ] T082 [US1] Implement get_holdings() method in src/account/service.py
- [ ] T083 [US1] Implement _validate_holdings() helper in src/account/service.py
- [ ] T084 [US1] Implement _detect_warnings() for incomplete data in src/account/service.py

**Verification**:

- [ ] T085 [US1] Run `pytest tests/unit/account/test_service.py -v` (all tests pass)

### US1+US2: Integration Tests

**Tests First**:

- [ ] T086 [P] [US1] Write integration test for end-to-end authentication + holdings fetch in tests/integration/test_account_integration.py
- [ ] T087 [P] [US1] Write integration test for token refresh on expiry in tests/integration/test_account_integration.py
- [ ] T088 [P] [US1] Write integration test for retry on transient failure in tests/integration/test_account_integration.py

**Verification**:

- [ ] T089 [US1] Run `pytest tests/integration/test_account_integration.py -v` (all tests pass)

### US1+US2: CLI Interface

**Tests First**:

- [ ] T090 [P] [US1] Write unit test for CLI fetch command in tests/unit/account/test_cli.py
- [ ] T091 [P] [US1] Write unit test for CLI status command in tests/unit/account/test_cli.py

**Implementation**:

- [ ] T092 [US1] Implement CLI module entry point in src/account/cli.py
- [ ] T093 [US1] Implement fetch command in src/account/cli.py
- [ ] T094 [US1] Implement status command in src/account/cli.py
- [ ] T095 [US1] Implement display_holdings() formatter in src/account/cli.py

**Verification**:

- [ ] T096 [US1] Run `pytest tests/unit/account/test_cli.py -v` (all tests pass)
- [ ] T097 [US1] Manual test: `python -m src.account.cli fetch --mock` (displays mock holdings)

### US1+US2: Fixtures & Mock Data

**Implementation**:

- [ ] T098 [P] [US1] Create mock API response fixtures in tests/fixtures/mock_korea_investment_responses.json
- [ ] T099 [P] [US1] Create sample portfolio fixtures in tests/fixtures/mock_portfolios.py

### US1+US2: Utilities

**Implementation**:

- [ ] T100 [US1] Implement encryption key generator in src/account/keygen.py
- [ ] T101 [US1] Implement config encryption utility in src/account/encrypt_config.py
- [ ] T102 [US1] Implement config verification utility in src/account/verify_config.py

**Phase 3 Success Criteria**:
✅ All US1+US2 tests pass
✅ Can authenticate with Korea Investment & Securities (mocked)
✅ Can fetch holdings and display (mocked)
✅ Can convert to PortfolioState
✅ Warning indicators work for incomplete data
✅ Retry logic functions correctly
✅ Rate limiting respects 1 req/sec limit

---

## Phase 4: US3 (P2) - Multiple Brokerage Accounts

**Goal**: Support multiple brokerage accounts with separate/consolidated views

**Independent Test Criteria**:
- Can configure multiple accounts in config.yaml
- Can fetch holdings from each account independently
- Can display individual account views
- Can display consolidated view across accounts
- Handles partial failures (one account down, others work)

### US3: Multi-Account Support

**Tests First**:

- [ ] T103 [P] [US3] Write unit test for multiple account configuration parsing in tests/unit/account/test_config.py
- [ ] T104 [P] [US3] Write unit test for AccountService.get_all_holdings() in tests/unit/account/test_service.py
- [ ] T105 [P] [US3] Write unit test for consolidated view generation in tests/unit/account/test_service.py
- [ ] T106 [P] [US3] Write unit test for partial failure handling in tests/unit/account/test_service.py

**Implementation**:

- [ ] T107 [US3] Implement get_all_holdings() in src/account/service.py
- [ ] T108 [US3] Implement consolidate_holdings() in src/account/service.py
- [ ] T109 [US3] Add --all flag to CLI fetch command in src/account/cli.py
- [ ] T110 [US3] Add --consolidated flag to CLI fetch command in src/account/cli.py
- [ ] T111 [US3] Implement display_consolidated_holdings() in src/account/cli.py

**Verification**:

- [ ] T112 [US3] Run `pytest tests/unit/account/test_config.py::test_multiple_accounts -v` (passes)
- [ ] T113 [US3] Run `pytest tests/unit/account/test_service.py::test_multi_account -v` (passes)

**Integration Tests**:

- [ ] T114 [P] [US3] Write integration test for fetching from multiple accounts in tests/integration/test_multi_account.py
- [ ] T115 [P] [US3] Write integration test for partial failure scenario in tests/integration/test_multi_account.py

**Verification**:

- [ ] T116 [US3] Run `pytest tests/integration/test_multi_account.py -v` (all tests pass)
- [ ] T117 [US3] Manual test: Configure 2 accounts, run `python -m src.account.cli fetch --all --mock`

**Phase 4 Success Criteria**:
✅ All US3 tests pass
✅ Can configure and fetch from multiple accounts
✅ Consolidated view combines holdings correctly
✅ Partial failures handled gracefully

---

## Phase 5: US4 (P2) - Slack Notifications

**Goal**: Send portfolio status updates to Slack

**Independent Test Criteria**:
- Can send formatted message to Slack webhook
- Message includes all essential portfolio info
- Warnings are highlighted in Slack message
- Slack failures don't block main operations
- Handles message size limits (truncation)

### US4: Slack Integration

**Tests First**:

- [ ] T118 [P] [US4] Write unit test for SlackNotification entity in tests/unit/notifications/test_models.py
- [ ] T119 [P] [US4] Write unit test for Slack message formatter in tests/unit/notifications/test_formatters.py
- [ ] T120 [P] [US4] Write unit test for Block Kit block generation in tests/unit/notifications/test_formatters.py
- [ ] T121 [P] [US4] Write unit test for message truncation (large portfolios) in tests/unit/notifications/test_formatters.py
- [ ] T122 [P] [US4] Write unit test for warning highlighting in tests/unit/notifications/test_formatters.py

**Implementation**:

- [ ] T123 [US4] Implement NotificationStatus enum in src/notifications/models.py
- [ ] T124 [US4] Implement NotificationTrigger enum in src/notifications/models.py
- [ ] T125 [US4] Implement SlackNotification dataclass in src/notifications/models.py
- [ ] T126 [US4] Implement PortfolioFormatter class in src/notifications/formatters.py
- [ ] T127 [US4] Implement format_detailed() method in src/notifications/formatters.py
- [ ] T128 [US4] Implement format_summary() method in src/notifications/formatters.py
- [ ] T129 [US4] Implement _truncate_holdings() helper in src/notifications/formatters.py

**Verification**:

- [ ] T130 [US4] Run `pytest tests/unit/notifications/test_models.py -v` (all tests pass)
- [ ] T131 [US4] Run `pytest tests/unit/notifications/test_formatters.py -v` (all tests pass)

### US4: Slack Client

**Tests First**:

- [ ] T132 [P] [US4] Write unit test for SlackClient.send() in tests/unit/notifications/test_slack.py
- [ ] T133 [P] [US4] Write unit test for webhook validation in tests/unit/notifications/test_slack.py
- [ ] T134 [P] [US4] Write unit test for error handling (timeout, 403, 500) in tests/unit/notifications/test_slack.py
- [ ] T135 [P] [US4] Write unit test for graceful degradation (don't block on failure) in tests/unit/notifications/test_slack.py

**Implementation**:

- [ ] T136 [US4] Implement SlackClient class in src/notifications/slack.py
- [ ] T137 [US4] Implement send() method with timeout in src/notifications/slack.py
- [ ] T138 [US4] Implement validate_webhook_url() in src/notifications/slack.py
- [ ] T139 [US4] Implement _handle_error() with logging in src/notifications/slack.py

**Contract Tests**:

- [ ] T140 [P] [US4] Write contract test for Slack webhook POST in tests/contract/test_slack_webhook.py

**Verification**:

- [ ] T141 [US4] Run `pytest tests/unit/notifications/test_slack.py -v` (all tests pass)
- [ ] T142 [US4] Run `pytest tests/contract/test_slack_webhook.py -v` (all tests pass)

### US4: Integration with Account Fetching

**Tests First**:

- [ ] T143 [P] [US4] Write integration test for fetch + Slack notification in tests/integration/test_slack_integration.py
- [ ] T144 [P] [US4] Write integration test for Slack failure doesn't block fetch in tests/integration/test_slack_integration.py

**Implementation**:

- [ ] T145 [US4] Integrate SlackClient into AccountService.get_holdings() in src/account/service.py
- [ ] T146 [US4] Add --no-slack flag to CLI in src/account/cli.py
- [ ] T147 [US4] Implement test-slack command in src/account/cli.py

**Verification**:

- [ ] T148 [US4] Run `pytest tests/integration/test_slack_integration.py -v` (all tests pass)
- [ ] T149 [US4] Manual test: `python -m src.account.cli test-slack` (sends test message)

**Phase 5 Success Criteria**:
✅ All US4 tests pass
✅ Slack notifications sent successfully (mocked webhook)
✅ Message formatting correct (Block Kit)
✅ Warnings highlighted properly
✅ Failures don't block main operations
✅ Truncation works for large portfolios

---

## Phase 6: US5 (P3) - Automatic Periodic Refresh

**Goal**: Automatically refresh holdings at configured intervals

**Independent Test Criteria**:
- Can configure refresh interval
- Scheduler triggers fetches at correct intervals
- Slack notifications sent on auto-refresh
- Errors logged but scheduler continues
- Can start/stop scheduler

### US5: Scheduler Implementation

**Tests First**:

- [ ] T150 [P] [US5] Write unit test for Scheduler class in tests/unit/account/test_scheduler.py
- [ ] T151 [P] [US5] Write unit test for interval calculation in tests/unit/account/test_scheduler.py
- [ ] T152 [P] [US5] Write unit test for error handling (continues on error) in tests/unit/account/test_scheduler.py
- [ ] T153 [P] [US5] Write unit test for graceful shutdown in tests/unit/account/test_scheduler.py

**Implementation**:

- [ ] T154 [US5] Implement Scheduler class in src/account/scheduler.py
- [ ] T155 [US5] Implement start() method with threading in src/account/scheduler.py
- [ ] T156 [US5] Implement stop() method in src/account/scheduler.py
- [ ] T157 [US5] Implement _run_scheduled_fetch() in src/account/scheduler.py
- [ ] T158 [US5] Add schedule command to CLI in src/account/cli.py

**Verification**:

- [ ] T159 [US5] Run `pytest tests/unit/account/test_scheduler.py -v` (all tests pass)

**Integration Tests**:

- [ ] T160 [P] [US5] Write integration test for scheduler triggers fetch in tests/integration/test_scheduler_integration.py

**Verification**:

- [ ] T161 [US5] Run `pytest tests/integration/test_scheduler_integration.py -v` (all tests pass)
- [ ] T162 [US5] Manual test: Start scheduler with 1-minute interval, verify fetches occur

**Phase 6 Success Criteria**:
✅ All US5 tests pass
✅ Scheduler runs fetches at configured intervals
✅ Errors logged and scheduler continues
✅ Can start/stop gracefully

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Finalize implementation with logging, documentation, and quality checks

### Logging & Error Handling

**Tests First**:

- [ ] T163 [P] Write unit test for structured logging in tests/unit/account/test_logging.py
- [ ] T164 [P] Write unit test for credential redaction in logs in tests/unit/account/test_logging.py

**Implementation**:

- [ ] T165 Configure structured logging in src/account/__init__.py
- [ ] T166 Implement log_api_call() decorator in src/account/logging.py
- [ ] T167 Implement redact_credentials() filter in src/account/logging.py
- [ ] T168 Add logging to all major operations (auth, fetch, slack)

**Verification**:

- [ ] T169 Run `pytest tests/unit/account/test_logging.py -v` (all tests pass)
- [ ] T170 Manual test: Run fetch command, verify logs don't contain credentials

### Property-Based Tests (Hypothesis)

**Tests First**:

- [ ] T171 [P] Write property test for Decimal arithmetic (no precision loss) in tests/unit/account/test_properties.py
- [ ] T172 [P] Write property test for AccountHoldings total_value calculation in tests/unit/account/test_properties.py
- [ ] T173 [P] Write property test for PortfolioState conversion fidelity in tests/unit/account/test_properties.py

**Verification**:

- [ ] T174 Run `pytest tests/unit/account/test_properties.py -v` (all tests pass)

### Documentation

- [ ] T175 Update pyproject.toml with new dependencies (finalize versions)
- [ ] T176 Create config/config.sample.yaml with inline comments
- [ ] T177 Update src/account/__init__.py with module docstring
- [ ] T178 Add docstrings to all public classes and methods
- [ ] T179 Create config/.gitignore (ignore config.yaml, allow config.sample.yaml)

### Code Quality

- [ ] T180 Run `ruff check src/account/ src/notifications/` (fix all issues)
- [ ] T181 Run `mypy src/account/ src/notifications/ --strict` (fix all type errors)
- [ ] T182 Run full test suite: `pytest tests/ -v --cov=src/account --cov=src/notifications`
- [ ] T183 Verify coverage ≥ 85% for account and notifications modules
- [ ] T184 Run pre-commit hooks: `pre-commit run --all-files`

### Final Verification

- [ ] T185 End-to-end manual test with real config (mock API): Fetch holdings for multiple accounts with Slack notification
- [ ] T186 Verify all success criteria from spec.md are met
- [ ] T187 Verify all acceptance scenarios from spec.md pass
- [ ] T188 Update CLAUDE.md with any additional commands or patterns

**Phase 7 Success Criteria**:
✅ All tests pass (100% pass rate)
✅ Code quality checks pass
✅ Coverage ≥ 85%
✅ Documentation complete
✅ Manual end-to-end test successful

---

## Task Dependencies

### Story Completion Order

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← Must complete before user stories
    ↓
    ├─→ Phase 3 (US1+US2 - P1) ← MVP - IMPLEMENT FIRST
    │       ↓
    ├─→ Phase 4 (US3 - P2) ← Depends on Phase 3
    │       ↓
    ├─→ Phase 5 (US4 - P2) ← Depends on Phase 3 (can run parallel to Phase 4)
    │       ↓
    └─→ Phase 6 (US5 - P3) ← Depends on Phase 3, Phase 5
            ↓
Phase 7 (Polish) ← Depends on all phases
```

### Critical Path

1. **Setup** (T001-T016) - 2 hours
2. **Foundational** (T017-T050) - 8 hours
3. **US1+US2** (T051-T102) - 16 hours ← **MVP COMPLETE HERE**
4. **US3** (T103-T117) - 6 hours
5. **US4** (T118-T149) - 8 hours (can overlap with US3)
6. **US5** (T160-T162) - 4 hours
7. **Polish** (T163-T188) - 6 hours

**Total Estimated Time**: ~50 hours

---

## Parallel Execution Opportunities

### Within Phase 2 (Foundational)

Can be executed in parallel (different files):

**Batch 1** (After T016):
- T017-T020 (crypto tests)
- T031-T034 (model tests)
- T042 (provider interface test)
- T046-T047 (rate limiter & retry tests)

**Batch 2** (After Batch 1 tests pass):
- T021-T028 (crypto & config implementation)
- T035-T040 (model implementation)
- T043-T044 (provider interface implementation)
- T048-T049 (rate limiter & retry implementation)

### Within Phase 3 (US1+US2)

Can be executed in parallel (different modules):

**Batch 1** (Tests):
- T051-T054 (auth tests)
- T063-T067 (provider tests)
- T078-T080 (service tests)
- T090-T091 (CLI tests)

**Batch 2** (Implementation after respective tests):
- T055-T058 (auth implementation)
- T068-T073 (provider implementation)
- T081-T084 (service implementation)
- T092-T095 (CLI implementation)

**Batch 3** (Contract & Integration tests):
- T059-T060 (auth contract tests)
- T074-T077 (holdings contract tests)
- T086-T089 (integration tests)

**Batch 4** (Utilities - can run anytime after T021):
- T098-T099 (fixtures)
- T100-T102 (utilities)

### Within Phase 5 (US4 - Slack)

Can be executed in parallel:

**Batch 1** (Tests):
- T118-T122 (formatter tests)
- T132-T135 (client tests)

**Batch 2** (Implementation):
- T123-T129 (formatter implementation)
- T136-T139 (client implementation)

### Within Phase 7 (Polish)

Can be executed in parallel:

**Batch 1**:
- T163-T164 (logging tests)
- T171-T173 (property tests)
- T175-T179 (documentation)

---

## Independent Test Validation

### US1+US2 (MVP) Test Checklist

Can independently verify MVP is complete:

1. ✅ Authentication works (T051-T062)
2. ✅ Holdings fetch works (T063-T077)
3. ✅ Service layer works (T078-T085)
4. ✅ Integration test passes (T086-T089)
5. ✅ CLI works (T090-T097)
6. ✅ PortfolioState conversion accurate (T034, T041)
7. ✅ Warning indicators function (T079, T084)
8. ✅ Retry logic works (T047, T088)
9. ✅ Rate limiting works (T067, T088)
10. ✅ All tests pass: `pytest tests/unit/account/ tests/integration/test_account_integration.py -v`

### US3 Test Checklist

Can independently verify multi-account support:

1. ✅ Multiple account config works (T103, T112)
2. ✅ Fetch all works (T104, T113)
3. ✅ Consolidated view works (T105, T113)
4. ✅ Partial failures handled (T106, T115)
5. ✅ Integration tests pass (T114-T116)
6. ✅ Manual test with 2+ accounts succeeds (T117)

### US4 Test Checklist

Can independently verify Slack integration:

1. ✅ Message formatting works (T119-T122, T130-T131)
2. ✅ Slack client works (T132-T135, T141-T142)
3. ✅ Integration with fetch works (T143-T144, T148)
4. ✅ Failures don't block main ops (T144)
5. ✅ Test command works (T147, T149)

### US5 Test Checklist

Can independently verify auto-refresh:

1. ✅ Scheduler works (T150-T153, T159)
2. ✅ Integration test passes (T160-T161)
3. ✅ Manual test succeeds (T162)

---

## Test Execution Commands

### Run All Tests

```bash
pytest tests/ -v --cov=src/account --cov=src/notifications --cov-report=html
```

### Run Tests by Phase

```bash
# Phase 2: Foundational
pytest tests/unit/account/test_crypto.py tests/unit/account/test_config.py tests/unit/account/test_models.py -v

# Phase 3: US1+US2 (MVP)
pytest tests/unit/account/test_auth.py tests/unit/account/providers/ tests/unit/account/test_service.py tests/unit/account/test_cli.py tests/integration/test_account_integration.py -v

# Phase 4: US3
pytest tests/unit/account/test_config.py::test_multiple_accounts tests/unit/account/test_service.py::test_multi_account tests/integration/test_multi_account.py -v

# Phase 5: US4
pytest tests/unit/notifications/ tests/integration/test_slack_integration.py -v

# Phase 6: US5
pytest tests/unit/account/test_scheduler.py tests/integration/test_scheduler_integration.py -v

# Phase 7: Polish
pytest tests/unit/account/test_logging.py tests/unit/account/test_properties.py -v
```

### Run Contract Tests

```bash
pytest tests/contract/ -v
```

### Run Property-Based Tests

```bash
pytest tests/unit/account/test_properties.py -v --hypothesis-show-statistics
```

---

## Progress Tracking

### Task Status Summary

| Phase | Total Tasks | Completed | In Progress | Not Started |
|-------|-------------|-----------|-------------|-------------|
| Phase 1: Setup | 16 | 0 | 0 | 16 |
| Phase 2: Foundational | 34 | 0 | 0 | 34 |
| Phase 3: US1+US2 (MVP) | 52 | 0 | 0 | 52 |
| Phase 4: US3 | 15 | 0 | 0 | 15 |
| Phase 5: US4 | 32 | 0 | 0 | 32 |
| Phase 6: US5 | 13 | 0 | 0 | 13 |
| Phase 7: Polish | 26 | 0 | 0 | 26 |
| **TOTAL** | **188** | **0** | **0** | **188** |

### MVP Progress (US1+US2)

Completion = (Phase 1 + Phase 2 + Phase 3 completed tasks) / (16 + 34 + 52) = 0%

**MVP is complete when**: All tasks T001-T102 are checked off

---

## Notes

- **TDD Approach**: All tests written before implementation (test tasks precede implementation tasks)
- **Parallel Opportunities**: Tasks marked with [P] can be executed in parallel with other [P] tasks in same batch
- **Story Labels**: [US1], [US2], etc. map to user stories in spec.md for traceability
- **Independent Testing**: Each user story phase has verification criteria and can be tested independently
- **Incremental Delivery**: MVP (US1+US2) can be delivered first, other stories added incrementally
- **File Paths**: All tasks include specific file paths for clarity
- **Estimated Time**: Total ~50 hours, MVP ~26 hours

**Last Updated**: 2025-11-24
