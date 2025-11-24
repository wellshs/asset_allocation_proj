"""Unit tests for authentication module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


class TestAuthentication:
    """Test authentication functions."""

    def test_authenticate_success(self):
        """Test successful authentication."""
        from src.account.auth import authenticate
        from src.account.models import BrokerageAccount, AccountStatus
        from src.account.config import AccountCredentials

        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.DISCONNECTED,
        )

        credentials = AccountCredentials(
            app_key="test_key",
            app_secret="test_secret",
            account_number="1234567890",
        )

        # Mock the provider authentication
        with patch("src.account.auth.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.authenticate.return_value = BrokerageAccount(
                account_id="test",
                provider="korea_investment",
                account_number="1234567890",
                status=AccountStatus.CONNECTED,
                access_token="mock_token",
                token_expiry=datetime.now() + timedelta(hours=24),
            )
            mock_get_provider.return_value = mock_provider

            result = authenticate(account, credentials)

            assert result.status == AccountStatus.CONNECTED
            assert result.access_token == "mock_token"
            assert result.token_expiry is not None

    def test_authenticate_failure(self):
        """Test authentication failure with invalid credentials."""
        from src.account.auth import authenticate
        from src.account.models import BrokerageAccount, AccountStatus
        from src.account.config import AccountCredentials
        from src.account.exceptions import AccountAuthException

        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.DISCONNECTED,
        )

        credentials = AccountCredentials(
            app_key="invalid_key",
            app_secret="invalid_secret",
            account_number="1234567890",
        )

        with patch("src.account.auth.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.authenticate.side_effect = AccountAuthException(
                "Invalid credentials"
            )
            mock_get_provider.return_value = mock_provider

            with pytest.raises(AccountAuthException):
                authenticate(account, credentials)


class TestTokenExpiry:
    """Test token expiry checking."""

    def test_check_token_expiry_valid(self):
        """Test check_token_expiry with valid token."""
        from src.account.auth import check_token_expiry
        from src.account.models import BrokerageAccount, AccountStatus

        future_time = datetime.now() + timedelta(hours=1)
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="valid_token",
            token_expiry=future_time,
        )

        result = check_token_expiry(account)
        assert result is True

    def test_check_token_expiry_expired(self):
        """Test check_token_expiry with expired token."""
        from src.account.auth import check_token_expiry
        from src.account.models import BrokerageAccount, AccountStatus

        past_time = datetime.now() - timedelta(hours=1)
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="expired_token",
            token_expiry=past_time,
        )

        result = check_token_expiry(account)
        assert result is False


class TestAutoReauthentication:
    """Test automatic re-authentication."""

    def test_refresh_token_success(self):
        """Test successful token refresh."""
        from src.account.auth import refresh_token
        from src.account.models import BrokerageAccount, AccountStatus
        from src.account.config import AccountCredentials

        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="old_token",
            token_expiry=datetime.now() - timedelta(hours=1),
        )

        credentials = AccountCredentials(
            app_key="test_key",
            app_secret="test_secret",
            account_number="1234567890",
        )

        with patch("src.account.auth.authenticate") as mock_authenticate:
            mock_authenticate.return_value = BrokerageAccount(
                account_id="test",
                provider="korea_investment",
                account_number="1234567890",
                status=AccountStatus.CONNECTED,
                access_token="new_token",
                token_expiry=datetime.now() + timedelta(hours=24),
            )

            result = refresh_token(account, credentials)

            assert result.access_token == "new_token"
            assert result.token_expiry > datetime.now()
