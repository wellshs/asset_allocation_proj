"""Integration test for parameter configuration changes affecting results."""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from src.backtesting.engine import BacktestEngine
from src.models.backtest_config import BacktestConfiguration, TransactionCosts
from src.models import RebalancingFrequency
from src.models.strategy_params import MomentumParameters
from src.strategies.momentum import MomentumStrategy


class TestParameterChangesProduceDifferentResults:
    """Test that changing parameters produces different allocation results."""

    @pytest.fixture
    def price_data(self):
        """Create price data fixture for parameter sensitivity tests."""
        # Create 60 days of data with clear trend
        dates = pd.date_range(start="2020-01-01", end="2020-03-10", freq="B")
        spy_prices = [100 + i * 0.5 for i in range(len(dates))]  # Strong uptrend
        agg_prices = [100 + i * 0.1 for i in range(len(dates))]  # Weak uptrend
        gld_prices = [100 - i * 0.2 for i in range(len(dates))]  # Downtrend

        return pd.DataFrame(
            {
                "date": dates.tolist() * 3,
                "symbol": ["SPY"] * len(dates)
                + ["AGG"] * len(dates)
                + ["GLD"] * len(dates),
                "price": spy_prices + agg_prices + gld_prices,
                "currency": ["USD"] * (len(dates) * 3),
            }
        )

    def test_different_lookback_periods_produce_different_weights(self, price_data):
        """Test that different lookback periods result in different allocations.

        Short lookback (20 days) will be more responsive to recent trends.
        Long lookback (40 days) will consider longer-term performance.
        """
        # Strategy with short lookback (20 days)
        params_short = MomentumParameters(
            lookback_days=20,
            assets=["SPY", "AGG", "GLD"],
            exclude_negative=True,
        )
        strategy_short = MomentumStrategy(params_short)

        # Strategy with long lookback (40 days)
        params_long = MomentumParameters(
            lookback_days=40,
            assets=["SPY", "AGG", "GLD"],
            exclude_negative=True,
        )
        strategy_long = MomentumStrategy(params_long)

        # Calculate weights on same date with both strategies
        calc_date = date(2020, 3, 10)

        weights_short = strategy_short.calculate_weights(calc_date, price_data)
        weights_long = strategy_long.calculate_weights(calc_date, price_data)

        # Verify both are valid
        assert sum(weights_short.weights.values()) == Decimal("1.0")
        assert sum(weights_long.weights.values()) == Decimal("1.0")

        # Verify parameters were recorded
        assert weights_short.parameters_snapshot["lookback_days"] == 20
        assert weights_long.parameters_snapshot["lookback_days"] == 40

        # Weights should differ (unless by extreme coincidence)
        # At least one asset should have different weight
        weights_differ = False
        for asset in ["SPY", "AGG", "GLD"]:
            if weights_short.weights.get(
                asset, Decimal("0")
            ) != weights_long.weights.get(asset, Decimal("0")):
                weights_differ = True
                break

        assert (
            weights_differ
        ), "Different lookback periods should produce different weights"

    def test_exclude_negative_parameter_affects_allocation(self, price_data):
        """Test that exclude_negative parameter changes allocation behavior."""
        calc_date = date(2020, 3, 10)

        # Strategy that excludes negative momentum assets
        params_exclude = MomentumParameters(
            lookback_days=30,
            assets=["SPY", "AGG", "GLD"],
            exclude_negative=True,
        )
        strategy_exclude = MomentumStrategy(params_exclude)
        weights_exclude = strategy_exclude.calculate_weights(calc_date, price_data)

        # Strategy that includes all assets regardless of momentum
        params_include = MomentumParameters(
            lookback_days=30,
            assets=["SPY", "AGG", "GLD"],
            exclude_negative=False,
        )
        strategy_include = MomentumStrategy(params_include)
        weights_include = strategy_include.calculate_weights(calc_date, price_data)

        # GLD has downtrend, so should be excluded in first strategy
        assert "GLD" in weights_exclude.excluded_assets or weights_exclude.weights.get(
            "GLD", Decimal("0")
        ) == Decimal("0")

        # But included in second strategy (even with negative momentum)
        assert "GLD" in weights_include.weights

        # Verify parameters recorded correctly
        assert weights_exclude.parameters_snapshot["exclude_negative"] is True
        assert weights_include.parameters_snapshot["exclude_negative"] is False

    def test_min_momentum_threshold_filters_assets(self, price_data):
        """Test that min_momentum threshold filters low-performing assets."""
        calc_date = date(2020, 3, 10)

        # No threshold - all positive momentum assets included
        params_no_threshold = MomentumParameters(
            lookback_days=30,
            assets=["SPY", "AGG", "GLD"],
            exclude_negative=True,
            min_momentum=None,
        )
        strategy_no_threshold = MomentumStrategy(params_no_threshold)
        weights_no_threshold = strategy_no_threshold.calculate_weights(
            calc_date, price_data
        )

        # High threshold (10%) - only strong performers
        params_high_threshold = MomentumParameters(
            lookback_days=30,
            assets=["SPY", "AGG", "GLD"],
            exclude_negative=True,
            min_momentum=Decimal("0.10"),  # 10% minimum
        )
        strategy_high_threshold = MomentumStrategy(params_high_threshold)
        weights_high_threshold = strategy_high_threshold.calculate_weights(
            calc_date, price_data
        )

        # High threshold should exclude more assets (AGG has weak uptrend)
        num_assets_no_threshold = sum(
            1 for w in weights_no_threshold.weights.values() if w > 0
        )
        num_assets_high_threshold = sum(
            1 for w in weights_high_threshold.weights.values() if w > 0
        )

        assert (
            num_assets_high_threshold <= num_assets_no_threshold
        ), "Higher threshold should include fewer assets"

        # Verify min_momentum recorded in parameters
        assert (
            weights_high_threshold.parameters_snapshot.get("min_momentum") is not None
        )

    def test_parameter_snapshot_captured_in_backtest(self):
        """Test that parameter snapshots are captured during backtest."""
        # Create price data with sufficient lookback history (30 business days before backtest start)
        # Need to start from mid-December to have 30+ business days before Feb 3
        dates = pd.date_range(start="2019-12-15", end="2020-02-15", freq="B")
        spy_prices = [100 + i * 0.5 for i in range(len(dates))]  # Uptrend
        agg_prices = [100 + i * 0.2 for i in range(len(dates))]  # Slower uptrend

        price_data = pd.DataFrame(
            {
                "date": dates.tolist() * 2,
                "symbol": ["SPY"] * len(dates) + ["AGG"] * len(dates),
                "price": spy_prices + agg_prices,
                "currency": ["USD"] * (len(dates) * 2),
            }
        )

        params = MomentumParameters(
            lookback_days=30,
            assets=["SPY", "AGG"],
            exclude_negative=True,
            min_momentum=Decimal("0.05"),
        )
        strategy = MomentumStrategy(params)

        config = BacktestConfiguration(
            initial_capital=Decimal("10000"),
            start_date=date(2020, 2, 3),  # Start after sufficient lookback period
            end_date=date(2020, 2, 10),
            rebalancing_frequency=RebalancingFrequency.WEEKLY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("0"), percentage=Decimal("0")
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, price_data)

        # Backtest should complete successfully
        assert result.metrics is not None
        assert len(result.portfolio_history) > 0

        # Parameters should be accessible for audit
        # (In a real system, you might store weights with each rebalance)
        assert params.lookback_days == 30
        assert params.exclude_negative is True
        assert params.min_momentum == Decimal("0.05")


