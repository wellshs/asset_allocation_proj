"""Unit tests for AccountService."""

from unittest.mock import Mock, patch
from decimal import Decimal


class TestAccountServiceGetHoldings:
    """Test AccountService.get_holdings()."""

    @patch("src.account.service.TokenCache")
    @patch("src.account.service.load_config")
    @patch("src.account.service.authenticate")
    @patch("src.account.service.get_provider")
    def test_get_holdings_success(
        self, mock_get_provider, mock_auth, mock_load_config, mock_token_cache
    ):
        """Test successful holdings retrieval."""
        from src.account.service import AccountService
        from tests.fixtures.mock_portfolios import create_mock_holdings_with_positions

        # Mock token cache
        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = None  # No cached token
        mock_token_cache.return_value = mock_cache_instance

        # Mock config
        mock_config = Mock()
        mock_account = Mock()
        mock_account.name = "Test Account"
        mock_account.enabled = True
        mock_account.provider = "korea_investment"
        mock_account.credentials = Mock()
        mock_account.credentials.account_number = "1234567890"
        mock_config.accounts = [mock_account]
        mock_load_config.return_value = mock_config

        # Mock authentication
        mock_authenticated = Mock()
        mock_authenticated.is_authenticated.return_value = True
        mock_auth.return_value = mock_authenticated

        # Mock provider
        mock_provider = Mock()
        mock_provider.fetch_holdings.return_value = (
            create_mock_holdings_with_positions()
        )
        mock_get_provider.return_value = mock_provider

        service = AccountService("config.yaml")
        holdings = service.get_holdings("Test Account")

        assert holdings.cash_balance == Decimal("1000000")
        assert len(holdings.positions) == 2

    @patch("src.account.service.TokenCache")
    @patch("src.account.service.load_config")
    @patch("src.account.service.authenticate")
    @patch("src.account.service.get_provider")
    def test_account_number_changed_in_config(
        self, mock_get_provider, mock_auth, mock_load_config, mock_token_cache
    ):
        """Test that account number changes in config are detected and handled."""
        from src.account.service import AccountService
        from src.account.models import BrokerageAccount, AccountStatus
        from tests.fixtures.mock_portfolios import create_mock_holdings_with_positions

        # Mock cached account with old account number
        old_account = BrokerageAccount(
            account_id="Test Account",
            provider="korea_investment",
            account_number="0000000000",  # Old account number
            status=AccountStatus.CONNECTED,
            access_token="old_token",
        )
        old_account.token_expiry = None  # Make it appear expired

        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = old_account
        mock_token_cache.return_value = mock_cache_instance

        # Mock config with new account number
        mock_config = Mock()
        mock_account = Mock()
        mock_account.name = "Test Account"
        mock_account.enabled = True
        mock_account.provider = "korea_investment"
        mock_account.credentials = Mock()
        mock_account.credentials.account_number = "1234567890"  # New account number
        mock_config.accounts = [mock_account]
        mock_load_config.return_value = mock_config

        # Mock authentication
        mock_authenticated = BrokerageAccount(
            account_id="Test Account",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="new_token",
        )
        mock_authenticated.token_expiry = None
        mock_auth.return_value = mock_authenticated

        # Mock provider
        mock_provider = Mock()
        mock_provider.fetch_holdings.return_value = (
            create_mock_holdings_with_positions()
        )
        mock_get_provider.return_value = mock_provider

        service = AccountService("config.yaml")
        holdings = service.get_holdings("Test Account")

        # Verify cache was cleared for old account number
        mock_cache_instance.remove.assert_called_once_with("Test Account")

        # Verify re-authentication was triggered
        mock_auth.assert_called_once()

        # Verify holdings were fetched successfully
        assert holdings.cash_balance == Decimal("1000000")


class TestIncompleteDataHandling:
    """Test handling of incomplete data."""

    def test_detect_warnings_missing_price(self):
        """Test warning detection for missing price data."""
        from src.account.service import AccountService
        from src.account.models import AccountHoldings, SecurityPosition
        from datetime import datetime, timezone

        service = AccountService.__new__(AccountService)

        position = SecurityPosition(
            symbol="TEST",
            name="Test",
            quantity=Decimal("100"),
            average_price=Decimal("1000"),
            current_price=Decimal("0"),  # Missing price
            current_value=Decimal("0"),
        )

        holdings = AccountHoldings(
            account_id="test",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("1000000"),
            positions=[position],
            total_value=Decimal("1000000"),
        )

        service._detect_warnings(holdings)
        assert holdings.positions[0].has_warning is True


