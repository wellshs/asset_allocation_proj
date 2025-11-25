"""Unit tests for CalculatedWeights model."""

from datetime import date
from decimal import Decimal

import pytest

from src.models.calculated_weights import CalculatedWeights


class TestCalculatedWeights:
    """Test suite for CalculatedWeights model."""

    def test_valid_weights(self):
        """Test creation with valid weights that sum to 1.0."""
        weights = CalculatedWeights(
            calculation_date=date(2020, 6, 15),
            weights={
                "SPY": Decimal("0.6000"),
                "AGG": Decimal("0.3000"),
                "GLD": Decimal("0.1000"),
            },
            strategy_name="test_strategy",
            parameters_snapshot={"lookback_days": 120},
        )

        weights.validate()  # Should not raise

        assert weights.calculation_date == date(2020, 6, 15)
        assert len(weights.weights) == 3
        assert weights.get_asset_weight("SPY") == Decimal("0.6000")
        assert weights.get_asset_weight("UNKNOWN") == Decimal("0")

    def test_weights_must_sum_to_one(self):
        """Test that weights must sum to 1.0 within tolerance."""
        weights = CalculatedWeights(
            calculation_date=date(2020, 6, 15),
            weights={
                "SPY": Decimal("0.5000"),
                "AGG": Decimal("0.3000"),
            },  # Sum = 0.8, not 1.0
            strategy_name="test_strategy",
            parameters_snapshot={},
        )

        with pytest.raises(ValueError, match="must sum to 1.0"):
            weights.validate()

    def test_negative_weight_rejected(self):
        """Test that negative weights are rejected."""
        weights = CalculatedWeights(
            calculation_date=date(2020, 6, 15),
            weights={
                "SPY": Decimal("0.6"),
                "AGG": Decimal("-0.1"),  # Negative!
                "GLD": Decimal("0.5"),
            },
            strategy_name="test_strategy",
            parameters_snapshot={},
        )

        with pytest.raises(ValueError, match="is negative"):
            weights.validate()

    def test_weight_exceeds_one_rejected(self):
        """Test that weights > 1.0 are rejected."""
        weights = CalculatedWeights(
            calculation_date=date(2020, 6, 15),
            weights={"SPY": Decimal("1.5")},  # Exceeds 1.0!
            strategy_name="test_strategy",
            parameters_snapshot={},
        )

        with pytest.raises(ValueError, match="exceeds 1.0"):
            weights.validate()

    def test_to_dict_serialization(self):
        """Test conversion to JSON-serializable dict."""
        weights = CalculatedWeights(
            calculation_date=date(2020, 6, 15),
            weights={"SPY": Decimal("0.6"), "AGG": Decimal("0.4")},
            strategy_name="momentum_120d",
            parameters_snapshot={"lookback_days": 120},
            excluded_assets=["GLD"],
            used_previous_weights=False,
            metadata={"momentum_scores": {"SPY": 0.15, "AGG": 0.05}},
        )

        result = weights.to_dict()

        assert result["calculation_date"] == "2020-06-15"
        assert result["weights"]["SPY"] == "0.6"
        assert result["strategy_name"] == "momentum_120d"
        assert result["excluded_assets"] == ["GLD"]
        assert result["used_previous_weights"] is False

    def test_excluded_assets_default(self):
        """Test that excluded_assets defaults to empty list."""
        weights = CalculatedWeights(
            calculation_date=date(2020, 6, 15),
            weights={"SPY": Decimal("1.0")},
            strategy_name="test",
            parameters_snapshot={},
        )

        assert weights.excluded_assets == []
        assert weights.used_previous_weights is False
        assert weights.metadata == {}

    def test_cash_allocation(self):
        """Test 100% cash allocation (all-negative momentum scenario)."""
        weights = CalculatedWeights(
            calculation_date=date(2020, 6, 15),
            weights={"CASH": Decimal("1.0")},
            strategy_name="momentum",
            parameters_snapshot={},
            excluded_assets=["SPY", "AGG", "GLD"],
        )

        weights.validate()  # Should pass
        assert weights.get_asset_weight("CASH") == Decimal("1.0")
        assert len(weights.excluded_assets) == 3
