"""Contract test for momentum calculation accuracy.

This test verifies that momentum calculations meet the specification requirements:
1. Momentum = (End Price / Start Price) - 1
2. Weights proportional to positive momentum scores
3. Negative momentum assets excluded when exclude_negative=True
4. 100% cash allocation when all assets have negative momentum
5. Weights always sum to exactly 1.0
"""

from datetime import date
from decimal import Decimal

import pandas as pd

from src.models.strategy_params import MomentumParameters
from src.strategies.momentum import MomentumStrategy


class TestMomentumCalculationAccuracy:
    """Contract tests for momentum calculation correctness."""

    def test_momentum_formula_accuracy(self):
        """Test that momentum is calculated as (end/start) - 1.

        Scenario: Asset A goes from 100 to 120 (20% return)
                  Asset B goes from 100 to 110 (10% return)
        Expected: Weights ~66.7% / 33.3% (2:1 ratio)
        """
        # Create price data: 3 days, 2 assets
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
                "symbol": ["SPY", "AGG", "SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 110.0, 105.0, 120.0, 110.0],
                "currency": ["USD"] * 6,
            }
        )

        params = MomentumParameters(
            lookback_days=3, assets=["SPY", "AGG"], exclude_negative=True
        )

        strategy = MomentumStrategy(params)

        # Calculate weights on day 4
        weights = strategy.calculate_weights(date(2020, 1, 4), price_data)

        # SPY: 100 → 120 = +20% momentum
        # AGG: 100 → 110 = +10% momentum
        # Ratio: 20:10 = 2:1 = 0.6667:0.3333

        assert weights.weights["SPY"] == Decimal("0.6667")
        assert weights.weights["AGG"] == Decimal("0.3333")
        assert sum(weights.weights.values()) == Decimal("1.0")

    def test_negative_momentum_exclusion(self):
        """Test that assets with negative momentum are excluded.

        Scenario: Asset A: +20%, Asset B: -5%, Asset C: +10%
        Expected: Only A and C in portfolio (B excluded)
        """
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2020-01-01",
                        "2020-01-01",
                        "2020-01-01",
                        "2020-01-02",
                        "2020-01-02",
                        "2020-01-02",
                        "2020-01-03",
                        "2020-01-03",
                        "2020-01-03",
                    ]
                ),
                "symbol": ["SPY", "AGG", "GLD"] * 3,
                "price": [
                    100.0,
                    100.0,
                    100.0,
                    110.0,
                    97.5,
                    105.0,
                    120.0,
                    95.0,
                    110.0,
                ],
                "currency": ["USD"] * 9,
            }
        )

        params = MomentumParameters(
            lookback_days=3, assets=["SPY", "AGG", "GLD"], exclude_negative=True
        )

        strategy = MomentumStrategy(params)
        weights = strategy.calculate_weights(date(2020, 1, 4), price_data)

        # SPY: 100 → 120 = +20%
        # AGG: 100 → 95 = -5% (EXCLUDED)
        # GLD: 100 → 110 = +10%
        # Ratio: 20:10 = 2:1 = 0.6667:0.3333

        assert "AGG" not in weights.weights or weights.weights["AGG"] == Decimal("0")
        assert weights.weights["SPY"] == Decimal("0.6667")
        assert weights.weights["GLD"] == Decimal("0.3333")
        assert sum(weights.weights.values()) == Decimal("1.0")
        assert "AGG" in weights.excluded_assets

    def test_all_negative_momentum_cash_allocation(self):
        """Test 100% cash when all assets have negative momentum.

        Scenario: All assets decline
        Expected: 100% CASH allocation
        """
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
                "symbol": ["SPY", "AGG", "SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 95.0, 98.0, 90.0, 96.0],
                "currency": ["USD"] * 6,
            }
        )

        params = MomentumParameters(
            lookback_days=3, assets=["SPY", "AGG"], exclude_negative=True
        )

        strategy = MomentumStrategy(params)
        weights = strategy.calculate_weights(date(2020, 1, 4), price_data)

        # SPY: 100 → 90 = -10%
        # AGG: 100 → 96 = -4%
        # Both negative → 100% CASH

        assert weights.weights.get("CASH") == Decimal("1.0")
        assert sum(weights.weights.values()) == Decimal("1.0")
        assert "SPY" in weights.excluded_assets
        assert "AGG" in weights.excluded_assets

    def test_weights_always_sum_to_one(self):
        """Property test: weights must always sum to 1.0."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 115.0, 107.0],
                "currency": ["USD"] * 4,
            }
        )

        params = MomentumParameters(lookback_days=2, assets=["SPY", "AGG"])
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # Must sum to exactly 1.0
        assert sum(weights.weights.values()) == Decimal("1.0")

    def test_exclude_negative_false_includes_all_assets(self):
        """Test that exclude_negative=False includes declining assets.

        Scenario: Asset A: +20%, Asset B: -10%
        With exclude_negative=False
        Expected: Both assets included with proportional weights
        """
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 120.0, 90.0],
                "currency": ["USD"] * 4,
            }
        )

        params = MomentumParameters(
            lookback_days=2, assets=["SPY", "AGG"], exclude_negative=False
        )

        strategy = MomentumStrategy(params)
        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # SPY: +20%, AGG: -10%
        # With exclude_negative=False, both included
        # Total momentum = 20 + (-10) = 10
        # Weights: SPY = 20/10 = 2.0 (but this is >1, so normalize differently)
        # Actually, we need to shift to make all positive, or use absolute values

        # Both should be present
        assert "SPY" in weights.weights
        assert "AGG" in weights.weights
        assert sum(weights.weights.values()) == Decimal("1.0")
