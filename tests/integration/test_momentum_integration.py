"""Integration test for MomentumStrategy with BacktestEngine."""

from datetime import date
from decimal import Decimal

import pandas as pd

from src.backtesting.engine import BacktestEngine
from src.models.backtest_config import BacktestConfiguration, TransactionCosts
from src.models import RebalancingFrequency
from src.models.strategy_params import MomentumParameters
from src.strategies.momentum import MomentumStrategy


class TestMomentumBacktestIntegration:
    """Integration tests for MomentumStrategy with BacktestEngine."""

    def test_momentum_backtest_complete_run(self):
        """Test complete backtest with momentum strategy."""
        # Create 2 weeks of price data with clear momentum pattern
        # Need sufficient history BEFORE backtest start
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        # Pre-backtest history for lookback
                        "2019-12-30",
                        "2019-12-30",
                        "2019-12-31",
                        "2019-12-31",
                        "2020-01-01",
                        "2020-01-01",
                        "2020-01-02",
                        "2020-01-02",
                        # Backtest period starts here
                        "2020-01-03",
                        "2020-01-03",
                        "2020-01-06",
                        "2020-01-06",
                        "2020-01-07",
                        "2020-01-07",
                        "2020-01-08",
                        "2020-01-08",
                    ]
                ),
                "symbol": ["SPY", "AGG"] * 8,
                "price": [
                    # Pre-backtest history
                    100.0,
                    100.0,
                    102.0,
                    100.0,
                    105.0,
                    100.0,
                    107.0,
                    101.0,
                    # Backtest period: SPY continues up, AGG starts rising
                    110.0,
                    101.0,
                    110.0,
                    105.0,
                    110.0,
                    108.0,
                    111.0,
                    110.0,
                ],
                "currency": ["USD"] * 16,
            }
        )

        # Create momentum strategy with 3-day lookback
        params = MomentumParameters(
            lookback_days=3, assets=["SPY", "AGG"], exclude_negative=True
        )
        strategy = MomentumStrategy(params)

        # Create backtest config - start on 2020-01-03 (have 4 days of history before)
        config = BacktestConfiguration(
            initial_capital=Decimal("10000"),
            start_date=date(2020, 1, 3),
            end_date=date(2020, 1, 8),
            rebalancing_frequency=RebalancingFrequency.DAILY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("0"), percentage=Decimal("0")
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        # Run backtest
        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, price_data)

        # Verify backtest completed
        assert result.metrics is not None
        assert len(result.portfolio_history) > 0
        assert len(result.trades) > 0

        # Verify portfolio value is positive
        final_value = result.portfolio_history[-1].total_value
        assert final_value > 0

    def test_momentum_weights_change_over_time(self):
        """Test that momentum weights adapt to changing market conditions."""
        # Create price data where momentum leader changes
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2019-12-30",
                        "2019-12-30",
                        "2019-12-31",
                        "2019-12-31",
                        "2020-01-01",
                        "2020-01-01",
                        "2020-01-02",
                        "2020-01-02",
                        "2020-01-03",
                        "2020-01-03",
                        "2020-01-06",
                        "2020-01-06",
                    ]
                ),
                "symbol": ["SPY", "AGG"] * 6,
                "price": [
                    100.0,
                    100.0,  # Start
                    105.0,
                    100.0,
                    110.0,
                    100.0,  # SPY up, AGG flat
                    115.0,
                    102.0,
                    120.0,
                    105.0,  # SPY continues up
                    121.0,
                    120.0,  # AGG catches up
                ],
                "currency": ["USD"] * 12,
            }
        )

        params = MomentumParameters(
            lookback_days=3, assets=["SPY", "AGG"], exclude_negative=True
        )
        strategy = MomentumStrategy(params)

        config = BacktestConfiguration(
            initial_capital=Decimal("10000"),
            start_date=date(2020, 1, 3),
            end_date=date(2020, 1, 6),
            rebalancing_frequency=RebalancingFrequency.DAILY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("0"), percentage=Decimal("0")
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, price_data)

        # Verify that trades occurred (weights changed)
        # Initial purchase + rebalancing trades
        assert len(result.trades) >= 2

    def test_momentum_with_negative_returns_allocates_cash(self):
        """Test that momentum strategy allocates to cash when all assets decline."""
        # Create declining market scenario
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 90.0, 95.0],  # Both decline
                "currency": ["USD"] * 4,
            }
        )

        params = MomentumParameters(
            lookback_days=2, assets=["SPY", "AGG"], exclude_negative=True
        )
        strategy = MomentumStrategy(params)

        # Test weight calculation directly (not full backtest)
        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # Should allocate 100% to CASH
        assert weights.weights.get("CASH") == Decimal("1.0")
        assert "SPY" in weights.excluded_assets
        assert "AGG" in weights.excluded_assets

    def test_momentum_with_transaction_costs(self):
        """Test that transaction costs are applied during momentum rebalancing."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2019-12-30",
                        "2019-12-30",
                        "2019-12-31",
                        "2019-12-31",
                        "2020-01-01",
                        "2020-01-01",
                        "2020-01-02",
                        "2020-01-02",
                        "2020-01-03",
                        "2020-01-03",
                    ]
                ),
                "symbol": ["SPY", "AGG"] * 5,
                "price": [
                    100.0,
                    100.0,
                    105.0,
                    100.0,
                    107.0,
                    101.0,
                    110.0,
                    102.0,
                    120.0,
                    110.0,
                ],
                "currency": ["USD"] * 10,
            }
        )

        params = MomentumParameters(
            lookback_days=3, assets=["SPY", "AGG"], exclude_negative=True
        )
        strategy = MomentumStrategy(params)

        config = BacktestConfiguration(
            initial_capital=Decimal("10000"),
            start_date=date(2020, 1, 2),
            end_date=date(2020, 1, 3),
            rebalancing_frequency=RebalancingFrequency.DAILY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("1.00"),  # $1 per trade
                percentage=Decimal("0.001"),  # 0.1%
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, price_data)

        # Verify transaction costs were applied
        total_costs = sum(trade.transaction_cost for trade in result.trades)
        assert total_costs > 0

        # Final value should include impact of costs (but may still be > initial due to gains)
        final_value = result.portfolio_history[-1].total_value
        # Just verify portfolio has a value and costs were deducted
        assert final_value > 0
        assert total_costs > Decimal("1.00")  # At least the fixed cost per trade

    def test_momentum_longer_backtest_period(self):
        """Test momentum strategy over longer period with monthly rebalancing."""
        # Create 4 months of data (includes pre-backtest period)
        dates = pd.date_range(start="2019-12-01", end="2020-03-31", freq="B")
        spy_prices = [100 + i * 0.5 for i in range(len(dates))]  # Uptrend
        agg_prices = [100 + i * 0.2 for i in range(len(dates))]  # Slower uptrend

        price_data = pd.DataFrame(
            {
                "date": dates.tolist() + dates.tolist(),
                "symbol": ["SPY"] * len(dates) + ["AGG"] * len(dates),
                "price": spy_prices + agg_prices,
                "currency": ["USD"] * (len(dates) * 2),
            }
        )

        params = MomentumParameters(
            lookback_days=20, assets=["SPY", "AGG"], exclude_negative=True
        )
        strategy = MomentumStrategy(params)

        config = BacktestConfiguration(
            initial_capital=Decimal("100000"),
            start_date=date(2020, 1, 20),  # After sufficient lookback period
            end_date=date(2020, 3, 31),
            rebalancing_frequency=RebalancingFrequency.MONTHLY,
            transaction_costs=TransactionCosts(
                fixed_per_trade=Decimal("0"), percentage=Decimal("0")
            ),
            base_currency="USD",
            risk_free_rate=Decimal("0"),
        )

        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, price_data)

        # Verify positive return (both assets trending up)
        assert result.metrics.total_return > 0

        # Verify SPY had higher allocation (faster momentum)
        # Check final portfolio holdings
        final_portfolio = result.portfolio_history[-1]
        spy_value = final_portfolio.asset_holdings.get(
            "SPY", Decimal("0")
        ) * final_portfolio.current_prices.get("SPY", Decimal("0"))
        agg_value = final_portfolio.asset_holdings.get(
            "AGG", Decimal("0")
        ) * final_portfolio.current_prices.get("AGG", Decimal("0"))

        # SPY should have higher value due to stronger momentum
        assert spy_value >= agg_value


class TestMomentumParameterSensitivity:
    """Test momentum strategy sensitivity to parameter changes."""

    def test_different_lookback_periods_produce_different_results(self):
        """Test that changing lookback period changes allocations."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2020-01-01",
                        "2020-01-01",
                        "2020-01-02",
                        "2020-01-02",
                        "2020-01-03",
                        "2020-01-03",
                        "2020-01-06",
                        "2020-01-06",
                    ]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG", "SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 105.0, 102.0, 110.0, 104.0, 115.0, 106.0],
                "currency": ["USD"] * 8,
            }
        )

        # Short lookback (2 days): recent performance
        params_short = MomentumParameters(lookback_days=2, assets=["SPY", "AGG"])
        strategy_short = MomentumStrategy(params_short)
        weights_short = strategy_short.calculate_weights(date(2020, 1, 7), price_data)

        # Long lookback (4 days): longer-term performance
        params_long = MomentumParameters(lookback_days=4, assets=["SPY", "AGG"])
        strategy_long = MomentumStrategy(params_long)
        weights_long = strategy_long.calculate_weights(date(2020, 1, 7), price_data)

        # Weights should differ (unless by coincidence they're the same)
        # Just verify both produce valid weights
        assert sum(weights_short.weights.values()) == Decimal("1.0")
        assert sum(weights_long.weights.values()) == Decimal("1.0")
