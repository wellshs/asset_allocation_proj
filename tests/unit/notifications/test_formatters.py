"""Unit tests for notification formatters."""

from decimal import Decimal
from datetime import datetime, timezone

from src.notifications.formatters import (
    PortfolioFormatter,
    format_krw,
    format_usd,
)
from src.account.models import AccountHoldings, SecurityPosition, AssetType


class TestFormatHelpers:
    """Test format helper functions."""

    def test_format_krw(self):
        """Test KRW formatting."""
        amount = Decimal("1234567.89")
        result = format_krw(amount)

        assert result == "₩1,234,568"  # Rounded up

    def test_format_usd(self):
        """Test USD formatting."""
        amount = Decimal("1234.567")
        result = format_usd(amount)

        assert result == "$1,234.57"  # Rounded up

    def test_format_krw_rounds_half_up(self):
        """Test KRW rounding behavior."""
        amount = Decimal("1000.5")
        result = format_krw(amount)

        assert result == "₩1,001"

    def test_format_usd_rounds_half_up(self):
        """Test USD rounding behavior."""
        amount = Decimal("10.005")
        result = format_usd(amount)

        assert result == "$10.01"


class TestPortfolioFormatterDetailed:
    """Test detailed portfolio formatting."""

    def test_format_detailed_with_currency_breakdown(self):
        """Test detailed format with USD/KRW breakdown."""
        holdings = AccountHoldings(
            account_id="test_account",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("30000000"),
            krw_cash_balance=Decimal("10000000"),
            usd_cash_balance=Decimal("15000"),
            exchange_rate=Decimal("1333.33"),
            total_value=Decimal("30000000"),
            positions=[],
        )

        result = PortfolioFormatter.format_detailed(holdings)

        assert "text" in result
        assert "blocks" in result
        assert "test_account" in result["text"]

        # Check blocks contain currency breakdown
        block_text = str(result["blocks"])
        assert "KRW:" in block_text
        assert "USD:" in block_text
        assert "Total:" in block_text

    def test_format_detailed_without_currency_breakdown(self):
        """Test detailed format without currency breakdown."""
        holdings = AccountHoldings(
            account_id="test_account",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("10000000"),
            total_value=Decimal("10000000"),
            positions=[],
        )

        result = PortfolioFormatter.format_detailed(holdings)

        assert "text" in result
        assert "blocks" in result

        # Should still show cash balance
        block_text = str(result["blocks"])
        assert "Cash Balance" in block_text

    def test_format_detailed_with_positions(self):
        """Test detailed format with positions."""
        position = SecurityPosition(
            symbol="AAPL",
            name="Apple Inc.",
            quantity=Decimal("10"),
            average_price=Decimal("150000"),
            current_price=Decimal("160000"),
            current_value=Decimal("1600000"),
            asset_type=AssetType.STOCK,
            profit_loss=Decimal("100000"),
        )

        holdings = AccountHoldings(
            account_id="test_account",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("10000000"),
            total_value=Decimal("11600000"),
            positions=[position],
        )

        result = PortfolioFormatter.format_detailed(holdings)

        block_text = str(result["blocks"])
        assert "Apple Inc." in block_text
        assert "AAPL" in block_text

    def test_format_detailed_limits_to_top_10(self):
        """Test detailed format limits positions to top 10."""
        positions = [
            SecurityPosition(
                symbol=f"STOCK{i}",
                name=f"Stock {i}",
                quantity=Decimal("10"),
                average_price=Decimal("100"),
                current_price=Decimal("100"),
                current_value=Decimal("1000"),
                asset_type=AssetType.STOCK,
            )
            for i in range(15)
        ]

        holdings = AccountHoldings(
            account_id="test_account",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("10000000"),
            total_value=Decimal("10015000"),
            positions=positions,
        )

        result = PortfolioFormatter.format_detailed(holdings)

        block_text = str(result["blocks"])
        # Should mention there are more holdings
        assert "5 more" in block_text


class TestPortfolioFormatterSummary:
    """Test summary portfolio formatting."""

    def test_format_summary_with_currency_breakdown(self):
        """Test summary format with USD/KRW breakdown."""
        holdings = AccountHoldings(
            account_id="test_account",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("30000000"),
            krw_cash_balance=Decimal("10000000"),
            usd_cash_balance=Decimal("15000"),
            exchange_rate=Decimal("1333.33"),
            total_value=Decimal("30000000"),
            positions=[],
        )

        result = PortfolioFormatter.format_summary(holdings)

        assert "text" in result
        assert "blocks" in result

        block_text = str(result["blocks"])
        assert "KRW:" in block_text
        assert "USD:" in block_text

    def test_format_summary_without_currency_breakdown(self):
        """Test summary format without currency breakdown."""
        holdings = AccountHoldings(
            account_id="test_account",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("10000000"),
            total_value=Decimal("10000000"),
            positions=[],
        )

        result = PortfolioFormatter.format_summary(holdings)

        assert "text" in result
        assert "blocks" in result

    def test_format_summary_shows_top_10(self):
        """Test summary format shows top 10 positions."""
        positions = [
            SecurityPosition(
                symbol=f"STOCK{i}",
                name=f"Stock {i}",
                quantity=Decimal("10"),
                average_price=Decimal("100"),
                current_price=Decimal("100"),
                current_value=Decimal("1000"),
                asset_type=AssetType.STOCK,
            )
            for i in range(15)
        ]

        holdings = AccountHoldings(
            account_id="test_account",
            timestamp=datetime.now(timezone.utc),
            cash_balance=Decimal("10000000"),
            total_value=Decimal("10015000"),
            positions=positions,
        )

        result = PortfolioFormatter.format_summary(holdings)

        block_text = str(result["blocks"])
        assert "5 more" in block_text
