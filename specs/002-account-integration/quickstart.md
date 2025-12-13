# Quickstart Guide: Brokerage Account Integration

**Feature**: 002-account-integration | **Date**: 2025-11-24

This guide will help you set up and test the brokerage account integration feature.

---

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.11+** installed
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **uv package manager** (recommended) or pip
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Korea Investment & Securities API credentials**:
   - APP_KEY (Application Key)
   - APP_SECRET (Application Secret)
   - ACCOUNT_NUMBER (Your brokerage account number)

   If you don't have these yet:
   - Visit https://apiportal.koreainvestment.com
   - Register for API access
   - Create an application to get APP_KEY and APP_SECRET

4. **Slack Webhook URL** (optional, for notifications):
   - Go to your Slack workspace
   - Create an Incoming Webhook: https://api.slack.com/messaging/webhooks
   - Copy the webhook URL (format: `https://hooks.slack.com/services/T.../B.../XXX`)

---

## Installation

### 1. Clone and Setup Repository

```bash
# Navigate to project directory
cd /path/to/asset_allocation_proj

# Sync dependencies (includes new packages for account integration)
uv sync
```

### 2. Verify New Dependencies

The following new dependencies should be installed:

```bash
uv pip list | grep -E "cryptography|pydantic|tenacity"
```

You should see:
- `cryptography` (≥41.0)
- `pydantic` (≥2.0)
- `tenacity` (≥8.2)

---

## Configuration Setup

### 1. Generate Encryption Key

First, generate an encryption key to secure your API credentials:

```bash
python -m src.account.keygen
```

This will output an encryption key. Save this securely - you'll need it to decrypt your credentials.

```
Generated encryption key: gAAAAABh...
Set this as environment variable ACCOUNT_ENCRYPTION_KEY
```

### 2. Set Environment Variable

Add the encryption key to your environment:

**Linux/macOS (bash/zsh)**:
```bash
export ACCOUNT_ENCRYPTION_KEY="gAAAAABh..."

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export ACCOUNT_ENCRYPTION_KEY="gAAAAABh..."' >> ~/.bashrc
```

**Linux/macOS (fish)**:
```fish
set -Ux ACCOUNT_ENCRYPTION_KEY "gAAAAABh..."
```

**Windows (PowerShell)**:
```powershell
$env:ACCOUNT_ENCRYPTION_KEY="gAAAAABh..."

# For persistence (requires admin):
[System.Environment]::SetEnvironmentVariable('ACCOUNT_ENCRYPTION_KEY', 'gAAAAABh...', 'User')
```

### 3. Create Configuration File

Copy the sample configuration:

```bash
mkdir -p config
cp config/config.sample.yaml config/config.yaml
```

### 4. Edit Configuration

Open `config/config.yaml` in your editor and fill in your credentials:

```yaml
version: "1.0"

accounts:
  - name: "My Main Account"
    provider: "korea_investment"
    enabled: true
    credentials:
      # These will be encrypted automatically on first use
      app_key: "YOUR_APP_KEY_HERE"
      app_secret: "YOUR_APP_SECRET_HERE"
      account_number: "YOUR_ACCOUNT_NUMBER"  # Format: 10 digits (e.g., 5006800001)
    settings:
      rate_limit_delay: 1.1  # Seconds between API requests

notifications:
  slack:
    enabled: true  # Set to false if you don't want Slack notifications
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    triggers:
      - "manual_refresh"
      - "auto_refresh"
    format: "detailed"  # or "summary"

refresh:
  auto_enabled: false  # Enable automatic periodic refresh
  interval_minutes: 60  # Refresh interval if auto_enabled is true
```

### 5. Encrypt Credentials

Run the encryption utility to encrypt your credentials in-place:

```bash
python -m src.account.encrypt_config config/config.yaml
```

This will replace plaintext credentials with encrypted values:

```yaml
credentials:
  app_key: "gAAAAABhk3d..."  # Encrypted
  app_secret: "gAAAAABhk3e..."  # Encrypted
  account_number: "gAAAAABhk3f..."  # Encrypted
```