class TestNonStandardAssetHandling:
    """Test handling of non-standard assets."""

    def test_non_standard_assets_displayed(self):
        """Test that non-standard assets are included in holdings."""
        from src.account.models import AccountHoldings, SecurityPosition, AssetType
        from datetime import datetime, timezone

        position = SecurityPosition(
            symbol="OPTION123",
            name="Option Contract",
            quantity=Decimal("10"),
            average_price=Decimal("5000"),
            current_price=Decimal("5500"),
            current_value=Decimal("55000"),
            asset_type=AssetType.OPTION,
        )

        holdings = AccountHoldings(
            account_id="test",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("1000000"),
            positions=[position],
            total_value=Decimal("1055000"),
        )

        assert holdings.positions[0].asset_type == AssetType.OPTION
        assert holdings.positions[0].symbol == "OPTION123"


class TestConsolidateHoldings:
    """Test holdings consolidation."""

    def test_consolidate_holdings_preserves_currency_info(self):
        """Test that consolidation preserves USD/KRW breakdown."""
        from src.account.service import AccountService
        from src.account.models import AccountHoldings
        from datetime import datetime, timezone

        service = AccountService.__new__(AccountService)

        # Domestic account (KRW only)
        domestic = AccountHoldings(
            account_id="domestic",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("10000000"),
            krw_cash_balance=Decimal("10000000"),
            usd_cash_balance=Decimal("0"),
            exchange_rate=None,
            total_value=Decimal("10000000"),
            positions=[],
        )

        # Overseas account (USD + KRW)
        overseas = AccountHoldings(
            account_id="overseas",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("20000000"),
            krw_cash_balance=Decimal("5000000"),
            usd_cash_balance=Decimal("10000"),
            exchange_rate=Decimal("1500"),
            total_value=Decimal("20000000"),
            positions=[],
        )

        consolidated = service.consolidate_holdings(
            {"domestic": domestic, "overseas": overseas}
        )

        assert consolidated.cash_balance == Decimal("30000000")
        assert consolidated.krw_cash_balance == Decimal("15000000")
        assert consolidated.usd_cash_balance == Decimal("10000")
        assert consolidated.exchange_rate == Decimal("1500")

    def test_consolidate_holdings_weighted_exchange_rate(self):
        """Test weighted average exchange rate calculation."""
        from src.account.service import AccountService
        from src.account.models import AccountHoldings
        from datetime import datetime, timezone

        service = AccountService.__new__(AccountService)

        # Account 1: $10,000 @ 1400
        account1 = AccountHoldings(
            account_id="account1",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("14000000"),
            krw_cash_balance=Decimal("0"),
            usd_cash_balance=Decimal("10000"),
            exchange_rate=Decimal("1400"),
            total_value=Decimal("14000000"),
            positions=[],
        )

        # Account 2: $20,000 @ 1500
        account2 = AccountHoldings(
            account_id="account2",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("30000000"),
            krw_cash_balance=Decimal("0"),
            usd_cash_balance=Decimal("20000"),
            exchange_rate=Decimal("1500"),
            total_value=Decimal("30000000"),
            positions=[],
        )

        consolidated = service.consolidate_holdings(
            {"account1": account1, "account2": account2}
        )

        # Weighted average: (10000*1400 + 20000*1500) / 30000 = 1466.67
        expected_rate = Decimal("1466.666666666666666666666667")
        assert consolidated.exchange_rate.quantize(
            Decimal("0.01")
        ) == expected_rate.quantize(Decimal("0.01"))
        assert consolidated.usd_cash_balance == Decimal("30000")

    def test_consolidate_holdings_no_usd(self):
        """Test consolidation with no USD holdings."""
        from src.account.service import AccountService
        from src.account.models import AccountHoldings
        from datetime import datetime, timezone

        service = AccountService.__new__(AccountService)

        # KRW-only accounts
        account1 = AccountHoldings(
            account_id="account1",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("10000000"),
            total_value=Decimal("10000000"),
            positions=[],
        )

        account2 = AccountHoldings(
            account_id="account2",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("20000000"),
            total_value=Decimal("20000000"),
            positions=[],
        )

        consolidated = service.consolidate_holdings(
            {"account1": account1, "account2": account2}
        )

        assert consolidated.cash_balance == Decimal("30000000")
        assert consolidated.krw_cash_balance is None
        assert consolidated.usd_cash_balance is None
        assert consolidated.exchange_rate is None
