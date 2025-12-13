# Implementation Plan: Brokerage Account Integration with Slack Notifications

**Branch**: `002-account-integration` | **Date**: 2025-11-24 | **Spec**: [spec.md](./spec.md)

## Summary

This feature integrates with Korea Investment & Securities brokerage API to retrieve current portfolio holdings (cash balance, securities positions, quantities, and market values) and converts them to the existing PortfolioState model format. Additionally, it sends portfolio status updates to Slack for remote monitoring. The system handles authentication via encrypted configuration files, implements retry strategies for API failures, respects rate limits through request queuing, and gracefully handles incomplete data with warning indicators.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- requests (≥2.31) for HTTP API calls
- cryptography for credential encryption
- pydantic for configuration validation
- Existing: pandas (≥2.0), numpy (≥1.24), pytest (≥7.0), hypothesis (≥6.0)

**Storage**:
- Configuration file (YAML/TOML) for encrypted credentials
- No database required (stateless operation)

**Testing**: pytest with hypothesis for property-based testing

**Target Platform**: Linux/macOS server or local development environment

**Project Type**: Single project (CLI-based portfolio management tool)

**Performance Goals**:
- Authentication: < 30 seconds
- Data retrieval: < 10 seconds per account
- Slack notification: < 5 seconds delivery
- API retry strategy: 3 attempts with exponential backoff (1s, 2s, 4s)

**Constraints**:
- Must respect brokerage API rate limits
- Credential security: encryption at rest, never logged
- 95% success rate for API calls under normal conditions
- Session validity: minimum 24 hours

**Scale/Scope**:
- Single user system (MVP)
- 1-3 brokerage accounts per user
- Portfolio size: up to 50 securities per account
- One brokerage provider initially (Korea Investment & Securities)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Test-First Development (NON-NEGOTIABLE)

✅ **PASS**: Implementation plan follows TDD workflow:
- Phase 0: Research technical approaches
- Phase 1: Design data models and contracts
- **Phase 2 (via /speckit.tasks)**: Test creation before implementation
- Tests will cover: authentication, data retrieval, retry logic, rate limiting, Slack integration, error handling

**Test Strategy**:
1. Unit tests for each module (authentication, data fetching, Slack notification, configuration)
2. Integration tests with mocked brokerage API responses
3. Contract tests against API specifications
4. Property-based tests for financial calculations (using hypothesis)
5. Error scenario tests (network failures, invalid credentials, rate limiting)

### II. Financial Data Accuracy (NON-NEGOTIABLE)

✅ **PASS**: Feature handles financial data with appropriate rigor:
- PortfolioState model uses Decimal for all monetary values (existing pattern)
- Data validation before conversion to PortfolioState
- Audit logging for all API interactions (excluding credentials)
- Warning indicators for incomplete/unrecognized data
- 100% fidelity requirement for data conversion (SC-008)

**Accuracy Measures**:
- All prices, quantities, and balances use Decimal type
- Data completeness validation before display
- Reproducible data retrieval with documented API version
- Edge cases documented: zero balance, missing market data, non-standard assets

### III. Simplicity (Start Simple, Justify Complexity)

⚠️ **REQUIRES JUSTIFICATION**: New dependencies introduced

**Complexity Items Requiring Justification**:
1. **cryptography library**: Needed for encrypting API credentials in configuration file (security requirement FR-006)
2. **pydantic library**: Validates configuration file structure and type safety
3. **Request queue/scheduler**: Implements rate limiting (FR-008)

See Complexity Tracking table below for detailed justifications.

**Simplicity Preserved**:
- Direct API calls using existing `requests` library
- No ORM or database (stateless design)
- Single module per concern (auth, fetch, slack, config)
- Reuses existing PortfolioState model
- No framework overhead (FastAPI, Django, etc.)

## Project Structure

### Documentation (this feature)

