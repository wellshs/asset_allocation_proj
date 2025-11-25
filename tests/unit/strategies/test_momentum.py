"""Unit tests for MomentumStrategy."""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from src.backtesting.price_window import InsufficientDataError
from src.models.strategy_params import MomentumParameters
from src.strategies.momentum import MomentumStrategy


class TestMomentumScoreCalculation:
    """Test suite for momentum score calculation."""

    def test_calculate_momentum_score_basic(self):
        """Test basic momentum score calculation: (end/start) - 1."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
                "symbol": ["SPY", "SPY", "SPY"],
                "price": [100.0, 110.0, 120.0],
                "currency": ["USD"] * 3,
            }
        )

        params = MomentumParameters(lookback_days=3, assets=["SPY"])
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 4), price_data)

        # 100 → 120 = 20% return
        assert weights.weights["SPY"] == Decimal("1.0")

    def test_momentum_with_multiple_assets(self):
        """Test momentum calculation with multiple assets."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 110.0, 105.0],
                "currency": ["USD"] * 4,
            }
        )

        params = MomentumParameters(lookback_days=2, assets=["SPY", "AGG"])
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # SPY: +10%, AGG: +5% → 10:5 = 2:1 = 0.6667:0.3333
        assert weights.weights["SPY"] == Decimal("0.6667")
        assert weights.weights["AGG"] == Decimal("0.3333")

    def test_momentum_excludes_negative_returns(self):
        """Test that negative returns are excluded when exclude_negative=True."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 110.0, 95.0],
                "currency": ["USD"] * 4,
            }
        )

        params = MomentumParameters(
            lookback_days=2, assets=["SPY", "AGG"], exclude_negative=True
        )
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # SPY: +10%, AGG: -5% (excluded)
        assert weights.weights["SPY"] == Decimal("1.0")
        assert "AGG" not in weights.weights or weights.weights["AGG"] == Decimal("0")
        assert "AGG" in weights.excluded_assets

    def test_all_negative_allocates_to_cash(self):
        """Test 100% CASH when all assets negative."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 95.0, 90.0],
                "currency": ["USD"] * 4,
            }
        )

        params = MomentumParameters(
            lookback_days=2, assets=["SPY", "AGG"], exclude_negative=True
        )
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        assert weights.weights.get("CASH") == Decimal("1.0")
        assert "SPY" in weights.excluded_assets
        assert "AGG" in weights.excluded_assets

    def test_zero_momentum_asset_gets_zero_weight(self):
        """Test that asset with zero momentum gets zero weight."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 110.0, 100.0],  # AGG unchanged
                "currency": ["USD"] * 4,
            }
        )

        params = MomentumParameters(lookback_days=2, assets=["SPY", "AGG"])
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # SPY: +10%, AGG: 0%
        # If exclude_negative=True (default), AGG might be excluded
        # Or if included, weight proportional: 10:0
        assert weights.weights["SPY"] == Decimal("1.0")

    def test_insufficient_data_raises_error(self):
        """Test that insufficient data raises InsufficientDataError."""
        # Only 2 days of data, but need 5
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
                "symbol": ["SPY", "SPY"],
                "price": [100.0, 105.0],
                "currency": ["USD"] * 2,
            }
        )

        params = MomentumParameters(lookback_days=5, assets=["SPY"])
        strategy = MomentumStrategy(params)

        with pytest.raises(InsufficientDataError):
            strategy.calculate_weights(date(2020, 1, 3), price_data)

    def test_missing_data_excludes_asset(self):
        """Test that assets with missing data are excluded."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02"]  # AGG missing on day 2
                ),
                "symbol": ["SPY", "AGG", "SPY"],
                "price": [100.0, 100.0, 110.0],
                "currency": ["USD"] * 3,
            }
        )

        params = MomentumParameters(lookback_days=2, assets=["SPY", "AGG"])
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # AGG has missing data, should be excluded
        assert weights.weights["SPY"] == Decimal("1.0")
        assert "AGG" in weights.excluded_assets

    def test_min_momentum_threshold(self):
        """Test that min_momentum threshold filters assets."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 120.0, 102.0],  # SPY: 20%, AGG: 2%
                "currency": ["USD"] * 4,
            }
        )

        # Set min_momentum = 5% (0.05)
        params = MomentumParameters(
            lookback_days=2,
            assets=["SPY", "AGG"],
            min_momentum=Decimal("0.05"),  # 5% threshold
        )
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # SPY: 20% (above threshold)
        # AGG: 2% (below threshold, excluded)
        assert weights.weights["SPY"] == Decimal("1.0")
        assert "AGG" in weights.excluded_assets


class TestMomentumMetadata:
    """Test suite for momentum calculation metadata."""

    def test_metadata_includes_momentum_scores(self):
        """Test that metadata includes momentum scores."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 110.0, 105.0],
                "currency": ["USD"] * 4,
            }
        )

        params = MomentumParameters(lookback_days=2, assets=["SPY", "AGG"])
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # Metadata should contain momentum scores
        assert "momentum_scores" in weights.metadata
        assert "SPY" in weights.metadata["momentum_scores"]
        assert "AGG" in weights.metadata["momentum_scores"]

    def test_parameters_snapshot_recorded(self):
        """Test that parameters are recorded in CalculatedWeights."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
                "symbol": ["SPY", "SPY"],
                "price": [100.0, 110.0],
                "currency": ["USD"] * 2,
            }
        )

        params = MomentumParameters(
            lookback_days=2, assets=["SPY"], exclude_negative=True
        )
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # Parameters should be captured
        assert "lookback_days" in weights.parameters_snapshot
        assert weights.parameters_snapshot["lookback_days"] == 2
        assert "exclude_negative" in weights.parameters_snapshot


class TestMomentumEdgeCases:
    """Test suite for momentum edge cases."""

    def test_single_asset_gets_full_allocation(self):
        """Test single asset with positive momentum gets 100%."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
                "symbol": ["SPY", "SPY"],
                "price": [100.0, 110.0],
                "currency": ["USD"] * 2,
            }
        )

        params = MomentumParameters(lookback_days=2, assets=["SPY"])
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        assert weights.weights["SPY"] == Decimal("1.0")

    def test_equal_momentum_equal_weights(self):
        """Test equal momentum results in equal weights."""
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "symbol": ["SPY", "AGG", "SPY", "AGG"],
                "price": [100.0, 100.0, 110.0, 110.0],  # Both +10%
                "currency": ["USD"] * 4,
            }
        )

        params = MomentumParameters(lookback_days=2, assets=["SPY", "AGG"])
        strategy = MomentumStrategy(params)

        weights = strategy.calculate_weights(date(2020, 1, 3), price_data)

        # Equal momentum → equal weights (but sum adjustment may affect last)
        assert abs(weights.weights["SPY"] - Decimal("0.5")) <= Decimal("0.0001")
        assert abs(weights.weights["AGG"] - Decimal("0.5")) <= Decimal("0.0001")
        assert sum(weights.weights.values()) == Decimal("1.0")
