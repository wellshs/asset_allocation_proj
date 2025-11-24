"""Contract tests for Dual Moving Average Strategy calculation accuracy."""

from decimal import Decimal

import pandas as pd

from src.models.strategy_params import DualMomentumParameters
from src.strategies.dual_momentum import DualMomentumStrategy


class TestDualMACalculationAccuracy:
    """Contract tests for dual moving average calculation correctness."""

    def test_short_ma_above_long_ma_bullish_signal(self):
        """Test that short MA > long MA generates bullish signal (buy).

        When short-term MA crosses above long-term MA, asset should be included.
        """
        # Create uptrend data where short MA > long MA (need 50+ days of data)
        dates = pd.date_range(start="2019-11-01", end="2020-01-31", freq="B")
        spy_prices = [100 + i * 2 for i in range(len(dates))]  # Strong uptrend

        price_data = pd.DataFrame(
            {
                "date": dates.tolist(),
                "symbol": ["SPY"] * len(dates),
                "price": spy_prices,
                "currency": ["USD"] * len(dates),
            }
        )

        params = DualMomentumParameters(
            lookback_days=50,
            assets=["SPY"],
            short_window=5,
            long_window=20,
        )
        strategy = DualMomentumStrategy(params)

        weights = strategy.calculate_weights(dates[-1].date(), price_data)

        # SPY should be included (bullish signal)
        assert weights.weights.get("SPY", Decimal("0")) == Decimal("1.0")

    def test_short_ma_below_long_ma_bearish_signal(self):
        """Test that short MA < long MA generates bearish signal (sell).

        When short-term MA crosses below long-term MA, asset should be excluded.
        """
        # Create downtrend data where short MA < long MA
        dates = pd.date_range(start="2019-11-01", end="2020-01-31", freq="B")
        spy_prices = [300 - i * 2 for i in range(len(dates))]  # Strong downtrend

        price_data = pd.DataFrame(
            {
                "date": dates.tolist(),
                "symbol": ["SPY"] * len(dates),
                "price": spy_prices,
                "currency": ["USD"] * len(dates),
            }
        )

        params = DualMomentumParameters(
            lookback_days=50,
            assets=["SPY"],
            short_window=5,
            long_window=20,
        )
        strategy = DualMomentumStrategy(params)

        weights = strategy.calculate_weights(dates[-1].date(), price_data)

        # SPY should be excluded (bearish signal) - allocate to CASH
        assert weights.weights.get("CASH", Decimal("0")) == Decimal("1.0")
        assert "SPY" in weights.excluded_assets

    def test_multi_asset_mixed_signals(self):
        """Test handling of multiple assets with different signals."""
        dates = pd.date_range(start="2019-11-01", end="2020-01-31", freq="B")

        # SPY: uptrend (bullish)
        spy_prices = [100 + i * 2 for i in range(len(dates))]

        # AGG: downtrend (bearish)
        agg_prices = [200 - i * 1 for i in range(len(dates))]

        price_data = pd.DataFrame(
            {
                "date": dates.tolist() * 2,
                "symbol": ["SPY"] * len(dates) + ["AGG"] * len(dates),
                "price": spy_prices + agg_prices,
                "currency": ["USD"] * (len(dates) * 2),
            }
        )

        params = DualMomentumParameters(
            lookback_days=50,
            assets=["SPY", "AGG"],
            short_window=5,
            long_window=20,
        )
        strategy = DualMomentumStrategy(params)

        weights = strategy.calculate_weights(dates[-1].date(), price_data)

        # Only SPY should be included (bullish), AGG excluded (bearish)
        assert weights.weights.get("SPY", Decimal("0")) == Decimal("1.0")
        assert "AGG" in weights.excluded_assets

        # Weights must sum to 1.0
        assert sum(weights.weights.values()) == Decimal("1.0")

    def test_all_bearish_allocate_cash(self):
        """Test that all bearish signals result in 100% cash allocation."""
        dates = pd.date_range(start="2019-11-01", end="2020-01-31", freq="B")

        # All assets in downtrend
        spy_prices = [300 - i * 2 for i in range(len(dates))]
        agg_prices = [250 - i * 1.5 for i in range(len(dates))]

        price_data = pd.DataFrame(
            {
                "date": dates.tolist() * 2,
                "symbol": ["SPY"] * len(dates) + ["AGG"] * len(dates),
                "price": spy_prices + agg_prices,
                "currency": ["USD"] * (len(dates) * 2),
            }
        )

        params = DualMomentumParameters(
            lookback_days=50,
            assets=["SPY", "AGG"],
            short_window=5,
            long_window=20,
        )
        strategy = DualMomentumStrategy(params)

        weights = strategy.calculate_weights(dates[-1].date(), price_data)

        # Should allocate 100% to CASH
        assert weights.weights.get("CASH", Decimal("0")) == Decimal("1.0")
        assert "SPY" in weights.excluded_assets
        assert "AGG" in weights.excluded_assets

    def test_signal_strength_weighting(self):
        """Test that use_signal_strength weights by MA spread."""
        dates = pd.date_range(start="2019-11-01", end="2020-01-31", freq="B")

        # SPY: strong uptrend (large MA spread)
        spy_prices = [100 + i * 3 for i in range(len(dates))]

        # AGG: weak uptrend (small MA spread)
        agg_prices = [100 + i * 0.5 for i in range(len(dates))]

        price_data = pd.DataFrame(
            {
                "date": dates.tolist() * 2,
                "symbol": ["SPY"] * len(dates) + ["AGG"] * len(dates),
                "price": spy_prices + agg_prices,
                "currency": ["USD"] * (len(dates) * 2),
            }
        )

        params = DualMomentumParameters(
            lookback_days=50,
            assets=["SPY", "AGG"],
            short_window=5,
            long_window=20,
            use_signal_strength=True,
        )
        strategy = DualMomentumStrategy(params)

        weights = strategy.calculate_weights(dates[-1].date(), price_data)

        # SPY should have higher weight (stronger signal)
        assert weights.weights.get("SPY", Decimal("0")) > weights.weights.get(
            "AGG", Decimal("0")
        )

        # Weights must sum to 1.0
        assert sum(weights.weights.values()) == Decimal("1.0")

    def test_weights_always_sum_to_one(self):
        """Test that weights always sum to exactly 1.0."""
        dates = pd.date_range(start="2019-11-01", end="2020-02-29", freq="B")

        # Create realistic mixed scenario
        import random

        random.seed(42)

        spy_prices = [100.0]
        for _ in range(len(dates) - 1):
            spy_prices.append(spy_prices[-1] * (1 + random.gauss(0.001, 0.01)))

        agg_prices = [100.0]
        for _ in range(len(dates) - 1):
            agg_prices.append(agg_prices[-1] * (1 + random.gauss(-0.0005, 0.008)))

        gld_prices = [100.0]
        for _ in range(len(dates) - 1):
            gld_prices.append(gld_prices[-1] * (1 + random.gauss(0.0002, 0.012)))

        price_data = pd.DataFrame(
            {
                "date": dates.tolist() * 3,
                "symbol": ["SPY"] * len(dates)
                + ["AGG"] * len(dates)
                + ["GLD"] * len(dates),
                "price": spy_prices + agg_prices + gld_prices,
                "currency": ["USD"] * (len(dates) * 3),
            }
        )

        params = DualMomentumParameters(
            lookback_days=50,
            assets=["SPY", "AGG", "GLD"],
            short_window=10,
            long_window=30,
        )
        strategy = DualMomentumStrategy(params)

        weights = strategy.calculate_weights(dates[-1].date(), price_data)

        # Weights must always sum to exactly 1.0
        assert sum(weights.weights.values()) == Decimal("1.0")
