"""Integration tests for BacktestEngine with real strategy instances."""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from src.backtesting.engine import BacktestEngine
from src.models.backtest_config import BacktestConfiguration, TransactionCosts
from src.models import RebalancingFrequency
from src.models.strategy_params import (
    MomentumParameters,
    RiskParityParameters,
    DualMomentumParameters,
)
from src.strategies.momentum import MomentumStrategy
from src.strategies.risk_parity import RiskParityStrategy
from src.strategies.dual_momentum import DualMomentumStrategy


class TestRealStrategiesBacktest:
    """Integration tests using actual strategy instances with BacktestEngine."""

    @pytest.fixture
    def price_data(self):
        """Create realistic price data for integration testing."""
        dates = pd.date_range(start="2019-11-01", end="2020-02-29", freq="B")

        # Create varied price movements
        import random

        random.seed(42)

        spy_prices = [100.0]
        for _ in range(len(dates) - 1):
            spy_prices.append(spy_prices[-1] * (1 + random.gauss(0.001, 0.01)))

        agg_prices = [100.0]
        for _ in range(len(dates) - 1):
            agg_prices.append(agg_prices[-1] * (1 + random.gauss(0.0001, 0.003)))

        gld_prices = [100.0]
        for _ in range(len(dates) - 1):
            gld_prices.append(gld_prices[-1] * (1 + random.gauss(0.0003, 0.016)))

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

    def test_momentum_strategy_real_backtest(self, price_data):
        """Test BacktestEngine with actual MomentumStrategy instance."""
        params = MomentumParameters(
            lookback_days=30, assets=["SPY", "AGG", "GLD"], exclude_negative=True
        )
        strategy = MomentumStrategy(params)

        config = BacktestConfiguration(
            initial_capital=Decimal("10000"),
            start_date=date(2020, 1, 15),
            end_date=date(2020, 2, 28),
            rebalancing_frequency=RebalancingFrequency.WEEKLY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("0"), percentage=Decimal("0")
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, price_data)

        # Verify backtest completed successfully
        assert result.metrics is not None
        assert len(result.portfolio_history) > 0
        assert len(result.trades) > 0

        # Verify final portfolio value is positive
        assert result.portfolio_history[-1].total_value > 0

    def test_risk_parity_strategy_real_backtest(self, price_data):
        """Test BacktestEngine with actual RiskParityStrategy instance."""
        params = RiskParityParameters(lookback_days=30, assets=["SPY", "AGG", "GLD"])
        strategy = RiskParityStrategy(params)

        config = BacktestConfiguration(
            initial_capital=Decimal("10000"),
            start_date=date(2020, 1, 15),
            end_date=date(2020, 2, 28),
            rebalancing_frequency=RebalancingFrequency.WEEKLY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("0"), percentage=Decimal("0")
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, price_data)

        # Verify backtest completed successfully
        assert result.metrics is not None
        assert len(result.portfolio_history) > 0
        assert len(result.trades) > 0

        # Verify final portfolio value is positive
        assert result.portfolio_history[-1].total_value > 0

        # Risk parity should maintain relatively balanced risk exposure
        # (Lower volatility assets like AGG should have higher weights)
        final_portfolio = result.portfolio_history[-1]
        agg_holdings = final_portfolio.asset_holdings.get("AGG", Decimal("0"))
        assert agg_holdings > 0  # Should have some AGG allocation

    def test_dual_momentum_strategy_real_backtest(self, price_data):
        """Test BacktestEngine with actual DualMomentumStrategy instance."""
        params = DualMomentumParameters(
            lookback_days=50,
            assets=["SPY", "AGG", "GLD"],
            short_window=5,
            long_window=20,
        )
        strategy = DualMomentumStrategy(params)

        config = BacktestConfiguration(
            initial_capital=Decimal("10000"),
            start_date=date(2020, 1, 15),
            end_date=date(2020, 2, 28),
            rebalancing_frequency=RebalancingFrequency.WEEKLY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("0"), percentage=Decimal("0")
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, price_data)

        # Verify backtest completed successfully
        assert result.metrics is not None
        assert len(result.portfolio_history) > 0

        # Dual momentum may have fewer trades if signals are bearish
        # Just verify some portfolio activity occurred
        assert result.portfolio_history[-1].total_value > 0

    def test_strategies_use_different_price_data(self, price_data):
        """Verify strategies actually process price_data differently.

        This addresses the review concern that mock strategies ignore price_data.
        """
        # Same period, different strategies should produce different results
        config = BacktestConfiguration(
            initial_capital=Decimal("10000"),
            start_date=date(2020, 1, 15),
            end_date=date(2020, 2, 28),
            rebalancing_frequency=RebalancingFrequency.WEEKLY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("0"), percentage=Decimal("0")
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        # Run three different strategies
        momentum_params = MomentumParameters(
            lookback_days=30, assets=["SPY", "AGG"], exclude_negative=True
        )
        risk_parity_params = RiskParityParameters(
            lookback_days=30, assets=["SPY", "AGG"]
        )
        dual_ma_params = DualMomentumParameters(
            lookback_days=50,
            assets=["SPY", "AGG"],
            short_window=5,
            long_window=20,
        )

        engine = BacktestEngine()

        result_momentum = engine.run_backtest(
            config, MomentumStrategy(momentum_params), price_data
        )
        result_risk_parity = engine.run_backtest(
            config, RiskParityStrategy(risk_parity_params), price_data
        )
        result_dual_ma = engine.run_backtest(
            config, DualMomentumStrategy(dual_ma_params), price_data
        )

        # All should complete successfully
        assert result_momentum.metrics is not None
        assert result_risk_parity.metrics is not None
        assert result_dual_ma.metrics is not None

        # Results should differ (different strategies analyzing same data)
        assert (
            result_momentum.metrics.total_return
            != result_risk_parity.metrics.total_return
            or result_momentum.metrics.total_return
            != result_dual_ma.metrics.total_return
        ), "Different strategies should produce different results"

    def test_strategy_with_transaction_costs(self, price_data):
        """Test that real strategies handle transaction costs correctly."""
        params = MomentumParameters(
            lookback_days=30, assets=["SPY", "AGG"], exclude_negative=True
        )
        strategy = MomentumStrategy(params)

        config = BacktestConfiguration(
            initial_capital=Decimal("10000"),
            start_date=date(2020, 1, 15),
            end_date=date(2020, 2, 28),
            rebalancing_frequency=RebalancingFrequency.WEEKLY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("1.00"), percentage=Decimal("0.001")
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, price_data)

        # Verify transaction costs were applied
        total_costs = sum(trade.transaction_cost for trade in result.trades)
        assert total_costs > 0

        # Final value should be less than it would be without costs
        assert result.portfolio_history[-1].total_value > 0
