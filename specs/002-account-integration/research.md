# Research: Brokerage Account Integration Technologies

**Feature**: 002-account-integration | **Date**: 2025-11-24 | **Phase**: 0

This document captures technology research and decisions for the brokerage account integration feature.

## Research Summary

All technical unknowns from the plan have been researched and resolved with concrete decisions.

---

## 1. Korea Investment & Securities API

### Decision

**Use Korea Investment & Securities Open API with REST endpoints**

###Rationale

- Korea Investment & Securities provides a comprehensive Open API for retail investors
- REST-based API with JSON responses (easy integration with Python requests library)
- Support for account authentication, balance inquiries, and holdings retrieval
- Official Python examples available in their documentation

### API Structure

**Authentication Flow**:
- OAuth 2.0 style with APP_KEY and APP_SECRET
- Token-based authentication (access token + token_type)
- Tokens expire after 24 hours (meets SC-007 requirement)

**Key Endpoints**:
1. `/oauth2/tokenP` - Get access token
2. `/uapi/domestic-stock/v1/trading/inquire-balance` - Get account balance and holdings
3. `/uapi/overseas-stock/v1/trading/inquire-balance` - For overseas holdings (future)

**Holdings Response Structure**:
```json
{
  "output1": {
    "dnca_tot_amt": "1000000",  // Total deposit
    "nxdy_excc_amt": "950000",  // Net assets
    "tot_evlu_amt": "10500000"  // Total evaluation amount
  },
  "output2": [
    {
      "pdno": "005930",           // Stock code
      "prdt_name": "삼성전자",     // Stock name
      "hldg_qty": "100",          // Holding quantity
      "pchs_avg_pric": "70000",   // Average purchase price
      "prpr": "71000",            // Current price
      "evlu_amt": "7100000"       // Evaluation amount
    }
  ]
}
```

**Rate Limiting**:
- Documented limit: 1 request per second per API key
- Implementation: Use request queue with 1.1 second delays (safety margin)

**Error Responses**:
- HTTP status codes (200, 401, 429, 500)
- Error messages in Korean and English
- Specific error codes for authentication failures

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Kiwoom Securities API | User selected Korea Investment (clarification Q1) |
| Screen scraping | Unreliable, breaks easily, violates ToS, no official support |
| Third-party aggregators (Plaid equivalent) | Not available for Korean brokerages, adds dependency |

### Implementation Notes

- Store API credentials (APP_KEY, APP_SECRET, account_number) in encrypted config
- Implement token refresh logic (check expiry, renew before 24h)
- Mock API responses for testing (save real responses as fixtures)
- Handle Korean character encoding (UTF-8)

---

## 2. Credential Encryption

### Decision

**Use `cryptography` library with Fernet (symmetric encryption) and PBKDF2 key derivation**

### Rationale

- **cryptography** is the standard Python library for encryption (maintained by PyCA)
- Fernet provides authenticated encryption (prevents tampering)
- PBKDF2 derives strong encryption keys from passwords/passphrases
- Simple API: `Fernet.encrypt()` / `Fernet.decrypt()`
- No need for asymmetric encryption (single-user system)

### Implementation Approach

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

# Key derivation from passphrase (stored separately or env var)
kdf = PBKDF2(
    algorithm=hashes.SHA256(),
    length=32,
    salt=os.environ['ENCRYPTION_SALT'],  # Fixed salt (or store in config)
    iterations=480000,  # OWASP recommendation
)
key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
cipher = Fernet(key)

# Encrypt credentials
encrypted_app_key = cipher.encrypt(app_key.encode())

# Decrypt for use
decrypted_app_key = cipher.decrypt(encrypted_app_key).decode()
```

### Storage Format

```yaml
# config.yaml (encrypted fields marked)
accounts:
  - name: "Main Account"
    provider: "korea_investment"
    credentials:
      app_key: "gAAAAABhk..."  # Encrypted
      app_secret: "gAAAAABhk..."  # Encrypted
      account_number: "gAAAAABhk..."  # Encrypted
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| PyCryptodome | Less widely adopted than cryptography, similar features |
| keyring library | Requires OS-level keychain (not portable, complex setup) |
| Argon2 (key derivation) | PBKDF2 sufficient for this use case, Argon2 adds dependency |
| Plaintext with file permissions | Violates FR-006 (encryption required), insecure |

### Implementation Notes

- Store encryption passphrase in environment variable `ACCOUNT_ENCRYPTION_KEY`
- Provide key generation utility (`python -m src.account.keygen`)
- Validate decryption on startup (fail fast if key is wrong)
- Never log encrypted or decrypted credentials

---

## 3. Configuration Format

### Decision

**Use YAML with pydantic for validation**

### Rationale

- YAML is human-readable and supports comments (better for sample files)
- pydantic provides excellent validation with clear error messages
- Type safety catches configuration mistakes early
- Integration: PyYAML for parsing + pydantic models for validation