⚠️ **Important**: The original `config.yaml` with plaintext credentials should be deleted or moved to a secure location.

### 6. Verify Configuration

Test that your configuration is valid:

```bash
python -m src.account.verify_config config/config.yaml
```

Expected output:
```
✅ Configuration is valid
✅ Encryption key found
✅ Credentials decrypted successfully
✅ 1 account(s) configured
   - My Main Account (korea_investment) ✓
✅ Slack notifications enabled
```

---

## First Run

### 1. Authenticate and Fetch Holdings

Run the account integration CLI:

```bash
python -m src.account.cli fetch --account "My Main Account"
```

Expected output:
```
🔐 Authenticating with Korea Investment & Securities...
✅ Authenticated successfully
   Token expires: 2025-11-25 15:30:00

📊 Fetching account holdings...
✅ Holdings retrieved successfully

Account: My Main Account
─────────────────────────────────
Cash Balance:      ₩1,000,000
Total Value:       ₩10,500,000
Holdings:          2 securities

Holdings Details:
  • 삼성전자 (005930)
    Quantity: 100 shares
    Current Price: ₩71,000
    Value: ₩7,100,000
    P/L: +₩100,000 (+1.43%)

  • 카카오 (035720)
    Quantity: 50 shares
    Current Price: ₩50,000
    Value: ₩2,500,000
    P/L: +₩100,000 (+4.17%)
```

### 2. Verify Slack Notification

If Slack notifications are enabled, check your Slack channel. You should see a formatted message with your portfolio update.

### 3. Test with Mock Data (Development)

For development/testing without real API calls:

```bash
python -m src.account.cli fetch --account "My Main Account" --mock
```

This uses pre-defined mock responses instead of calling the real API.

---

## Common Commands

### Fetch Holdings for All Accounts

```bash
python -m src.account.cli fetch --all
```

### Fetch Without Slack Notification

```bash
python -m src.account.cli fetch --account "My Main Account" --no-slack
```

### View Configuration

```bash
python -m src.account.cli config --show
```

### Test Slack Integration

```bash
python -m src.account.cli test-slack
```

This sends a test message to Slack to verify the webhook is working.

### Enable Auto-Refresh

Edit `config/config.yaml`:

```yaml
refresh:
  auto_enabled: true
  interval_minutes: 60  # Fetch holdings every 60 minutes
```

Then run the scheduler:

```bash
python -m src.account.cli schedule
```

---

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Unit Tests Only

```bash
pytest tests/unit/
```

### Run Integration Tests

```bash
pytest tests/integration/
```

### Run with Coverage

```bash
pytest --cov=src/account --cov=src/notifications tests/
```

### Run Contract Tests

Contract tests verify API responses match the expected schema:

```bash
pytest tests/contract/
```

---

## Troubleshooting

### Issue: "Encryption key not found"

**Solution**: Ensure `ACCOUNT_ENCRYPTION_KEY` environment variable is set:

```bash
echo $ACCOUNT_ENCRYPTION_KEY  # Should output your key
```

If empty, set it again following step 2 in Configuration Setup.

---

### Issue: "Invalid credentials" or "401 Unauthorized"

**Possible causes**:
1. APP_KEY or APP_SECRET is incorrect
2. API access not enabled in Korea Investment portal
3. Credentials expired or revoked

**Solution**:
1. Verify credentials in Korea Investment portal
2. Check API access is enabled
3. Generate new credentials if necessary
4. Update `config/config.yaml` and re-encrypt

---

### Issue: "Rate limit exceeded" or "429 Too Many Requests"

**Solution**:
- Increase `rate_limit_delay` in configuration (default: 1.1 seconds)
- Reduce frequency of manual fetches
- If using auto-refresh, increase `interval_minutes`

```yaml
settings:
  rate_limit_delay: 2.0  # Increase to 2 seconds between requests
```

---

### Issue: "Slack webhook failed" or notifications not appearing

**Possible causes**:
1. Webhook URL is invalid or revoked
2. Slack workspace permissions changed
3. Network connectivity issue

