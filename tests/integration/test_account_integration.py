"""Integration tests for account operations."""

from unittest.mock import patch, Mock
from datetime import datetime, timedelta, timezone


class TestEndToEndAuthenticationAndFetch:
    """Test end-to-end authentication and holdings fetch."""

    @patch("requests.post")
    @patch("requests.get")
    def test_authenticate_and_fetch_holdings(self, mock_get, mock_post):
        """Test complete flow: authenticate then fetch holdings."""
        from src.account.auth import authenticate, get_provider
        from src.account.models import BrokerageAccount, AccountStatus
        from src.account.config import AccountCredentials
        import json

        # Mock authentication
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "access_token": "test_token",
                "expires_in": 86400,
            },
        )

        # Mock holdings (domestic + overseas)
        with open("tests/fixtures/mock_korea_investment_responses.json") as f:
            mock_data = json.load(f)

        # Mock domestic and overseas responses
        mock_domestic = Mock(
            status_code=200, json=lambda: mock_data["holdings_with_positions"]
        )
        mock_overseas = Mock(
            status_code=200,
            json=lambda: mock_data["overseas_holdings_with_positions"],
        )
        mock_get.side_effect = [mock_domestic, mock_overseas]

        # Create account
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

        # Authenticate
        account = authenticate(account, credentials)
        assert account.is_authenticated()

        # Fetch holdings
        provider = get_provider("korea_investment")
        holdings = provider.fetch_holdings(account, credentials)

        assert holdings.cash_balance > 0
        assert len(holdings.positions) > 0


class TestTokenRefreshOnExpiry:
    """Test automatic token refresh."""

    @patch("src.account.auth.authenticate")
    def test_token_refresh_when_expired(self, mock_authenticate):
        """Test that expired tokens trigger re-authentication."""
        from src.account.auth import refresh_token
        from src.account.models import BrokerageAccount, AccountStatus
        from src.account.config import AccountCredentials

        # Create expired account
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="expired_token",
            token_expiry=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        credentials = AccountCredentials(
            app_key="test_key",
            app_secret="test_secret",
            account_number="1234567890",
        )

        # Mock re-authentication
        mock_authenticate.return_value = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="new_token",
            token_expiry=datetime.now(timezone.utc) + timedelta(hours=24),
        )

        refreshed = refresh_token(account, credentials)

        assert refreshed.access_token == "new_token"
        assert refreshed.is_authenticated()


class TestRetryOnTransientFailure:
    """Test retry logic for transient failures."""

    @patch("requests.get")
    def test_retry_on_500_error(self, mock_get):
        """Test that 500 errors are retried."""
        from src.account.providers.korea_investment import KoreaInvestmentProvider
        from src.account.models import BrokerageAccount, AccountStatus
        from src.account.config import AccountCredentials

        # First two domestic calls fail, third succeeds, then overseas succeeds
        import json

        with open("tests/fixtures/mock_korea_investment_responses.json") as f:
            mock_data = json.load(f)

        mock_get.side_effect = [
            Mock(status_code=500, text="Server Error"),  # Domestic fail 1
            Mock(status_code=500, text="Server Error"),  # Domestic fail 2
            Mock(
                status_code=200, json=lambda: mock_data["holdings_with_positions"]
            ),  # Domestic success
            Mock(
                status_code=200,
                json=lambda: mock_data["overseas_holdings_with_positions"],
            ),  # Overseas success
        ]

        provider = KoreaInvestmentProvider()
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="test_token",
            token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        credentials = AccountCredentials(
            app_key="test_key",
            app_secret="test_secret",
            account_number="1234567890",
        )

        holdings = provider.fetch_holdings(account, credentials)
        assert holdings is not None
        assert mock_get.call_count == 4  # 3 domestic (2 fail + 1 success) + 1 overseas