```text
specs/002-account-integration/
├── plan.md              # This file
├── research.md          # Phase 0: Technology decisions
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Setup instructions
├── contracts/           # Phase 1: API schemas
│   ├── korea-investment-auth.yaml
│   ├── korea-investment-holdings.yaml
│   └── slack-webhook.yaml
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2: Implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── __init__.py
│   ├── portfolio_state.py          # Existing
│   ├── strategy.py                 # Existing
│   └── backtest_config.py          # Existing
├── account/                         # NEW: Account integration module
│   ├── __init__.py
│   ├── auth.py                      # Authentication logic
│   ├── client.py                    # Brokerage API client
│   ├── providers/                   # Provider-specific implementations
│   │   ├── __init__.py
│   │   ├── base.py                  # AccountProvider interface
│   │   └── korea_investment.py     # Korea Investment & Securities implementation
│   ├── models.py                    # BrokerageAccount, AccountHoldings, SecurityPosition entities
│   ├── config.py                    # Configuration file handling
│   └── exceptions.py                # Account-specific exceptions
├── notifications/                   # NEW: Notification module
│   ├── __init__.py
│   ├── slack.py                     # Slack integration
│   ├── formatters.py                # Message formatting logic
│   └── models.py                    # SlackNotification entity
├── backtesting/                     # Existing
│   ├── engine.py
│   ├── rebalancer.py
│   └── ...
├── data/                            # Existing
│   ├── loaders.py
│   ├── providers.py
│   └── ...
└── cli/                             # Existing (will be extended)
    └── __init__.py

tests/
├── unit/
│   ├── account/
│   │   ├── test_auth.py
│   │   ├── test_client.py
│   │   ├── test_config.py
│   │   └── providers/
│   │       └── test_korea_investment.py
│   └── notifications/
│       ├── test_slack.py
│       └── test_formatters.py
├── integration/
│   ├── test_account_integration.py  # End-to-end account data retrieval
│   └── test_slack_integration.py    # End-to-end Slack notification
├── contract/
│   ├── test_korea_investment_contract.py
│   └── test_slack_contract.py
└── fixtures/
    ├── mock_korea_investment_responses.json
    ├── sample_config.yaml
    └── mock_portfolios.py

config/                              # NEW: Configuration templates
├── config.sample.yaml               # Sample configuration file (FR-001a)
└── .gitignore                       # Ensure real config is not committed
```

**Structure Decision**: Selected single project structure (Option 1) as this is a CLI-based tool without separate frontend/backend concerns. All modules are organized under `src/` with clear separation between account integration (`src/account/`), notifications (`src/notifications/`), and existing modules.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| cryptography library | Encrypt API credentials in configuration file (FR-006: credentials must be encrypted at rest) | Storing plaintext credentials violates security requirements and exposes financial account access |
| pydantic library | Type-safe configuration validation with clear error messages for users | Manual dict parsing is error-prone and provides poor user experience when configuration is malformed; dataclasses lack validation |
| Request queue with delays | Implement rate limiting to respect brokerage API limits (FR-008: queue with delays) | Immediate rejection on rate limit would provide poor UX; exponential backoff alone doesn't prevent hitting limits proactively |
| Slack webhook library/logic | Send formatted notifications to Slack (FR-014: Slack integration) | Email or logging would not provide the real-time mobile accessibility that users requested |

## Phase 0: Research & Technology Decisions

**Output**: [research.md](./research.md)

### Research Tasks

The following technical decisions need research:

1. **Korea Investment & Securities API**:
   - Authentication flow (OAuth2, API keys, tokens)
   - Holdings endpoint structure
   - Rate limiting policies
   - Error response formats
   - Python SDK availability

2. **Credential Encryption**:
   - Encryption library choice (cryptography, PyCryptodome)
   - Key derivation method (PBKDF2, Argon2)
   - Storage format (encrypted fields in YAML/TOML)

3. **Configuration Format**:
   - Format choice (YAML vs TOML vs JSON)
   - Validation library (pydantic, marshmallow, attrs)
   - Structure for multiple accounts

4. **Rate Limiting Implementation**:
   - Queue implementation (collections.deque, queue.Queue)
   - Delay mechanism (time.sleep, asyncio, threading)
   - Thread-safety considerations

