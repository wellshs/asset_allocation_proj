# Data Model: Brokerage Account Integration

**Feature**: 002-account-integration | **Date**: 2025-11-24 | **Phase**: 1

This document defines all data entities for the brokerage account integration feature.

---

## Entity Overview

| Entity | Purpose | Location |
|--------|---------|----------|
| BrokerageAccount | Represents a connection to a brokerage account | `src/account/models.py` |
| AccountHoldings | Snapshot of current holdings from brokerage | `src/account/models.py` |
| SecurityPosition | Individual security holding within an account | `src/account/models.py` |
| BrokerageProvider | Configuration for a brokerage API provider | `src/account/providers/base.py` |
| SlackNotification | Notification message and delivery tracking | `src/notifications/models.py` |
| AccountConfig | Configuration for account credentials and settings | `src/account/config.py` |

---

## 1. BrokerageAccount

**Purpose**: Represents a connection to a specific brokerage account with authentication state and metadata.

### Fields

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class AccountStatus(Enum):
    """Account connection status."""
    DISCONNECTED = "disconnected"  # Not authenticated
    CONNECTED = "connected"        # Successfully authenticated
    ERROR = "error"                # Authentication or connection error
    EXPIRED = "expired"            # Token expired, needs re-auth

@dataclass
class BrokerageAccount:
    """Represents a brokerage account connection.

    Attributes:
        account_id: Unique identifier for this account (user-defined name)
        provider: Brokerage provider name (e.g., "korea_investment")
        account_number: Encrypted account number at the brokerage
        status: Current connection status
        access_token: Current API access token (encrypted)
        token_expiry: When the access token expires
        last_fetch_time: Timestamp of last successful data fetch
        last_error: Last error message (if status == ERROR)
    """
    account_id: str
    provider: str
    account_number: str
    status: AccountStatus
    access_token: str | None = None
    token_expiry: datetime | None = None
    last_fetch_time: datetime | None = None
    last_error: str | None = None

    def is_authenticated(self) -> bool:
        """Check if account is currently authenticated."""
        return (
            self.status == AccountStatus.CONNECTED
            and self.access_token is not None
            and self.token_expiry is not None
            and datetime.now() < self.token_expiry
        )

    def needs_reauth(self) -> bool:
        """Check if account needs re-authentication."""
        return (
            self.status in (AccountStatus.DISCONNECTED, AccountStatus.EXPIRED)
            or self.token_expiry is None
            or datetime.now() >= self.token_expiry
        )
```

### Validation Rules

- `account_id`: Non-empty string, unique across all accounts
- `provider`: Must be a supported provider ("korea_investment")
- `account_number`: Non-empty encrypted string
- `access_token`: Non-empty when status == CONNECTED
- `token_expiry`: Must be future datetime when status == CONNECTED
- `last_fetch_time`: Cannot be in the future

### State Transitions

```
DISCONNECTED → CONNECTED  (successful authentication)
DISCONNECTED → ERROR      (authentication failure)
CONNECTED → EXPIRED       (token expires)
CONNECTED → ERROR         (API call fails)
EXPIRED → CONNECTED       (successful re-authentication)
ERROR → CONNECTED         (error resolved, re-authenticated)
```

### Relationships

- Has many `SecurityPosition` (via AccountHoldings)
- Belongs to one `BrokerageProvider`
- May trigger `SlackNotification` on data fetch

---

## 2. AccountHoldings

**Purpose**: Represents the current state of assets in a brokerage account at a specific point in time.

### Fields

```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class AccountHoldings:
    """Current holdings in a brokerage account.

    Attributes:
        account_id: ID of the account these holdings belong to
        timestamp: When this data was retrieved
        cash_balance: Cash available in the account (base currency)
        positions: List of security positions held
        total_value: Total account value (cash + positions)
        has_warnings: Whether any positions have incomplete data
        warnings: List of warning messages for incomplete data
    """
    account_id: str
    timestamp: datetime
    cash_balance: Decimal
    positions: list["SecurityPosition"]
    total_value: Decimal
    has_warnings: bool = False
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    def calculate_total_value(self) -> Decimal:
        """Calculate total account value."""
        positions_value = sum(pos.total_value for pos in self.positions)
        return self.cash_balance + positions_value

    def to_portfolio_state(self) -> "PortfolioState":
        """Convert to existing PortfolioState model."""
        from models.portfolio_state import PortfolioState

        asset_holdings = {
            pos.symbol: pos.quantity
            for pos in self.positions
        }
        current_prices = {
            pos.symbol: pos.current_price
            for pos in self.positions
        }

        return PortfolioState(
            timestamp=self.timestamp.date(),
            cash_balance=self.cash_balance,
            asset_holdings=asset_holdings,
            current_prices=current_prices
        )
