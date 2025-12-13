"""Integration test for BacktestEngine with dynamic strategies."""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from src.backtesting.engine import BacktestEngine
from src.backtesting.price_window import InsufficientDataError
from src.models.backtest_config import BacktestConfiguration, TransactionCosts
from src.models.calculated_weights import CalculatedWeights
from src.models.strategy import AllocationStrategy
from src.models import RebalancingFrequency


class MockDynamicStrategy:
    """Mock dynamic strategy for testing."""

    def __init__(self, weights_by_date: dict[date, dict[str, Decimal]]):
        """Initialize with pre-defined weights by date.

        Args:
            weights_by_date: Mapping of date to weights dict
        """
        self.weights_by_date = weights_by_date
        self.call_count = 0

    def calculate_weights(
        self, calculation_date: date, price_data: pd.DataFrame
    ) -> CalculatedWeights:
        """Calculate weights for given date.

        Args:
            calculation_date: Date for calculation
            price_data: Historical price data

        Returns:
            CalculatedWeights for the date
        """
        self.call_count += 1

        if calculation_date not in self.weights_by_date:
            raise InsufficientDataError(f"No weights defined for {calculation_date}")

        return CalculatedWeights(
            calculation_date=calculation_date,
            weights=self.weights_by_date[calculation_date],
            strategy_name="mock_dynamic",
            parameters_snapshot={"test": True},
        )


def test_backtest_detects_dynamic_strategy():
    """Test that BacktestEngine detects and calls calculate_weights."""
    # Create price data
    price_data = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2020-01-02", "2020-01-02", "2020-01-03", "2020-01-03"]
            ),
            "symbol": ["SPY", "AGG", "SPY", "AGG"],
            "price": [300.0, 110.0, 305.0, 111.0],
            "currency": ["USD", "USD", "USD", "USD"],
        }
    )

    # Create dynamic strategy with different weights on each date
    dynamic_strategy = MockDynamicStrategy(
        weights_by_date={
            date(2020, 1, 2): {"SPY": Decimal("0.6"), "AGG": Decimal("0.4")},
            date(2020, 1, 3): {"SPY": Decimal("0.7"), "AGG": Decimal("0.3")},
        }
    )

    # Create backtest config
    config = BacktestConfiguration(
        initial_capital=Decimal("10000"),
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 3),
        rebalancing_frequency=RebalancingFrequency.DAILY,
        transaction_costs=TransactionCosts(
            fixed_per_trade=Decimal("0"), percentage=Decimal("0")
        ),
        base_currency="USD",
        risk_free_rate=Decimal("0"),
    )

    # Run backtest
    engine = BacktestEngine()
    result = engine.run_backtest(config, dynamic_strategy, price_data)

    # Verify calculate_weights was called (once for each date)
    assert dynamic_strategy.call_count == 2

    # Verify backtest completed successfully
    assert result.metrics is not None
    assert len(result.portfolio_history) == 2
    assert len(result.trades) > 0  # Initial + rebalancing trades


def test_backtest_static_strategy_still_works():
    """Test that static strategies still work after engine modifications."""
    # Create price data with both assets on both dates
    price_data = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2020-01-02", "2020-01-02", "2020-01-03", "2020-01-03"]
            ),
            "symbol": ["SPY", "AGG", "SPY", "AGG"],
            "price": [300.0, 110.0, 305.0, 111.0],
            "currency": ["USD", "USD", "USD", "USD"],
        }
    )

    # Create static strategy
    static_strategy = AllocationStrategy(
        name="60/40",
        asset_weights={"SPY": Decimal("0.6"), "AGG": Decimal("0.4")},
    )

    # Create backtest config
    config = BacktestConfiguration(
        initial_capital=Decimal("10000"),
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 3),
        rebalancing_frequency=RebalancingFrequency.NEVER,
        transaction_costs=TransactionCosts(
            fixed_per_trade=Decimal("0"), percentage=Decimal("0")
        ),
        base_currency="USD",
        risk_free_rate=Decimal("0"),
    )

    # Run backtest
    engine = BacktestEngine()
    result = engine.run_backtest(config, static_strategy, price_data)

    # Verify backtest completed successfully
    assert result.metrics is not None
    assert len(result.portfolio_history) == 2  # Two days of data
    assert len(result.trades) == 2  # Initial purchases only (no rebalancing)


def test_backtest_handles_insufficient_data_with_fallback():
    """Test that engine uses previous weights when data is insufficient."""

    class FailingDynamicStrategy:
        """Strategy that fails on second calculation."""

        def __init__(self):
            self.call_count = 0

        def calculate_weights(
            self, calculation_date: date, price_data: pd.DataFrame
        ) -> CalculatedWeights:
            self.call_count += 1

            if self.call_count == 1:
                # First call succeeds
                return CalculatedWeights(
                    calculation_date=calculation_date,
                    weights={"SPY": Decimal("0.6"), "AGG": Decimal("0.4")},
                    strategy_name="failing",
                    parameters_snapshot={},
                )
            else:
                # Second call fails
                raise InsufficientDataError("Not enough data")

    # Create price data
    price_data = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2020-01-02", "2020-01-02", "2020-01-03", "2020-01-03"]
            ),
            "symbol": ["SPY", "AGG", "SPY", "AGG"],
            "price": [300.0, 110.0, 305.0, 111.0],
            "currency": ["USD", "USD", "USD", "USD"],
        }
    )

    strategy = FailingDynamicStrategy()

    config = BacktestConfiguration(
        initial_capital=Decimal("10000"),
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 3),
        rebalancing_frequency=RebalancingFrequency.DAILY,
        transaction_costs=TransactionCosts(
            fixed_per_trade=Decimal("0"), percentage=Decimal("0")
        ),
        base_currency="USD",
        risk_free_rate=Decimal("0"),
    )

    # Run backtest - should succeed by using previous weights
    engine = BacktestEngine()
    result = engine.run_backtest(config, strategy, price_data)

    # Verify calculate_weights was called twice
    assert strategy.call_count == 2

    # Verify backtest completed successfully despite second call failing
    assert result.metrics is not None
    assert len(result.portfolio_history) == 2


def test_backtest_fails_on_initial_insufficient_data():
    """Test that engine raises error if initial calculation fails."""

    class AlwaysFailingStrategy:
        """Strategy that always fails."""

        def calculate_weights(
            self, calculation_date: date, price_data: pd.DataFrame
        ) -> CalculatedWeights:
            raise InsufficientDataError("Never enough data")

    price_data = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2020-01-02", "2020-01-02", "2020-01-03", "2020-01-03"]
            ),
            "symbol": ["SPY", "AGG", "SPY", "AGG"],
            "price": [300.0, 110.0, 305.0, 111.0],
            "currency": ["USD", "USD", "USD", "USD"],
        }
    )

    strategy = AlwaysFailingStrategy()

    config = BacktestConfiguration(
        initial_capital=Decimal("10000"),
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 3),
        rebalancing_frequency=RebalancingFrequency.NEVER,
        transaction_costs=TransactionCosts(
            fixed_per_trade=Decimal("0"), percentage=Decimal("0")
        ),
        base_currency="USD",
        risk_free_rate=Decimal("0"),
    )

    # Should raise DataError
    engine = BacktestEngine()
    with pytest.raises(Exception, match="Insufficient data for initial calculation"):
        engine.run_backtest(config, strategy, price_data)