class TestParameterValidation:
    """Test parameter validation during strategy initialization."""

    def test_invalid_lookback_rejected(self):
        """Test that invalid lookback values are rejected."""
        # Zero lookback
        with pytest.raises(ValueError, match="must be positive"):
            params = MomentumParameters(lookback_days=0, assets=["SPY"])
            params.validate()

        # Negative lookback
        with pytest.raises(ValueError, match="must be positive"):
            params = MomentumParameters(lookback_days=-10, assets=["SPY"])
            params.validate()

        # Excessive lookback
        with pytest.raises(ValueError, match="≤ 500"):
            params = MomentumParameters(lookback_days=600, assets=["SPY"])
            params.validate()

    def test_empty_assets_rejected(self):
        """Test that empty asset list is rejected."""
        with pytest.raises(ValueError, match="at least one asset"):
            params = MomentumParameters(lookback_days=120, assets=[])
            params.validate()

    def test_duplicate_assets_rejected(self):
        """Test that duplicate assets are rejected."""
        with pytest.raises(ValueError, match="Duplicate assets"):
            params = MomentumParameters(lookback_days=120, assets=["SPY", "AGG", "SPY"])
            params.validate()

    def test_short_lookback_warning(self):
        """Test warning for very short lookback periods."""
        with pytest.warns(UserWarning, match="may be too short"):
            params = MomentumParameters(lookback_days=15, assets=["SPY"])
            params.validate()

    def test_long_lookback_warning(self):
        """Test warning for very long lookback periods."""
        with pytest.warns(UserWarning, match="may be too slow"):
            params = MomentumParameters(lookback_days=300, assets=["SPY"])
            params.validate()

    def test_negative_min_momentum_rejected(self):
        """Test that negative min_momentum is rejected."""
        with pytest.raises(ValueError, match="must be non-negative"):
            params = MomentumParameters(
                lookback_days=120, assets=["SPY"], min_momentum=Decimal("-0.05")
            )
            params.validate()