```

### Validation Rules

- `account_id`: Must match an existing BrokerageAccount
- `timestamp`: Cannot be in the future
- `cash_balance`: Non-negative Decimal
- `positions`: Can be empty list (zero holdings)
- `total_value`: Must equal `cash_balance + sum(position.total_value)`
- `has_warnings`: True if any position has `incomplete_data == True`

### Relationships

- Belongs to one `BrokerageAccount`
- Has many `SecurityPosition`
- Converts to `PortfolioState` (existing model)

---

## 3. SecurityPosition

**Purpose**: Represents a holding of a specific security within an account.

### Fields

```python
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

class AssetType(Enum):
    """Type of asset."""
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    OPTION = "option"
    FUTURE = "future"
    FOREIGN_STOCK = "foreign_stock"
    UNKNOWN = "unknown"

@dataclass
class SecurityPosition:
    """A single security position in an account.

    Attributes:
        symbol: Security identifier (e.g., stock code)
        name: Human-readable security name
        asset_type: Type of asset
        quantity: Number of units held
        average_price: Average purchase price per unit
        current_price: Current market price per unit
        total_value: Current total value (quantity * current_price)
        incomplete_data: Whether this position has missing/unrecognized data
        warning_message: Warning message if incomplete_data == True
    """
    symbol: str
    name: str
    asset_type: AssetType
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal
    total_value: Decimal
    incomplete_data: bool = False
    warning_message: str | None = None

    def calculate_unrealized_gain(self) -> Decimal:
        """Calculate unrealized gain/loss."""
        return (self.current_price - self.average_price) * self.quantity

    def calculate_return_pct(self) -> Decimal:
        """Calculate percentage return."""
        if self.average_price == 0:
            return Decimal(0)
        return ((self.current_price - self.average_price) / self.average_price) * 100
```

### Validation Rules

- `symbol`: Non-empty string
- `name`: Non-empty string
- `asset_type`: Valid AssetType enum value
- `quantity`: Positive Decimal
- `average_price`: Non-negative Decimal
- `current_price`: Non-negative Decimal (can be 0 if unknown)
- `total_value`: Should equal `quantity * current_price`
- `incomplete_data`: True if any price is 0 or asset_type == UNKNOWN
- `warning_message`: Required if `incomplete_data == True`

### Relationships

- Belongs to one `AccountHoldings`
- Classified by `AssetType`

---

## 4. BrokerageProvider

**Purpose**: Represents configuration and capabilities of a brokerage API provider.

### Fields

```python
from dataclasses import dataclass
from enum import Enum

class AuthMethod(Enum):
    """Authentication method."""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    TOKEN = "token"

@dataclass
class BrokerageProvider:
    """Configuration for a brokerage API provider.

    Attributes:
        provider_id: Unique identifier (e.g., "korea_investment")
        display_name: Human-readable name
        base_url: API base URL
        auth_method: Authentication method used
        rate_limit_per_second: Maximum requests per second
        token_lifetime_hours: How long tokens remain valid
        supports_multiple_accounts: Whether user can have multiple accounts
    """
    provider_id: str
    display_name: str
    base_url: str
    auth_method: AuthMethod
    rate_limit_per_second: float
    token_lifetime_hours: int
    supports_multiple_accounts: bool = True

    def get_rate_limit_delay(self) -> float:
        """Calculate minimum delay between requests (with safety margin)."""
        return (1.0 / self.rate_limit_per_second) * 1.1  # 10% safety margin