### Configuration Structure

```yaml
# config.yaml
version: "1.0"

encryption:
  enabled: true
  # Passphrase loaded from environment variable ACCOUNT_ENCRYPTION_KEY

accounts:
  - name: "Main Brokerage Account"
    provider: "korea_investment"
    enabled: true
    credentials:
      app_key: "encrypted_value"  # Or plaintext if encryption disabled (dev only)
      app_secret: "encrypted_value"
      account_number: "encrypted_value"
    settings:
      rate_limit_delay: 1.1  # seconds between requests

notifications:
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/services/XXX/YYY/ZZZ"
    triggers:
      - "manual_refresh"
      - "auto_refresh"
    format: "detailed"  # or "summary"

refresh:
  auto_enabled: false
  interval_minutes: 60
```

### Pydantic Models

```python
from pydantic import BaseModel, HttpUrl, Field
from typing import Literal

class AccountCredentials(BaseModel):
    app_key: str
    app_secret: str
    account_number: str

class BrokerageAccountConfig(BaseModel):
    name: str
    provider: Literal["korea_investment"]
    enabled: bool = True
    credentials: AccountCredentials
    settings: dict[str, float] = Field(default_factory=lambda: {"rate_limit_delay": 1.1})

class SlackConfig(BaseModel):
    enabled: bool = False
    webhook_url: HttpUrl | None = None
    triggers: list[str] = ["manual_refresh"]
    format: Literal["detailed", "summary"] = "detailed"

class Config(BaseModel):
    version: str = "1.0"
    accounts: list[BrokerageAccountConfig]
    notifications: dict[str, SlackConfig]
    refresh: dict[str, bool | int] = Field(default_factory=dict)
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| TOML | Less familiar to users, requires tomllib (Python 3.11+), less flexible for nested structures |
| JSON | No comments, less human-readable, not ideal for configuration files |
| Python file (config.py) | Allows arbitrary code execution (security risk), harder to validate |
| .env files | Flat structure, poor for multiple accounts, no nested configuration |

### Implementation Notes

- Provide comprehensive `config.sample.yaml` with inline comments
- Validate on load with pydantic (fail fast with clear error messages)
- Support environment variable substitution: `${SLACK_WEBHOOK_URL}`
- Configuration file location: `config/config.yaml` (gitignored)

---

## 4. Rate Limiting Implementation

### Decision

**Use simple queue with time.sleep delays (synchronous)**

### Rationale

- Simple and sufficient for single-user CLI tool
- Korea Investment API limit: 1 req/sec → use 1.1 sec delay (safety margin)
- No need for async/threading complexity (SC-002: < 10 sec total is acceptable)
- `collections.deque` provides efficient FIFO queue

### Implementation Approach

```python
from collections import deque
import time
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, min_interval: float = 1.1):
        self.min_interval = min_interval
        self.last_request_time: datetime | None = None

    def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        if self.last_request_time is None:
            self.last_request_time = datetime.now()
            return

        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        self.last_request_time = datetime.now()

class APIClient:
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.request_queue = deque()

    def _make_request(self, endpoint: str, **kwargs):
        self.rate_limiter.wait_if_needed()
        return requests.get(endpoint, **kwargs)
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| asyncio with aiohttp | Adds complexity, not needed for CLI tool, SC-002 allows 10 sec total |
| Threading with queue.Queue | Thread-safe not needed (single-threaded CLI), adds complexity |
| Third-party library (ratelimit, limits) | Adds dependency for simple functionality |
| Token bucket algorithm | Over-engineered for 1 req/sec limit |

### Implementation Notes

- Make rate limit configurable per account (default: 1.1 sec)
- Log rate limiting delays for debugging
- Add metrics: requests_made, delays_applied, total_wait_time

---

## 5. Slack Integration

### Decision

**Use direct webhook POST with requests library and Block Kit formatting**

### Rationale

- Slack incoming webhooks are simple HTTP POST endpoints
- No need for Slack SDK (overkill for one-way notifications)
- Block Kit provides rich formatting (better than plain text)
- Size limit: 3000 characters per message (adequate for portfolio summaries)

### Webhook Format

```python
import requests

def send_slack_notification(webhook_url: str, blocks: list[dict]):
    payload = {
        "blocks": blocks,
        "unfurl_links": False,
        "unfurl_media": False
    }
    response = requests.post(
        webhook_url,
        json=payload,
        timeout=5  # SC-009: < 5 sec delivery
    )
    response.raise_for_status()
```

### Message Format (Block Kit)