5. **Slack Integration**:
   - Webhook API format
   - Message formatting (blocks, attachments)
   - Size limits and pagination strategies
   - Error handling patterns

6. **Retry Strategy**:
   - Library choice (tenacity, backoff, custom)
   - Retry policies for different error types
   - Timeout handling

### Research Methodology

For each research task:
1. Review official documentation
2. Evaluate 2-3 alternative approaches
3. Consider: simplicity, maintenance burden, community support, existing project patterns
4. Document decision with rationale

## Phase 1: Design Artifacts

### Data Model ([data-model.md](./data-model.md))

Entities to be designed:

1. **BrokerageAccount**: Connection state and metadata
2. **AccountHoldings**: Portfolio snapshot from brokerage
3. **SecurityPosition**: Individual security holding details
4. **BrokerageProvider**: Provider configuration and capabilities
5. **SlackNotification**: Notification message and delivery status

Each entity includes:
- Fields with types (prefer Decimal for financial data)
- Validation rules
- Relationships to other entities
- State transitions (if applicable)

### API Contracts ([contracts/](./contracts/))

Contract specifications:

1. **korea-investment-auth.yaml**: Authentication endpoint contract
2. **korea-investment-holdings.yaml**: Holdings retrieval endpoint contract
3. **slack-webhook.yaml**: Slack incoming webhook contract

Format: OpenAPI 3.0 specification with:
- Request/response schemas
- Error responses
- Authentication requirements
- Rate limiting notes

### Quickstart Guide ([quickstart.md](./quickstart.md))

Developer setup instructions:
1. Prerequisites (Python 3.11+, API credentials)
2. Installation steps (uv sync, dependencies)
3. Configuration setup (copy sample, encrypt credentials)
4. Running first account data fetch
5. Testing the integration
6. Troubleshooting common issues

## Phase 2: Task Generation

**Note**: Phase 2 (task generation and implementation) is handled by the `/speckit.tasks` command, NOT by `/speckit.plan`.

The `/speckit.tasks` command will:
1. Break down implementation into test-first tasks
2. Order tasks by dependency
3. Create tasks.md with detailed implementation steps

Expected task categories:
1. Configuration and encryption setup
2. Authentication module (tests first, then implementation)
3. API client for Korea Investment & Securities
4. Data transformation to PortfolioState
5. Slack notification module
6. Rate limiting and retry logic
7. Integration tests
8. Documentation and sample files

## Post-Planning Actions

After this planning phase completes:

1. ✅ Constitution Check re-evaluated (see gates above)
2. ✅ Complexity justified (see tracking table)
3. ⏭️ **Next**: Run `/speckit.tasks` to generate implementation tasks
4. ⏭️ User reviews and approves test strategy
5. ⏭️ Implementation begins following TDD workflow

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Korea Investment API documentation incomplete/outdated | High | Research community resources, contact broker support, implement feature flags for untested endpoints |
| API rate limits more restrictive than expected | Medium | Implement conservative default delays, make limits configurable, add queue monitoring |
| Credential encryption adds UX friction | Low | Provide clear quickstart guide, auto-generate encryption key on first run, validate config with helpful errors |
| Slack webhook failures block operations | Medium | Async notification with timeout, graceful degradation (FR-014b), retry queue for failed notifications |
| Multiple account support increases complexity | Medium | Start with single account (P1), add multi-account incrementally (P2), reuse provider interface pattern |

## Success Validation

Implementation is complete when:

1. ✅ All tests pass (unit, integration, contract)
2. ✅ Constitution gates remain green
3. ✅ Success criteria met (SC-001 through SC-011)
4. ✅ Code review confirms TDD adherence
5. ✅ Sample configuration works end-to-end
6. ✅ Quickstart guide validated by fresh setup
7. ✅ No security issues (credentials encrypted, never logged)
8. ✅ Slack notifications delivered within 5 seconds
9. ✅ Rate limiting prevents API errors over 1-hour test
10. ✅ Financial data accuracy verified with known test portfolio
