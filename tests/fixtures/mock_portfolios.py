"""Mock portfolio data for testing."""

from datetime import datetime
from decimal import Decimal
from src.account.models import AccountHoldings, SecurityPosition, AssetType


def create_mock_holdings_with_positions() -> AccountHoldings:
    """Create mock holdings with multiple positions."""
    positions = [
        SecurityPosition(
            symbol="005930",
            name="삼성전자",
            quantity=Decimal("100"),
            average_price=Decimal("70000"),
            current_price=Decimal("71000"),
            current_value=Decimal("7100000"),
            asset_type=AssetType.STOCK,
            profit_loss=Decimal("100000"),
        ),
        SecurityPosition(
            symbol="035720",
            name="카카오",
            quantity=Decimal("50"),
            average_price=Decimal("48000"),
            current_price=Decimal("50000"),
            current_value=Decimal("2500000"),
            asset_type=AssetType.STOCK,
            profit_loss=Decimal("100000"),
        ),
    ]

    return AccountHoldings(
        account_id="test_account",
        timestamp=datetime.now(),
        cash_balance=Decimal("1000000"),
        positions=positions,
        total_value=Decimal("10600000"),
    )


def create_mock_holdings_empty() -> AccountHoldings:
    """Create mock holdings with no positions (cash only)."""
    return AccountHoldings(
        account_id="test_account",
        timestamp=datetime.now(),
        cash_balance=Decimal("1000000"),
        positions=[],
        total_value=Decimal("1000000"),
    )
