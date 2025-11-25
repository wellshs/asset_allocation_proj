"""Unit tests for StrategyParameters classes."""

from decimal import Decimal

import pytest

from src.models.strategy_params import (
    DualMomentumParameters,
    MomentumParameters,
    RiskParityParameters,
    StrategyParameters,
)


class TestStrategyParameters:
    """Test suite for base StrategyParameters."""

    def test_valid_parameters(self):
        """Test creation with valid parameters."""
        params = StrategyParameters(lookback_days=120, assets=["SPY", "AGG", "GLD"])

        params.validate()  # Should not raise
        assert params.lookback_days == 120
        assert len(params.assets) == 3
        assert params.get_required_history_days() == 120

    def test_lookback_must_be_positive(self):
        """Test that lookback_days must be positive."""
        params = StrategyParameters(lookback_days=0, assets=["SPY"])

        with pytest.raises(ValueError, match="must be positive"):
            params.validate()

    def test_lookback_exceeds_maximum(self):
        """Test that lookback_days cannot exceed 500."""
        params = StrategyParameters(lookback_days=600, assets=["SPY"])

        with pytest.raises(ValueError, match="≤ 500"):
            params.validate()

    def test_assets_cannot_be_empty(self):
        """Test that assets list cannot be empty."""
        params = StrategyParameters(lookback_days=120, assets=[])

        with pytest.raises(ValueError, match="at least one asset"):
            params.validate()

    def test_duplicate_assets_rejected(self):
        """Test that duplicate assets are rejected."""
        params = StrategyParameters(lookback_days=120, assets=["SPY", "AGG", "SPY"])

        with pytest.raises(ValueError, match="Duplicate assets"):
            params.validate()

    def test_short_lookback_warning(self):
        """Test warning for lookback < 30 days."""
        params = StrategyParameters(lookback_days=20, assets=["SPY"])

        with pytest.warns(UserWarning, match="may be too short"):
            params.validate()

    def test_long_lookback_warning(self):
        """Test warning for lookback > 252 days."""
        params = StrategyParameters(lookback_days=300, assets=["SPY"])

        with pytest.warns(UserWarning, match="may be too slow"):
            params.validate()


class TestMomentumParameters:
    """Test suite for MomentumParameters."""

    def test_valid_momentum_parameters(self):
        """Test creation with valid momentum parameters."""
        params = MomentumParameters(
            lookback_days=120,
            assets=["SPY", "AGG"],
            exclude_negative=True,
            min_momentum=Decimal("0.05"),
        )

        params.validate()
        assert params.exclude_negative is True
        assert params.min_momentum == Decimal("0.05")

    def test_default_exclude_negative(self):
        """Test that exclude_negative defaults to True."""
        params = MomentumParameters(lookback_days=120, assets=["SPY"])

        assert params.exclude_negative is True

    def test_negative_min_momentum_rejected(self):
        """Test that negative min_momentum is rejected."""
        params = MomentumParameters(
            lookback_days=120, assets=["SPY"], min_momentum=Decimal("-0.1")
        )

        with pytest.raises(ValueError, match="must be non-negative"):
            params.validate()

    def test_min_momentum_none_allowed(self):
        """Test that min_momentum can be None."""
        params = MomentumParameters(
            lookback_days=120, assets=["SPY"], min_momentum=None
        )

        params.validate()  # Should not raise
        assert params.min_momentum is None


class TestRiskParityParameters:
    """Test suite for RiskParityParameters."""

    def test_valid_risk_parity_parameters(self):
        """Test creation with valid risk parity parameters."""
        params = RiskParityParameters(
            lookback_days=120,
            assets=["SPY", "AGG"],
            target_volatility=Decimal("0.12"),
            min_volatility_threshold=Decimal("0.0001"),
            annualization_factor=252,
        )

        params.validate()
        assert params.target_volatility == Decimal("0.12")
        assert params.annualization_factor == 252

    def test_default_min_volatility_threshold(self):
        """Test default min_volatility_threshold."""
        params = RiskParityParameters(lookback_days=120, assets=["SPY"])

        assert params.min_volatility_threshold == Decimal("0.0001")
        assert params.annualization_factor == 252

    def test_target_volatility_too_low_rejected(self):
        """Test that target_volatility < 1% is rejected."""
        params = RiskParityParameters(
            lookback_days=120, assets=["SPY"], target_volatility=Decimal("0.005")
        )

        with pytest.raises(ValueError, match="≥ 0.01"):
            params.validate()

    def test_target_volatility_too_high_rejected(self):
        """Test that target_volatility > 50% is rejected."""
        params = RiskParityParameters(
            lookback_days=120, assets=["SPY"], target_volatility=Decimal("0.60")
        )

        with pytest.raises(ValueError, match="≤ 0.50"):
            params.validate()

    def test_min_volatility_must_be_positive(self):
        """Test that min_volatility_threshold must be positive."""
        params = RiskParityParameters(
            lookback_days=120, assets=["SPY"], min_volatility_threshold=Decimal("0")
        )

        with pytest.raises(ValueError, match="must be positive"):
            params.validate()


class TestDualMomentumParameters:
    """Test suite for DualMomentumParameters."""

    def test_valid_dual_momentum_parameters(self):
        """Test creation with valid dual momentum parameters."""
        params = DualMomentumParameters(
            lookback_days=200,
            assets=["SPY", "AGG"],
            short_window=50,
            long_window=200,
            use_signal_strength=False,
        )

        params.validate()
        assert params.short_window == 50
        assert params.long_window == 200
        assert params.get_required_history_days() == 200

    def test_short_window_must_be_positive(self):
        """Test that short_window must be positive."""
        params = DualMomentumParameters(
            lookback_days=200, assets=["SPY"], short_window=0, long_window=200
        )

        with pytest.raises(ValueError, match="short_window must be positive"):
            params.validate()

    def test_short_must_be_less_than_long(self):
        """Test that short_window < long_window."""
        params = DualMomentumParameters(
            lookback_days=200, assets=["SPY"], short_window=200, long_window=200
        )

        with pytest.raises(ValueError, match="must be < long_window"):
            params.validate()

    def test_lookback_must_exceed_long_window(self):
        """Test that lookback_days >= long_window."""
        params = DualMomentumParameters(
            lookback_days=100, assets=["SPY"], short_window=50, long_window=200
        )

        with pytest.raises(ValueError, match="must be ≥ long_window"):
            params.validate()

    def test_get_required_history_returns_long_window(self):
        """Test that required history is long_window."""
        params = DualMomentumParameters(
            lookback_days=200, assets=["SPY"], short_window=50, long_window=200
        )

        assert params.get_required_history_days() == 200
