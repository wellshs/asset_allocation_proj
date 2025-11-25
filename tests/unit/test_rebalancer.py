"""Unit tests for rebalancing logic."""

from datetime import date
from decimal import Decimal

from src.models import RebalancingFrequency
from src.backtesting.rebalancer import (
    generate_rebalancing_dates,
    calculate_rebalancing_trades,
)
from src.models.portfolio_state import PortfolioState


class TestRebalancingDates:
    """Tests for rebalancing date generation."""

    def test_quarterly_rebalancing_dates(self):
        """Test quarterly rebalancing date generation."""
        start_date = date(2020, 1, 1)
        end_date = date(2020, 12, 31)

        dates = generate_rebalancing_dates(
            start_date, end_date, RebalancingFrequency.QUARTERLY
        )

        # Should have Q1, Q2, Q3, Q4
        assert len(dates) >= 4
        # First date should be start date
        assert dates[0] == start_date

    def test_monthly_rebalancing_dates(self):
        """Test monthly rebalancing date generation."""
        start_date = date(2020, 1, 1)
        end_date = date(2020, 6, 30)

        dates = generate_rebalancing_dates(
            start_date, end_date, RebalancingFrequency.MONTHLY
        )

        # Should have 6 months
        assert len(dates) >= 6

    def test_annually_rebalancing_dates(self):
        """Test annual rebalancing date generation."""
        start_date = date(2018, 1, 1)
        end_date = date(2020, 12, 31)

        dates = generate_rebalancing_dates(
            start_date, end_date, RebalancingFrequency.ANNUALLY
        )

        # Should have 3 years: 2018, 2019, 2020
        assert len(dates) >= 3

    def test_never_rebalancing(self):
        """Test that NEVER frequency returns empty list."""
        start_date = date(2020, 1, 1)
        end_date = date(2020, 12, 31)

        dates = generate_rebalancing_dates(
            start_date, end_date, RebalancingFrequency.NEVER
        )

        # Should return empty list (no rebalancing)
        assert dates == []


class TestRebalancingTrades:
    """Tests for rebalancing trade calculations."""

    def test_calculate_rebalancing_trades(self):
        """Test trade calculation to rebalance portfolio."""
        # Current portfolio: 70% SPY, 30% AGG
        current_state = PortfolioState(
            timestamp=date(2020, 6, 1),
            cash_balance=Decimal("0"),
            asset_holdings={"SPY": Decimal("7"), "AGG": Decimal("3")},
            current_prices={"SPY": Decimal("300"), "AGG": Decimal("100")},
        )
        # Total value: 7*300 + 3*100 = 2100 + 300 = 2400

        # Target: 60% SPY, 40% AGG
        target_weights = {"SPY": Decimal("0.6"), "AGG": Decimal("0.4")}

        trades = calculate_rebalancing_trades(current_state, target_weights)

        # Target values: SPY=1440 (60% of 2400), AGG=960 (40% of 2400)
        # Current values: SPY=2100, AGG=300
        # Need to sell SPY and buy AGG

        assert "SPY" in trades
        assert "AGG" in trades

        # SPY should be negative (sell)
        assert trades["SPY"] < 0

        # AGG should be positive (buy)
        assert trades["AGG"] > 0

    def test_no_rebalancing_when_at_target(self):
        """Test that no trades generated when already at target weights."""
        # Portfolio already at 60/40
        current_state = PortfolioState(
            timestamp=date(2020, 6, 1),
            cash_balance=Decimal("0"),
            asset_holdings={"SPY": Decimal("6"), "AGG": Decimal("4")},
            current_prices={"SPY": Decimal("300"), "AGG": Decimal("300")},
        )
        # Total: 6*300 + 4*300 = 3000
        # Current weights: SPY=60%, AGG=40%

        target_weights = {"SPY": Decimal("0.6"), "AGG": Decimal("0.4")}

        trades = calculate_rebalancing_trades(current_state, target_weights)

        # All trades should be very small (near zero due to rounding)
        for symbol, quantity in trades.items():
            assert abs(quantity) < Decimal("0.01")

    def test_weights_sum_to_one_after_rebalancing(self):
        """Property test: portfolio weights sum to 1.0 after rebalancing."""
        current_state = PortfolioState(
            timestamp=date(2020, 6, 1),
            cash_balance=Decimal("1000"),
            asset_holdings={"SPY": Decimal("5"), "AGG": Decimal("10")},
            current_prices={"SPY": Decimal("300"), "AGG": Decimal("100")},
        )

        target_weights = {"SPY": Decimal("0.7"), "AGG": Decimal("0.3")}

        trades = calculate_rebalancing_trades(current_state, target_weights)

        # Apply trades to portfolio
        new_holdings = {}
        for symbol in current_state.asset_holdings.keys():
            new_holdings[symbol] = current_state.asset_holdings[symbol] + trades.get(
                symbol, Decimal("0")
            )

        # Calculate new state
        new_state = PortfolioState(
            timestamp=current_state.timestamp,
            cash_balance=Decimal("0"),  # Assume all cash used
            asset_holdings=new_holdings,
            current_prices=current_state.current_prices,
        )

        # Check weights sum to ~1.0
        weights = new_state.get_current_weights()
        total_weight = sum(weights.values())

        assert abs(total_weight - Decimal("1.0")) < Decimal("0.01")