```python
blocks = [
    {
        "type": "header",
        "text": {"type": "plain_text", "text": "📊 Portfolio Update: Main Account"}
    },
    {
        "type": "section",
        "fields": [
            {"type": "mrkdwn", "text": "*Total Value:*\n₩10,500,000"},
            {"type": "mrkdwn", "text": "*Cash Balance:*\n₩1,000,000"},
        ]
    },
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Holdings:*\n• 삼성전자 (005930): 100 shares @ ₩71,000 = ₩7,100,000\n• ..."}
    },
    {
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "Updated: 2025-11-24 15:30:45 KST"}]
    }
]
```

### Handling Size Limits

- Limit holdings display to top 10 by value
- Truncate with "... and X more holdings" footer
- Calculate size before sending (estimate: ~100 chars per holding)

### Error Handling

- Timeout after 5 seconds (SC-009)
- Catch requests.exceptions (ConnectionError, Timeout, HTTPError)
- Log error but don't raise (FR-014b: don't block main operation)
- Retry once for transient failures (network timeout)

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Slack SDK (slack_sdk) | Overkill for simple webhooks, adds dependency |
| Email notifications | Requires SMTP setup, less real-time than Slack |
| Discord/Teams webhooks | User specifically requested Slack |
| Slack app with OAuth | Complex setup, not needed for outgoing notifications |

### Implementation Notes

- Validate webhook URL format at configuration load time
- Test webhook with "Connection test" message on first run
- Support both "detailed" and "summary" formats (configurable)
- Handle Korean characters properly (UTF-8 encoding)

---

## 6. Retry Strategy

### Decision

**Use `tenacity` library with exponential backoff**

### Rationale

- Tenacity is the de-facto standard for retry logic in Python
- Clean declarative syntax with decorators
- Supports exponential backoff, stop conditions, retry on specific exceptions
- Well-tested and maintained

### Implementation

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import requests

@retry(
    stop=stop_after_attempt(3),  # FR-009: 3 retries
    wait=wait_exponential(multiplier=1, min=1, max=4),  # 1s, 2s, 4s
    retry=retry_if_exception_type((
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError  # Only for 5xx errors
    )),
    reraise=True
)
def fetch_account_holdings(client: APIClient) -> AccountHoldings:
    response = client.get_holdings()
    response.raise_for_status()
    return parse_holdings(response.json())
```

### Retry Policy by Error Type

| Error Type | Retry? | Rationale |
|------------|--------|-----------|
| ConnectionError | Yes (3x) | Transient network issue |
| Timeout | Yes (3x) | Transient network/server issue |
| HTTP 5xx | Yes (3x) | Server error, might recover |
| HTTP 429 (Rate Limit) | No | Handled by rate limiter |
| HTTP 401 (Auth Failure) | No | Invalid credentials, won't fix with retry |
| HTTP 400 (Bad Request) | No | Code bug, won't fix with retry |

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| backoff library | Similar to tenacity, slightly less popular |
| Custom retry loop | Reinventing the wheel, error-prone |
| No retry library (manual) | Hard to test, missing edge cases |

### Implementation Notes

- Log retry attempts with attempt number and delay
- Include original exception in final error message
- Differentiate between retryable and non-retryable errors
- Total retry time: ~7 seconds max (1s + 2s + 4s)

---

## Technology Stack Summary

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| Broker API Client | requests | ≥2.31 | Standard HTTP library, already in project |
| Credential Encryption | cryptography + Fernet | Latest | Industry standard, authenticated encryption |
| Configuration | PyYAML + pydantic | Latest | Human-readable + type-safe validation |
| Rate Limiting | Custom (time.sleep) | N/A | Simple, sufficient for 1 req/sec limit |
| Slack Integration | requests (webhooks) | ≥2.31 | Direct POST, no SDK needed |
| Retry Logic | tenacity | Latest | Standard retry library with exponential backoff |
| Testing | pytest + hypothesis | ≥7.0, ≥6.0 | Existing project dependencies |

---

## Dependencies to Add

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    # Existing
    "pandas>=2.0",
    "numpy>=1.24",
    "requests>=2.31",

    # New for account integration
    "cryptography>=41.0",  # Credential encryption
    "pydantic>=2.0",       # Configuration validation
    "PyYAML>=6.0",         # YAML parsing
    "tenacity>=8.2",       # Retry logic
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "hypothesis>=6.0",
    # ... existing dev dependencies
]
```

---

## Research Validation

All research tasks from plan.md Phase 0 have been completed:

- ✅ Korea Investment & Securities API (authentication, endpoints, rate limits, error handling)
- ✅ Credential Encryption (library choice, algorithm, key derivation)
- ✅ Configuration Format (YAML + pydantic)
- ✅ Rate Limiting Implementation (simple queue with delays)
- ✅ Slack Integration (webhooks, message format, size limits)
- ✅ Retry Strategy (tenacity with exponential backoff)

All decisions are documented with rationale, alternatives considered, and implementation notes.

**Next Phase**: Generate data model and contracts (Phase 1)
