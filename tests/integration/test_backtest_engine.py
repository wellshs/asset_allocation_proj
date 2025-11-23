"""Integration tests for end-to-end backtest execution."""

import pytest
from pathlib import Path
from datetime import date
from decimal import Decimal

from src.backtesting.engine import BacktestEngine
from src.models.backtest_config import BacktestConfiguration
from src.models.strategy import AllocationStrategy
from src.models import RebalancingFrequency
from src.data.loaders import CSVDataProvider


class TestBacktestEngineIntegration:
    """Integration tests for complete backtest workflow."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get path to test fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    @pytest.fixture
    def data_provider(self, fixtures_dir):
        """Create CSV data provider."""
        return CSVDataProvider(fixtures_dir)

    def test_end_to_end_backtest_execution(self, data_provider):
        """Test complete backtest from data loading to results.

        This test validates the entire workflow:
        1. Load historical price data
        2. Configure strategy and backtest parameters
        3. Execute backtest
        4. Generate performance metrics
        5. Verify results structure
        """
        # Load data
        prices = data_provider.load_prices(
            symbols=["SPY", "AGG"],
            start_date=date(2010, 1, 4),
            end_date=date(2010, 12, 31),
        )

        # Define strategy
        strategy = AllocationStrategy(
            name="Balanced",
            asset_weights={"SPY": Decimal("0.5"), "AGG": Decimal("0.5")},
        )

        # Configure backtest
        config = BacktestConfiguration(
            start_date=date(2010, 1, 4),
            end_date=date(2010, 12, 31),
            initial_capital=Decimal("100000"),
            rebalancing_frequency=RebalancingFrequency.QUARTERLY,
            base_currency="USD",
        )

        # Execute backtest
        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, prices)

        # Verify result structure
        assert result is not None
        assert hasattr(result, "metrics")
        assert hasattr(result, "trades")
        assert hasattr(result, "portfolio_history")

        # Verify metrics exist and have reasonable values
        metrics = result.metrics
        assert metrics.start_date == date(2010, 1, 4)
        assert metrics.end_date == date(2010, 12, 31)
        # Allow small rounding error in start value
        assert abs(metrics.start_value - Decimal("100000")) < Decimal("0.01")
        assert metrics.end_value > 0
        assert metrics.num_trades >= 0

        # Portfolio history should exist
        assert len(result.portfolio_history) > 0
        assert result.portfolio_history[0].timestamp == date(2010, 1, 4)

    def test_buy_and_hold_no_rebalancing(self, data_provider):
        """Test buy-and-hold strategy produces minimal trades."""
        prices = data_provider.load_prices(
            symbols=["SPY"], start_date=date(2010, 1, 4), end_date=date(2010, 12, 31)
        )

        strategy = AllocationStrategy(
            name="Buy and Hold", asset_weights={"SPY": Decimal("1.0")}
        )

        config = BacktestConfiguration(
            start_date=date(2010, 1, 4),
            end_date=date(2010, 12, 31),
            initial_capital=Decimal("100000"),
            rebalancing_frequency=RebalancingFrequency.NEVER,
            base_currency="USD",
        )

        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, prices)

        # Buy-and-hold should have only initial purchase
        assert (
            result.metrics.num_trades == 1
        ), "Buy-and-hold should have exactly 1 trade (initial purchase)"

    def test_performance_metrics_consistency(self, data_provider):
        """Test that performance metrics are internally consistent."""
        prices = data_provider.load_prices(
            symbols=["SPY", "AGG"],
            start_date=date(2010, 1, 4),
            end_date=date(2010, 12, 31),
        )

        strategy = AllocationStrategy(
            name="Test", asset_weights={"SPY": Decimal("0.6"), "AGG": Decimal("0.4")}
        )

        config = BacktestConfiguration(
            start_date=date(2010, 1, 4),
            end_date=date(2010, 12, 31),
            initial_capital=Decimal("100000"),
            rebalancing_frequency=RebalancingFrequency.MONTHLY,
            base_currency="USD",
        )

        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, prices)

        metrics = result.metrics

        # Total return should match (end - start) / start
        expected_total_return = (
            metrics.end_value - metrics.start_value
        ) / metrics.start_value
        assert abs(metrics.total_return - expected_total_return) < Decimal("0.0001")

        # Max drawdown should be negative or zero
        assert metrics.max_drawdown <= 0

        # Volatility should be non-negative
        assert metrics.volatility >= 0

    def test_transaction_costs_reduce_portfolio_value(self, data_provider):
        """Verify transaction costs are deducted from cash balance.

        This test ensures that transaction costs are properly applied by:
        1. Running a backtest with non-zero transaction costs
        2. Verifying that trades have transaction costs recorded
        3. Comparing with a zero-cost backtest to verify the impact
        """
        # Load data
        prices = data_provider.load_prices(
            symbols=["SPY", "AGG"],
            start_date=date(2010, 1, 4),
            end_date=date(2010, 12, 31),
        )

        # Define strategy
        strategy = AllocationStrategy(
            name="Balanced",
            asset_weights={"SPY": Decimal("0.5"), "AGG": Decimal("0.5")},
        )

        # Create config with non-zero transaction costs
        from src.models.backtest_config import TransactionCosts

        config = BacktestConfiguration(
            start_date=date(2010, 1, 4),
            end_date=date(2010, 12, 31),
            initial_capital=Decimal("100000"),
            rebalancing_frequency=RebalancingFrequency.QUARTERLY,
            base_currency="USD",
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("10"), percentage=Decimal("0.001")
            ),
        )

        # Execute backtest
        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, prices)

        # Calculate expected costs from trades (excluding initial purchase which has 0 cost)
        expected_costs = sum(
            trade.transaction_cost
            for trade in result.trades
            if trade.transaction_cost > 0
        )

        # Verify costs were actually deducted
        assert expected_costs > 0, "Test requires non-zero transaction costs"

        # Verify individual trade costs are calculated correctly (fixed + percentage)
        # Check at least one rebalancing trade
        rebalancing_trades = [t for t in result.trades if t.transaction_cost > 0]
        assert len(rebalancing_trades) > 0, "Should have rebalancing trades with costs"

        for trade in rebalancing_trades[:3]:  # Check first 3 trades
            trade_value = abs(trade.quantity * trade.price)
            expected_cost = Decimal("10") + (Decimal("0.001") * trade_value)
            # Round to 2 decimal places like the actual calculation
            expected_cost = expected_cost.quantize(Decimal("0.01"))
            assert (
                trade.transaction_cost == expected_cost
            ), f"Trade cost {trade.transaction_cost} should equal fixed (10) + percentage (0.001 × {trade_value}) = {expected_cost}"

        # Compare with a backtest without transaction costs
        config_no_costs = BacktestConfiguration(
            start_date=date(2010, 1, 4),
            end_date=date(2010, 12, 31),
            initial_capital=Decimal("100000"),
            rebalancing_frequency=RebalancingFrequency.QUARTERLY,
            base_currency="USD",
        )

        result_no_costs = engine.run_backtest(config_no_costs, strategy, prices)

        # End value with costs should be lower by at least the total costs
        value_difference = result_no_costs.metrics.end_value - result.metrics.end_value

        # The difference should be at least the expected costs
        # (will likely be higher due to compounding effects and different trading patterns)
        assert value_difference > 0, "Portfolio with costs should have lower end value"
        assert (
            value_difference >= expected_costs
        ), f"Value difference ({value_difference}) should be at least the transaction costs ({expected_costs})"

        # Verify that transaction costs are being tracked in cash balance
        # Check that final cash balance reflects costs
        final_cash_with_costs = result.portfolio_history[-1].cash_balance
        final_cash_no_costs = result_no_costs.portfolio_history[-1].cash_balance

        # Cash difference should reflect at least the direct transaction costs
        cash_difference = final_cash_no_costs - final_cash_with_costs
        assert (
            cash_difference > 0
        ), "Cash balance should be lower when transaction costs are applied"
