# asset_allocation_proj Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-24

## Active Technologies

- Python 3.11+ + pandas (≥2.0), numpy (≥1.24), pytest (≥7.0), hypothesis (≥6.0), requests (≥2.31) (001-backtesting-logic)
- Python 3.11+ + cryptography (≥41.0), pydantic (≥2.0), PyYAML (≥6.0), tenacity (≥8.2), requests (≥2.31) (002-account-integration)

## Project Structure

```text
src/
├── models/          # Data models (PortfolioState, Strategy, etc.)
├── backtesting/     # Backtesting engine and rebalancer
├── data/            # Data loaders and providers
├── account/         # NEW (002): Brokerage account integration
│   ├── providers/   # Provider-specific implementations
│   └── models.py    # Account entities
├── notifications/   # NEW (002): Slack notifications
└── cli/             # Command-line interface

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
├── contract/        # API contract tests
└── fixtures/        # Test fixtures and mocks
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes

- 002-account-integration: Added Python 3.11+ + cryptography (≥41.0), pydantic (≥2.0), PyYAML (≥6.0), tenacity (≥8.2) for brokerage account integration and Slack notifications
- 001-backtesting-logic: Added Python 3.11+ + pandas (≥2.0), numpy (≥1.24), pytest (≥7.0), hypothesis (≥6.0), requests (≥2.31)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
