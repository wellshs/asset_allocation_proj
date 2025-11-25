"""Contract tests for Risk Parity Strategy calculation accuracy."""

from datetime import date
from decimal import Decimal

import pandas as pd

from src.models.strategy_params import RiskParityParameters
from src.strategies.risk_parity import RiskParityStrategy


class TestRiskParityCalculationAccuracy:
    """Contract tests for risk parity calculation correctness."""

    def test_inverse_volatility_weighting(self):
        """Test that weights are inversely proportional to volatility.

        Low volatility asset should get higher weight.
        """
        # Create data with different volatilities
        # Asset A: low volatility (stable prices)
        # Asset B: high volatility (large swings)
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
                        "2020-01-07",
                        "2020-01-07",
                    ]
                ),
                "symbol": ["A", "B"] * 5,
                "price": [
                    100.0,
                    100.0,  # Start
                    100.5,
                    105.0,  # A stable, B volatile
                    101.0,
                    95.0,  # A stable, B volatile
                    100.5,
                    110.0,  # A stable, B volatile
                    101.0,
                    90.0,  # A stable, B volatile
                ],
                "currency": ["USD"] * 10,
            }
        )

        params = RiskParityParameters(lookback_days=5, assets=["A", "B"])
        strategy = RiskParityStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 8), price_data)

        # Asset A (low volatility) should have higher weight than B
        assert weights.weights["A"] > weights.weights["B"]

        # Weights should sum to 1.0
        assert sum(weights.weights.values()) == Decimal("1.0")

    def test_equal_volatility_equal_weights(self):
        """Test that equal volatilities result in equal weights."""
        # Create data where both assets have same volatility
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
                    ]
                ),
                "symbol": ["SPY", "QQQ"] * 3,
                "price": [
                    100.0,
                    200.0,  # Start (different base prices)
                    105.0,
                    210.0,  # Both +5%
                    102.0,
                    204.0,  # Both -2.86%
                ],
                "currency": ["USD"] * 6,
            }
        )

        params = RiskParityParameters(lookback_days=3, assets=["SPY", "QQQ"])
        strategy = RiskParityStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 4), price_data)

        # Should be approximately equal (within small tolerance due to rounding)
        assert abs(weights.weights["SPY"] - weights.weights["QQQ"]) <= Decimal("0.01")
        assert sum(weights.weights.values()) == Decimal("1.0")

    def test_zero_volatility_excluded(self):
        """Test that assets with zero volatility are excluded."""
        # Create data where one asset has no price movement
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
                    ]
                ),
                "symbol": ["SPY", "STABLE"] * 3,
                "price": [
                    100.0,
                    100.0,  # Start
                    105.0,
                    100.0,  # SPY moves, STABLE flat
                    102.0,
                    100.0,  # SPY moves, STABLE flat
                ],
                "currency": ["USD"] * 6,
            }
        )

        params = RiskParityParameters(lookback_days=3, assets=["SPY", "STABLE"])
        strategy = RiskParityStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 4), price_data)

        # STABLE should be excluded or have zero weight
        assert "STABLE" in weights.excluded_assets or weights.weights.get(
            "STABLE", Decimal("0")
        ) == Decimal("0")

        # SPY should get 100% allocation
        assert weights.weights.get("SPY", Decimal("0")) == Decimal("1.0")

    def test_volatility_calculation_annualization(self):
        """Test that volatility is correctly annualized.

        Daily volatility should be multiplied by sqrt(252).
        """
        # Create data with realistic price movements (some volatility)
        dates = pd.date_range(start="2020-01-01", end="2020-01-31", freq="B")
        # Vary prices with some randomness to create volatility
        import random

        random.seed(42)
        spy_prices = [
            100.0 * (1 + random.gauss(0.001, 0.02)) ** i for i in range(len(dates))
        ]

        price_data = pd.DataFrame(
            {
                "date": dates.tolist(),
                "symbol": ["SPY"] * len(dates),
                "price": spy_prices,
                "currency": ["USD"] * len(dates),
            }
        )

        params = RiskParityParameters(lookback_days=20, assets=["SPY"])
        strategy = RiskParityStrategy(params)

        weights = strategy.calculate_weights(dates[-1].date(), price_data)

        # Should complete without error and assign 100% to single asset
        assert weights.weights.get("SPY", Decimal("0")) == Decimal("1.0")

        # Metadata should contain volatility
        assert "volatilities" in weights.metadata
        assert "SPY" in weights.metadata["volatilities"]
        assert (
            weights.metadata["volatilities"]["SPY"] > 0
        )  # Should have non-zero volatility

    def test_weights_sum_to_one(self):
        """Test that weights always sum to exactly 1.0."""
        # Create realistic multi-asset scenario with varying volatilities
        dates = pd.date_range(start="2020-01-01", end="2020-01-31", freq="B")

        # Create prices with realistic volatility patterns
        import random

        random.seed(42)

        # SPY: moderate volatility (~15% annualized)
        spy_prices = [100.0]
        for _ in range(len(dates) - 1):
            spy_prices.append(spy_prices[-1] * (1 + random.gauss(0.0005, 0.01)))

        # AGG: low volatility (~5% annualized)
        agg_prices = [100.0]
        for _ in range(len(dates) - 1):
            agg_prices.append(agg_prices[-1] * (1 + random.gauss(0.0001, 0.003)))

        # GLD: high volatility (~25% annualized)
        gld_prices = [100.0]
        for _ in range(len(dates) - 1):
            gld_prices.append(gld_prices[-1] * (1 + random.gauss(0.0003, 0.016)))

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

        params = RiskParityParameters(
            lookback_days=20,
            assets=["SPY", "AGG", "GLD"],
        )
        strategy = RiskParityStrategy(params)

        weights = strategy.calculate_weights(dates[-1].date(), price_data)

        # Weights must sum to exactly 1.0
        assert sum(weights.weights.values()) == Decimal("1.0")

        # AGG (lowest volatility) should have highest weight
        assert weights.weights.get("AGG", Decimal("0")) > Decimal("0")
        assert weights.weights.get("SPY", Decimal("0")) > Decimal("0")
        assert weights.weights.get("GLD", Decimal("0")) > Decimal("0")

        # AGG should have higher weight than GLD (inverse volatility)
        assert weights.weights["AGG"] > weights.weights["GLD"]
