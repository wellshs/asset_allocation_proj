"""Unit tests for CLI Slack integration."""

from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime, timezone

from src.account.cli import validate_slack_config, send_to_slack
from src.account.models import AccountHoldings


class TestValidateSlackConfig:
    """Test Slack configuration validation."""

    def test_validate_with_valid_config(self):
        """Test validation with valid Slack configuration."""
        from pydantic import BaseModel

        class SlackConfig(BaseModel):
            enabled: bool = True
            webhook_url: str = "https://hooks.slack.com/test"
            format: str = "detailed"

        class NotificationConfig(BaseModel):
            slack: SlackConfig = SlackConfig()

        class Config(BaseModel):
            notifications: NotificationConfig = NotificationConfig()

        config = Config()

        webhook_url, format_type, is_valid, error = validate_slack_config(config)

        assert is_valid is True
        assert webhook_url == "https://hooks.slack.com/test"
        assert format_type == "detailed"
        assert error is None

    def test_validate_with_no_notifications(self):
        """Test validation when notifications config is missing."""
        config = Mock()
        del config.notifications

        webhook_url, format_type, is_valid, error = validate_slack_config(config)

        assert is_valid is False
        assert webhook_url is None
        assert format_type is None
        assert "not configured" in error

    def test_validate_with_disabled_slack(self):
        """Test validation when Slack is disabled."""
        config = Mock()
        config.notifications.slack.enabled = False

        webhook_url, format_type, is_valid, error = validate_slack_config(config)

        assert is_valid is False
        assert "disabled" in error

    def test_validate_with_missing_webhook_url(self):
        """Test validation when webhook URL is missing."""
        config = Mock()
        config.notifications.slack.enabled = True
        config.notifications.slack.webhook_url = ""

        webhook_url, format_type, is_valid, error = validate_slack_config(config)

        assert is_valid is False
        assert "webhook URL not configured" in error


class TestSendToSlack:
    """Test Slack notification sending."""

    def test_send_to_slack_success(self):
        """Test successful Slack notification."""
        config = Mock()
        config.notifications.slack.enabled = True
        config.notifications.slack.webhook_url = "https://hooks.slack.com/test"
        config.notifications.slack.format = "detailed"

        holdings = AccountHoldings(
            account_id="test",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("1000"),
            total_value=Decimal("1000"),
            positions=[],
        )

        with patch("src.notifications.slack.send_portfolio_update") as mock_send:
            mock_send.return_value = True
            result = send_to_slack(config, [holdings])

        assert result == 1
        mock_send.assert_called_once()

    def test_send_to_slack_invalid_config(self):
        """Test Slack notification with invalid config."""
        config = Mock()
        del config.notifications

        holdings = AccountHoldings(
            account_id="test",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("1000"),
            total_value=Decimal("1000"),
            positions=[],
        )

        result = send_to_slack(config, [holdings])

        assert result == -1

    def test_send_to_slack_partial_failure(self):
        """Test Slack notification with partial failure."""
        config = Mock()
        config.notifications.slack.enabled = True
        config.notifications.slack.webhook_url = "https://hooks.slack.com/test"
        config.notifications.slack.format = "detailed"

        holdings1 = AccountHoldings(
            account_id="account1",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("1000"),
            total_value=Decimal("1000"),
            positions=[],
        )

        holdings2 = AccountHoldings(
            account_id="account2",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("2000"),
            total_value=Decimal("2000"),
            positions=[],
        )

        with patch("src.notifications.slack.send_portfolio_update") as mock_send:
            # First succeeds, second fails
            mock_send.side_effect = [True, False]
            result = send_to_slack(config, [holdings1, holdings2])

        assert result == 1
        assert mock_send.call_count == 2

    def test_send_to_slack_exception_handling(self):
        """Test Slack notification handles exceptions."""
        config = Mock()
        config.notifications.slack.enabled = True
        config.notifications.slack.webhook_url = "https://hooks.slack.com/test"
        config.notifications.slack.format = "detailed"

        holdings = AccountHoldings(
            account_id="test",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("1000"),
            total_value=Decimal("1000"),
            positions=[],
        )

        with patch("src.notifications.slack.send_portfolio_update") as mock_send:
            mock_send.side_effect = Exception("Network error")
            result = send_to_slack(config, [holdings])

        assert result == 0