```

### Validation Rules

- `provider_id`: Non-empty, lowercase with underscores
- `display_name`: Non-empty string
- `base_url`: Valid HTTPS URL
- `auth_method`: Valid AuthMethod enum
- `rate_limit_per_second`: Positive float
- `token_lifetime_hours`: Positive integer

### Predefined Providers

```python
KOREA_INVESTMENT = BrokerageProvider(
    provider_id="korea_investment",
    display_name="Korea Investment & Securities",
    base_url="https://openapi.koreainvestment.com:9443",
    auth_method=AuthMethod.OAUTH2,
    rate_limit_per_second=1.0,
    token_lifetime_hours=24,
    supports_multiple_accounts=True
)
```

---

## 5. SlackNotification

**Purpose**: Represents a notification message to be sent to Slack with delivery tracking.

### Fields

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class NotificationStatus(Enum):
    """Notification delivery status."""
    PENDING = "pending"      # Not yet sent
    SENT = "sent"            # Successfully delivered
    FAILED = "failed"        # Delivery failed
    RETRYING = "retrying"    # Retrying after transient failure

class NotificationTrigger(Enum):
    """What triggered this notification."""
    MANUAL_REFRESH = "manual_refresh"
    AUTO_REFRESH = "auto_refresh"
    ON_DEMAND = "on_demand"
    ERROR = "error"

@dataclass
class SlackNotification:
    """A Slack notification message.

    Attributes:
        notification_id: Unique identifier
        account_id: Account this notification is about
        trigger: What triggered this notification
        webhook_url: Slack webhook URL to send to
        message_blocks: Slack Block Kit formatted message
        status: Delivery status
        created_at: When notification was created
        sent_at: When notification was successfully sent
        error_message: Error message if status == FAILED
        retry_count: Number of delivery attempts
    """
    notification_id: str
    account_id: str
    trigger: NotificationTrigger
    webhook_url: str
    message_blocks: list[dict]
    status: NotificationStatus
    created_at: datetime
    sent_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = 0

    def mark_sent(self):
        """Mark notification as successfully sent."""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now()
        self.error_message = None

    def mark_failed(self, error: str):
        """Mark notification as failed."""
        self.status = NotificationStatus.FAILED
        self.error_message = error
        self.retry_count += 1
```

### Validation Rules

- `notification_id`: Non-empty unique string (UUID recommended)
- `account_id`: Must match an existing BrokerageAccount
- `trigger`: Valid NotificationTrigger enum
- `webhook_url`: Valid HTTPS Slack webhook URL
- `message_blocks`: Non-empty list of Block Kit blocks
- `status`: Valid NotificationStatus enum
- `created_at`: Cannot be in the future
- `sent_at`: Must be after `created_at` if not None
- `retry_count`: Non-negative integer (max: 3)

### State Transitions

```
PENDING → SENT     (successful delivery)
PENDING → FAILED   (delivery error, max retries exceeded)
PENDING → RETRYING (transient error, will retry)
RETRYING → SENT    (retry successful)
RETRYING → FAILED  (retry failed, max retries exceeded)
```

### Relationships

- Belongs to one `BrokerageAccount`
- Triggered by NotificationTrigger event

---

## 6. AccountConfig

**Purpose**: Configuration for account credentials and settings loaded from config file.

### Fields