**Solution**:
1. Test webhook manually:
   ```bash
   python -m src.account.cli test-slack
   ```
2. Regenerate webhook URL in Slack if revoked
3. Check network connectivity to hooks.slack.com
4. Review Slack webhook logs in app management

---

### Issue: "Security symbol not recognized" warning

This means a security in your account couldn't be identified or has incomplete data.

**Solution**:
- This is expected for non-standard assets (options, futures, bonds)
- Holdings are still shown with available data
- Warning indicator appears in display and Slack notifications
- No action needed unless the security code is incorrect

---

### Issue: Token expired during operation

**Solution**:
- System automatically re-authenticates using stored credentials
- If re-authentication fails, check credentials are still valid
- Verify account status:
  ```bash
  python -m src.account.cli status
  ```

---

## Configuration Reference

### Complete config.yaml Example

```yaml
version: "1.0"

# Multiple accounts support
accounts:
  - name: "Main Trading Account"
    provider: "korea_investment"
    enabled: true
    credentials:
      app_key: "gAAAAABhk..."  # Encrypted
      app_secret: "gAAAAABhk..."  # Encrypted
      account_number: "gAAAAABhk..."  # Encrypted
    settings:
      rate_limit_delay: 1.1
      timeout_seconds: 30

  - name: "Long Term Account"
    provider: "korea_investment"
    enabled: true
    credentials:
      app_key: "gAAAAABhk..."
      app_secret: "gAAAAABhk..."
      account_number: "gAAAAABhk..."
    settings:
      rate_limit_delay: 1.1

# Notification settings
notifications:
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/services/..."
    triggers:
      - "manual_refresh"  # Send on manual fetch
      - "auto_refresh"    # Send on scheduled fetch
      - "on_demand"       # Send when explicitly requested
      - "error"           # Send on errors
    format: "detailed"  # "detailed" = full holdings list, "summary" = top 10 only

# Auto-refresh settings
refresh:
  auto_enabled: false
  interval_minutes: 60
```

---

## Next Steps

Now that you have the account integration working:

1. **Review the Data Model**: See [data-model.md](./data-model.md) for entity definitions
2. **Explore API Contracts**: Check [contracts/](./contracts/) for API specifications
3. **Run the Test Suite**: Ensure all tests pass before making changes
4. **Integrate with Backtesting**: Use `AccountHoldings.to_portfolio_state()` to convert to `PortfolioState` for backtesting
5. **Customize Notifications**: Modify Slack message format in `src/notifications/formatters.py`

---

## Getting Help

### Documentation

- Feature Specification: [spec.md](./spec.md)
- Implementation Plan: [plan.md](./plan.md)
- Research Notes: [research.md](./research.md)

### API Documentation

- Korea Investment API: https://apiportal.koreainvestment.com
- Slack Webhooks: https://api.slack.com/messaging/webhooks
- Slack Block Kit: https://api.slack.com/block-kit

### Support

For issues specific to this feature:
1. Check troubleshooting section above
2. Review error logs in `logs/account-integration.log`
3. Run tests to isolate the issue: `pytest tests/ -v`
4. Check API status pages for service outages

---

## Security Best Practices

1. **Never commit** `config/config.yaml` to version control
   - Ensure `config/` is in `.gitignore`
   - Use `config.sample.yaml` as template only

2. **Protect encryption key**:
   - Store `ACCOUNT_ENCRYPTION_KEY` in environment variables
   - Don't hard-code in scripts
   - Use secrets management (e.g., AWS Secrets Manager) in production

3. **Rotate credentials** periodically:
   - Generate new APP_KEY/APP_SECRET every 6-12 months
   - Update configuration and re-encrypt

4. **Monitor API usage**:
   - Review logs for unauthorized access attempts
   - Set up alerts for failed authentication

5. **Limit Slack webhook exposure**:
   - Don't share webhook URLs publicly
   - Regenerate if accidentally exposed
   - Use private Slack channels for sensitive portfolio data

---

**Last Updated**: 2025-11-24
**Feature Branch**: 002-account-integration
