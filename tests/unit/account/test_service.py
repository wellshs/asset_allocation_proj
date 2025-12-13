"""Unit tests for AccountService."""

from unittest.mock import Mock, patch
from decimal import Decimal


class TestAccountServiceGetHoldings:
    """Test AccountService.get_holdings()."""

    @patch("src.account.service.load_config")
    @patch("src.account.service.authenticate")
    @patch("src.account.service.get_provider")
    def test_get_holdings_success(self, mock_get_provider, mock_auth, mock_load_config):
        """Test successful holdings retrieval."""
        from src.account.service import AccountService
        from tests.fixtures.mock_portfolios import create_mock_holdings_with_positions

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
