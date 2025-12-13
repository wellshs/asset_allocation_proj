"""Unit tests for StrategyParameters classes."""

from decimal import Decimal

import pytest

from src.models.strategy_params import (
    DualMomentumParameters,
    InfiniteBuyingParameters,
    MomentumParameters,
    RiskParityParameters,
    StrategyParameters,
    ValueRebalancingParameters,
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


class TestInfiniteBuyingParameters:
    """Test suite for InfiniteBuyingParameters."""

    def test_valid_infinite_buying_parameters(self):
        """Test creation with valid infinite buying parameters."""
        params = InfiniteBuyingParameters(
            lookback_days=30,
            assets=["TQQQ"],
            divisions=40,
            take_profit_pct=Decimal("0.10"),
            phase_threshold=Decimal("0.50"),
        )

        params.validate()
        assert params.divisions == 40
        assert params.take_profit_pct == Decimal("0.10")
        assert params.phase_threshold == Decimal("0.50")

    def test_defaults(self):
        """Test default values."""
        params = InfiniteBuyingParameters(lookback_days=30, assets=["TQQQ"])

        params.validate()
        assert params.divisions == 40
        assert params.take_profit_pct == Decimal("0.10")
        assert params.phase_threshold == Decimal("0.50")
        assert params.use_rsi is False
        assert params.rsi_threshold == 30
        assert params.conservative_buy_only_below_avg is True

    def test_single_asset_only(self):
        """Test that multiple assets are rejected."""
        params = InfiniteBuyingParameters(
            lookback_days=30, assets=["TQQQ", "SOXL"], divisions=40
        )

        with pytest.raises(ValueError, match="only supports single asset"):
            params.validate()

    def test_divisions_must_be_positive(self):
        """Test that divisions must be positive."""
        params = InfiniteBuyingParameters(
            lookback_days=30, assets=["TQQQ"], divisions=0
        )

        with pytest.raises(ValueError, match="divisions must be positive"):
            params.validate()

    def test_high_divisions_warning(self):
        """Test warning for divisions > 100."""
        params = InfiniteBuyingParameters(
            lookback_days=30, assets=["TQQQ"], divisions=150
        )

        with pytest.warns(UserWarning, match="divisions=150 is very high"):
            params.validate()

    def test_take_profit_must_be_positive(self):
        """Test that take_profit_pct must be positive."""
        params = InfiniteBuyingParameters(
            lookback_days=30, assets=["TQQQ"], take_profit_pct=Decimal("0")
        )

        with pytest.raises(ValueError, match="take_profit_pct must be positive"):
            params.validate()

    def test_phase_threshold_range(self):
        """Test that phase_threshold must be between 0 and 1."""
        # Too low
        params = InfiniteBuyingParameters(
            lookback_days=30, assets=["TQQQ"], phase_threshold=Decimal("0")
        )
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            params.validate()

        # Too high
        params = InfiniteBuyingParameters(
            lookback_days=30, assets=["TQQQ"], phase_threshold=Decimal("1.0")
        )
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            params.validate()

    def test_rsi_threshold_validation(self):
        """Test RSI threshold validation when use_rsi is True."""
        # Invalid RSI threshold
        params = InfiniteBuyingParameters(
            lookback_days=30, assets=["TQQQ"], use_rsi=True, rsi_threshold=0
        )
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            params.validate()

        params = InfiniteBuyingParameters(
            lookback_days=30, assets=["TQQQ"], use_rsi=True, rsi_threshold=100
        )
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            params.validate()

    def test_split_sell_percentages_must_sum_to_one(self):
        """Test that split sell percentages must sum to 1.0."""
        params = InfiniteBuyingParameters(
            lookback_days=30,
            assets=["TQQQ"],
            split_sell_pct_1=Decimal("0.3"),
            split_sell_pct_2=Decimal("0.5"),
        )

        with pytest.raises(ValueError, match="must sum to 1.0"):
            params.validate()


class TestValueRebalancingParameters:
    """Test suite for ValueRebalancingParameters."""

    def test_valid_value_rebalancing_parameters(self):
        """Test creation with valid value rebalancing parameters."""
        params = ValueRebalancingParameters(
            lookback_days=30,
            assets=["SPY"],
            initial_capital=Decimal("10000"),
            gradient=Decimal("10"),
            upper_band_pct=Decimal("0.05"),
            lower_band_pct=Decimal("0.05"),
        )

        params.validate()
        assert params.initial_capital == Decimal("10000")
        assert params.gradient == Decimal("10")
        assert params.upper_band_pct == Decimal("0.05")

    def test_defaults(self):
        """Test default values."""
        params = ValueRebalancingParameters(lookback_days=30, assets=["SPY"])

        params.validate()
        assert params.initial_capital == Decimal("10000")
        assert params.gradient == Decimal("10")
        assert params.upper_band_pct == Decimal("0.05")
        assert params.lower_band_pct == Decimal("0.05")
        assert params.rebalance_frequency == 30
        assert params.value_growth_rate == Decimal("0.10")

    def test_single_asset_only(self):
        """Test that multiple assets are rejected."""
        params = ValueRebalancingParameters(
            lookback_days=30, assets=["SPY", "QQQ"], initial_capital=Decimal("10000")
        )

        with pytest.raises(ValueError, match="only supports single asset"):
            params.validate()

    def test_initial_capital_must_be_positive(self):
        """Test that initial_capital must be positive."""
        params = ValueRebalancingParameters(
            lookback_days=30, assets=["SPY"], initial_capital=Decimal("0")
        )

        with pytest.raises(ValueError, match="initial_capital must be positive"):
            params.validate()

    def test_gradient_must_be_positive(self):
        """Test that gradient must be positive."""
        params = ValueRebalancingParameters(
            lookback_days=30, assets=["SPY"], gradient=Decimal("0")
        )

        with pytest.raises(ValueError, match="gradient must be positive"):
            params.validate()

    def test_band_percentages_must_be_positive(self):
        """Test that band percentages must be positive."""
        # Upper band
        params = ValueRebalancingParameters(
            lookback_days=30, assets=["SPY"], upper_band_pct=Decimal("0")
        )
        with pytest.raises(ValueError, match="upper_band_pct must be positive"):
            params.validate()

        # Lower band
        params = ValueRebalancingParameters(
            lookback_days=30, assets=["SPY"], lower_band_pct=Decimal("0")
        )
        with pytest.raises(ValueError, match="lower_band_pct must be positive"):
            params.validate()

    def test_rebalance_frequency_must_be_positive(self):
        """Test that rebalance_frequency must be positive."""
        params = ValueRebalancingParameters(
            lookback_days=30, assets=["SPY"], rebalance_frequency=0
        )

        with pytest.raises(ValueError, match="rebalance_frequency must be positive"):
            params.validate()

    def test_growth_rate_range(self):
        """Test that value_growth_rate must be in reasonable range."""
        # Too low
        params = ValueRebalancingParameters(
            lookback_days=30, assets=["SPY"], value_growth_rate=Decimal("-0.6")
        )
        with pytest.raises(ValueError, match="must be between -0.5 and 1.0"):
            params.validate()

        # Too high
        params = ValueRebalancingParameters(
            lookback_days=30, assets=["SPY"], value_growth_rate=Decimal("1.5")
        )
        with pytest.raises(ValueError, match="must be between -0.5 and 1.0"):
            params.validate()
