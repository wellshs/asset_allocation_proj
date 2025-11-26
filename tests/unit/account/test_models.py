"""Unit tests for account data models."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal


class TestBrokerageAccount:
    """Test BrokerageAccount entity."""

    def test_brokerage_account_creation(self):
        """Test creating a BrokerageAccount instance."""
        from src.account.models import BrokerageAccount, AccountStatus

        account = BrokerageAccount(
            account_id="test_account",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.DISCONNECTED,
        )

        assert account.account_id == "test_account"
        assert account.provider == "korea_investment"
        assert account.status == AccountStatus.DISCONNECTED
        assert account.access_token is None
        assert account.token_expiry is None

    def test_is_authenticated_with_valid_token(self):
        """Test is_authenticated returns True for valid token."""
        from src.account.models import BrokerageAccount, AccountStatus

        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="valid_token",
            token_expiry=future_time,
        )

        assert account.is_authenticated() is True

    def test_is_authenticated_with_expired_token(self):
        """Test is_authenticated returns False for expired token."""
        from src.account.models import BrokerageAccount, AccountStatus

        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.CONNECTED,
            access_token="expired_token",
            token_expiry=past_time,
        )

        assert account.is_authenticated() is False

    def test_is_authenticated_disconnected_status(self):
        """Test is_authenticated returns False when disconnected."""
        from src.account.models import BrokerageAccount, AccountStatus

        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        account = BrokerageAccount(
            account_id="test",
            provider="korea_investment",
            account_number="1234567890",
            status=AccountStatus.DISCONNECTED,
            access_token="token",
            token_expiry=future_time,
        )

        assert account.is_authenticated() is False


class TestAccountHoldings:
    """Test AccountHoldings entity."""

    def test_account_holdings_creation(self):
        """Test creating AccountHoldings instance."""
        from src.account.models import AccountHoldings, SecurityPosition

        positions = [
            SecurityPosition(
                symbol="005930",
                name="Samsung Electronics",
                quantity=Decimal("100"),
                average_price=Decimal("70000"),
                current_price=Decimal("71000"),
                current_value=Decimal("7100000"),
            )
        ]

        holdings = AccountHoldings(
            account_id="test",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("1000000"),
            positions=positions,
            total_value=Decimal("8100000"),
        )

        assert holdings.account_id == "test"
        assert holdings.cash_balance == Decimal("1000000")
        assert len(holdings.positions) == 1
        assert holdings.total_value == Decimal("8100000")

    def test_account_holdings_empty_positions(self):
        """Test AccountHoldings with no positions (cash only)."""
        from src.account.models import AccountHoldings

        holdings = AccountHoldings(
            account_id="test",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("5000000"),
            positions=[],
            total_value=Decimal("5000000"),
        )

        assert len(holdings.positions) == 0
        assert holdings.cash_balance == holdings.total_value


class TestSecurityPosition:
    """Test SecurityPosition entity."""

    def test_security_position_creation(self):
        """Test creating a SecurityPosition."""
        from src.account.models import SecurityPosition, AssetType

        position = SecurityPosition(
            symbol="005930",
            name="Samsung Electronics",
            quantity=Decimal("100"),
            average_price=Decimal("70000"),
            current_price=Decimal("71000"),
            current_value=Decimal("7100000"),
            asset_type=AssetType.STOCK,
        )

        assert position.symbol == "005930"
        assert position.name == "Samsung Electronics"
        assert position.quantity == Decimal("100")
        assert position.current_price == Decimal("71000")
        assert position.asset_type == AssetType.STOCK

    def test_security_position_profit_loss(self):
        """Test calculating profit/loss for a position."""
        from src.account.models import SecurityPosition

        position = SecurityPosition(
            symbol="035720",
            name="Kakao",
            quantity=Decimal("50"),
            average_price=Decimal("48000"),
            current_price=Decimal("50000"),
            current_value=Decimal("2500000"),
            profit_loss=Decimal("100000"),
        )

        assert position.profit_loss == Decimal("100000")

    def test_security_position_non_standard_asset(self):
        """Test SecurityPosition for non-standard assets."""
        from src.account.models import SecurityPosition, AssetType

        position = SecurityPosition(
            symbol="OPTION123",
            name="Option Contract",
            quantity=Decimal("10"),
            average_price=Decimal("5000"),
            current_price=Decimal("5500"),
            current_value=Decimal("55000"),
            asset_type=AssetType.OPTION,
        )

        assert position.asset_type == AssetType.OPTION
        assert position.symbol == "OPTION123"


class TestAccountHoldingsConversion:
    """Test AccountHoldings.to_portfolio_state() conversion."""

    def test_to_portfolio_state_conversion(self):
        """Test converting AccountHoldings to PortfolioState."""
        from src.account.models import AccountHoldings, SecurityPosition

        positions = [
            SecurityPosition(
                symbol="005930",
                name="Samsung Electronics",
                quantity=Decimal("100"),
                average_price=Decimal("70000"),
                current_price=Decimal("71000"),
                current_value=Decimal("7100000"),
            ),
            SecurityPosition(
                symbol="035720",
                name="Kakao",
                quantity=Decimal("50"),
                average_price=Decimal("48000"),
                current_price=Decimal("50000"),
                current_value=Decimal("2500000"),
            ),
        ]

        holdings = AccountHoldings(
            account_id="test",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("1000000"),
            positions=positions,
            total_value=Decimal("10600000"),
        )

        portfolio_state = holdings.to_portfolio_state()

        # Check that conversion maintains data fidelity
        assert portfolio_state.cash_balance == Decimal("1000000")
        assert len(portfolio_state.asset_holdings) == 2
        assert "005930" in portfolio_state.asset_holdings
        assert "035720" in portfolio_state.asset_holdings
        assert portfolio_state.current_prices["005930"] == Decimal("71000")
        assert portfolio_state.current_prices["035720"] == Decimal("50000")

    def test_to_portfolio_state_empty_positions(self):
        """Test conversion with no positions."""
        from src.account.models import AccountHoldings

        holdings = AccountHoldings(
            account_id="test",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("5000000"),
            positions=[],
            total_value=Decimal("5000000"),
        )

        portfolio_state = holdings.to_portfolio_state()

        assert portfolio_state.cash_balance == Decimal("5000000")
        assert len(portfolio_state.asset_holdings) == 0