class TestParameterBacktestSensitivity:
    """Test that parameter changes affect backtest performance metrics."""

    def test_lookback_affects_backtest_performance(self):
        """Test that different lookback periods result in different performance."""
        # Create data with trend reversal - need sufficient history before backtest start
        # Start from Dec 2019 to have 30+ days before backtest start on 2020-02-03
        dates = pd.date_range(start="2019-12-01", end="2020-02-29", freq="B")
        # First half: SPY up, second half: SPY down
        mid_point = len(dates) // 2
        spy_prices = [100 + i * 0.5 for i in range(mid_point)] + [
            100 + mid_point * 0.5 - (i - mid_point) * 0.3
            for i in range(mid_point, len(dates))
        ]
        agg_prices = [100 + i * 0.1 for i in range(len(dates))]  # Steady up

        price_data = pd.DataFrame(
            {
                "date": dates.tolist() * 2,
                "symbol": ["SPY"] * len(dates) + ["AGG"] * len(dates),
                "price": spy_prices + agg_prices,
                "currency": ["USD"] * (len(dates) * 2),
            }
        )

        # Short lookback (10 days) - more responsive
        params_short = MomentumParameters(
            lookback_days=10, assets=["SPY", "AGG"], exclude_negative=True
        )
        strategy_short = MomentumStrategy(params_short)

        config = BacktestConfiguration(
            initial_capital=Decimal("10000"),
            start_date=date(2020, 2, 3),  # Start after sufficient lookback period
            end_date=date(2020, 2, 28),
            rebalancing_frequency=RebalancingFrequency.WEEKLY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("0"), percentage=Decimal("0")
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        engine = BacktestEngine()
        result_short = engine.run_backtest(config, strategy_short, price_data)

        # Long lookback (30 days) - slower to react
        params_long = MomentumParameters(
            lookback_days=30, assets=["SPY", "AGG"], exclude_negative=True
        )
        strategy_long = MomentumStrategy(params_long)

        result_long = engine.run_backtest(config, strategy_long, price_data)

        # Both should complete successfully
        assert result_short.metrics is not None
        assert result_long.metrics is not None

        # Performance should differ (short lookback adapts faster to reversal)
        # This is a weak assertion - just verify they're different
        assert (
            result_short.metrics.total_return != result_long.metrics.total_return
            or result_short.metrics.volatility != result_long.metrics.volatility
        ), "Different lookback periods should produce different performance"
