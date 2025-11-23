"""Unit tests for portfolio state management."""

from datetime import date
from decimal import Decimal

from src.models.portfolio_state import PortfolioState


class TestPortfolioState:
    """Tests for PortfolioState dataclass."""

    def test_total_value_calculation(self):
        """Test that total_value correctly sums cash and holdings."""
        state = PortfolioState(
            timestamp=date(2020, 1, 1),
            cash_balance=Decimal("10000"),
            asset_holdings={"SPY": Decimal("10"), "AGG": Decimal("20")},
            current_prices={"SPY": Decimal("300"), "AGG": Decimal("100")},
        )

        # Expected: 10000 + (10 * 300) + (20 * 100) = 10000 + 3000 + 2000 = 15000
        assert state.total_value == Decimal("15000")

    def test_total_value_with_zero_cash(self):
        """Test total_value when cash balance is zero."""
        state = PortfolioState(
            timestamp=date(2020, 1, 1),
            cash_balance=Decimal("0"),
            asset_holdings={"SPY": Decimal("10")},
            current_prices={"SPY": Decimal("300")},
        )

        assert state.total_value == Decimal("3000")

    def test_get_current_weights(self):
        """Test current weight calculation."""
        state = PortfolioState(
            timestamp=date(2020, 1, 1),
            cash_balance=Decimal("0"),
            asset_holdings={"SPY": Decimal("10"), "AGG": Decimal("20")},
            current_prices={"SPY": Decimal("300"), "AGG": Decimal("100")},
        )

        weights = state.get_current_weights()

        # Expected weights: SPY = 3000/5000 = 0.6, AGG = 2000/5000 = 0.4
        assert weights["SPY"] == Decimal("0.6")
        assert weights["AGG"] == Decimal("0.4")

    def test_get_current_weights_with_zero_total(self):
        """Test weight calculation when portfolio value is zero."""
        state = PortfolioState(
            timestamp=date(2020, 1, 1),
            cash_balance=Decimal("0"),
            asset_holdings={},
            current_prices={},
        )

        weights = state.get_current_weights()
        assert weights == {}

    def test_fractional_shares(self):
        """Test that fractional shares are supported."""
        state = PortfolioState(
            timestamp=date(2020, 1, 1),
            cash_balance=Decimal("1000"),
            asset_holdings={"SPY": Decimal("10.567890")},
            current_prices={"SPY": Decimal("300.1234")},
        )

        # Should handle 6 decimal places for quantity
        expected_value = Decimal("1000") + Decimal("10.567890") * Decimal("300.1234")
        assert state.total_value == expected_value
