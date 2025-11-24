"""Unit tests for Korea Investment & Securities provider."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
import json


class TestKoreaInvestmentAuthentication:
    """Test KoreaInvestmentProvider.authenticate()."""

    @patch("requests.post")
    def test_authenticate_success(self, mock_post):
        """Test successful authentication."""
        from src.account.providers.korea_investment import KoreaInvestmentProvider
        from src.account.models import BrokerageAccount, AccountStatus
        from src.account.config import AccountCredentials

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token_123",
            "token_type": "Bearer",
            "expires_in": 86400,
        }
        mock_post.return_value = mock_response

        provider = KoreaInvestmentProvider()
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

        result = provider.authenticate(account, credentials)

        assert result.status == AccountStatus.CONNECTED
        assert result.access_token == "test_token_123"
        assert result.token_expiry is not None

    @patch("requests.post")
    def test_authenticate_failure(self, mock_post):
        """Test authentication failure."""
        from src.account.providers.korea_investment import KoreaInvestmentProvider
        from src.account.models import BrokerageAccount, AccountStatus
        from src.account.config import AccountCredentials
        from src.account.exceptions import AccountAuthException

        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid credentials"}
        mock_post.return_value = mock_response

        provider = KoreaInvestmentProvider()
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

        with pytest.raises(AccountAuthException):
            provider.authenticate(account, credentials)


class TestKoreaInvestmentFetchHoldings:
    """Test KoreaInvestmentProvider.fetch_holdings()."""

    @patch("requests.get")
    def test_fetch_holdings_with_positions(self, mock_get):
        """Test fetching holdings with multiple positions."""
        from src.account.providers.korea_investment import KoreaInvestmentProvider
        from src.account.models import BrokerageAccount, AccountStatus

        # Load mock response
        with open("tests/fixtures/mock_korea_investment_responses.json") as f:
            mock_data = json.load(f)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data["holdings_with_positions"]
        mock_get.return_value = mock_response

        provider = KoreaInvestmentProvider()
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="test_token",
            token_expiry=datetime.now() + timedelta(hours=1),
        )

        holdings = provider.fetch_holdings(account)

        assert holdings.account_id == "test"
        assert holdings.cash_balance == Decimal("1000000")
        assert len(holdings.positions) == 2
        assert holdings.positions[0].symbol == "005930"
        assert holdings.positions[0].name == "삼성전자"

    @patch("requests.get")
    def test_fetch_holdings_empty(self, mock_get):
        """Test fetching holdings with no positions."""
        from src.account.providers.korea_investment import KoreaInvestmentProvider
        from src.account.models import BrokerageAccount, AccountStatus

        with open("tests/fixtures/mock_korea_investment_responses.json") as f:
            mock_data = json.load(f)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data["holdings_no_positions"]
        mock_get.return_value = mock_response

        provider = KoreaInvestmentProvider()
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="test_token",
            token_expiry=datetime.now() + timedelta(hours=1),
        )

        holdings = provider.fetch_holdings(account)

        assert holdings.cash_balance == Decimal("1000000")
        assert len(holdings.positions) == 0


class TestAPIResponseParsing:
    """Test _parse_holdings_response helper."""

    def test_parse_holdings_response(self):
        """Test parsing API response to AccountHoldings."""
        from src.account.providers.korea_investment import KoreaInvestmentProvider

        with open("tests/fixtures/mock_korea_investment_responses.json") as f:
            mock_data = json.load(f)

        provider = KoreaInvestmentProvider()
        holdings = provider._parse_holdings_response(
            "test_account", mock_data["holdings_with_positions"]
        )

        assert holdings.cash_balance == Decimal("1000000")
        assert len(holdings.positions) == 2
        assert holdings.positions[0].current_price == Decimal("71000")


class TestErrorHandling:
    """Test error handling for network and API errors."""

    @patch("requests.get")
    def test_network_timeout(self, mock_get):
        """Test handling of network timeout."""
        from src.account.providers.korea_investment import KoreaInvestmentProvider
        from src.account.models import BrokerageAccount, AccountStatus
        from src.account.exceptions import AccountAPIException
        import requests

        mock_get.side_effect = requests.Timeout("Connection timeout")

        provider = KoreaInvestmentProvider()
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="test_token",
            token_expiry=datetime.now() + timedelta(hours=1),
        )

        with pytest.raises(AccountAPIException):
            provider.fetch_holdings(account)

    @patch("requests.get")
    def test_server_error_500(self, mock_get):
        """Test handling of 500 server error."""
        from src.account.providers.korea_investment import KoreaInvestmentProvider
        from src.account.models import BrokerageAccount, AccountStatus
        from src.account.exceptions import AccountAPIException

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        provider = KoreaInvestmentProvider()
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="test_token",
            token_expiry=datetime.now() + timedelta(hours=1),
        )

        with pytest.raises(AccountAPIException):
            provider.fetch_holdings(account)


class TestRateLimitingIntegration:
    """Test rate limiting integration."""

    @patch("requests.get")
    def test_rate_limiting_enforced(self, mock_get):
        """Test that rate limiting is enforced between requests."""
        from src.account.providers.korea_investment import KoreaInvestmentProvider
        from src.account.models import BrokerageAccount, AccountStatus
        import time

        with open("tests/fixtures/mock_korea_investment_responses.json") as f:
            mock_data = json.load(f)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data["holdings_with_positions"]
        mock_get.return_value = mock_response

        provider = KoreaInvestmentProvider()
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="test_token",
            token_expiry=datetime.now() + timedelta(hours=1),
        )

        # First request should be fast
        start = time.time()
        provider.fetch_holdings(account)
        first_duration = time.time() - start

        # Second request should include rate limit delay
        start = time.time()
        provider.fetch_holdings(account)
        second_duration = time.time() - start

        # Second request should take at least 1 second longer
        assert second_duration > first_duration + 0.5