```python
from pydantic import BaseModel, HttpUrl, Field, field_validator

class AccountCredentials(BaseModel):
    """Encrypted account credentials."""
    app_key: str
    app_secret: str
    account_number: str

    @field_validator("app_key", "app_secret", "account_number")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Credential field cannot be empty")
        return v

class AccountSettings(BaseModel):
    """Account-specific settings."""
    rate_limit_delay: float = 1.1
    timeout_seconds: int = 30

class BrokerageAccountConfig(BaseModel):
    """Configuration for a single brokerage account."""
    name: str = Field(..., min_length=1, description="User-friendly account name")
    provider: str = Field(..., pattern="^[a-z_]+$", description="Provider ID")
    enabled: bool = True
    credentials: AccountCredentials
    settings: AccountSettings = Field(default_factory=AccountSettings)

class SlackConfig(BaseModel):
    """Slack notification configuration."""
    enabled: bool = False
    webhook_url: HttpUrl | None = None
    triggers: list[str] = ["manual_refresh"]
    format: str = "detailed"  # "detailed" or "summary"

    @field_validator("triggers")
    @classmethod
    def validate_triggers(cls, v: list[str]) -> list[str]:
        valid_triggers = ["manual_refresh", "auto_refresh", "on_demand", "error"]
        for trigger in v:
            if trigger not in valid_triggers:
                raise ValueError(f"Invalid trigger: {trigger}")
        return v

class RefreshConfig(BaseModel):
    """Auto-refresh configuration."""
    auto_enabled: bool = False
    interval_minutes: int = 60

class Config(BaseModel):
    """Root configuration model."""
    version: str = "1.0"
    accounts: list[BrokerageAccountConfig] = Field(..., min_length=1)
    notifications: dict[str, SlackConfig] = Field(default_factory=lambda: {"slack": SlackConfig()})
    refresh: RefreshConfig = Field(default_factory=RefreshConfig)

    @field_validator("accounts")
    @classmethod
    def validate_unique_names(cls, v: list[BrokerageAccountConfig]) -> list[BrokerageAccountConfig]:
        names = [acc.name for acc in v]
        if len(names) != len(set(names)):
            raise ValueError("Account names must be unique")
        return v
```

### Validation Rules

- Enforced by pydantic validators
- All credentials must be non-empty
- Account names must be unique
- Provider IDs must be lowercase with underscores
- Slack webhook URL must be valid HTTPS URL
- Triggers must be from allowed list
- At least one account must be configured

---

## Data Flow

### Account Data Retrieval Flow

```
1. Load Config
   ├─> AccountConfig (pydantic validation)
   └─> Decrypt credentials

2. Authenticate
   ├─> BrokerageAccount (create/update)
   ├─> Call auth endpoint
   └─> Update access_token, token_expiry, status

3. Fetch Holdings
   ├─> Call holdings endpoint (with rate limiting)
   ├─> Parse API response
   └─> Create AccountHoldings
       └─> Create SecurityPosition (for each holding)

4. Convert to PortfolioState
   └─> AccountHoldings.to_portfolio_state()

5. Send Notification (if enabled)
   ├─> Create SlackNotification
   ├─> Format message blocks
   └─> Send via webhook
```

### Data Transformations

```
API Response (JSON)
    ↓
AccountHoldings + SecurityPosition[]
    ↓
PortfolioState (existing model)
    ↓
Application logic (backtesting, analysis, etc.)
```

---

## Decimal Usage

All financial values use `Decimal` type for precision:

- `cash_balance` (AccountHoldings)
- `total_value` (AccountHoldings, SecurityPosition)
- `quantity` (SecurityPosition)
- `average_price` (SecurityPosition)
- `current_price` (SecurityPosition)

**Rationale**: Floating point arithmetic can introduce rounding errors. `Decimal` ensures financial accuracy (Constitution Principle II).

---

## Testing Considerations

### Unit Tests

- Test each entity's validation rules
- Test state transitions (BrokerageAccount, SlackNotification)
- Test calculations (total_value, unrealized_gain, return_pct)
- Test conversions (to_portfolio_state)

### Property-Based Tests (Hypothesis)

- Generate random valid entities
- Verify invariants hold (e.g., total_value == sum of positions)
- Test Decimal precision (no rounding errors)

### Integration Tests

- Test full data flow with mocked API responses
- Test error scenarios (invalid data, missing fields)
- Test configuration loading and validation

---

## Implementation Notes

1. **Immutability**: Consider using `frozen=True` for dataclasses where appropriate
2. **Serialization**: Add `to_dict()` / `from_dict()` methods for persistence if needed
3. **Logging**: Log all entity state changes (excluding sensitive data)
4. **Error Messages**: Provide clear validation error messages for user-facing configuration
5. **Type Hints**: Use strict type hints throughout (checked with mypy)

**Next Phase**: Generate API contracts (Phase 1 continued)
