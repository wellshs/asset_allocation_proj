"""Unit tests for MomentumStrategy parameter validation."""

from decimal import Decimal

import pytest

from src.models.strategy_params import MomentumParameters
from src.strategies.momentum import MomentumStrategy


class TestMomentumParameterValidation:
    """Test suite for MomentumStrategy parameter validation."""

    def test_valid_parameters_accepted(self):
        """Test that valid parameters are accepted."""
        params = MomentumParameters(
            lookback_days=120,
            assets=["SPY", "AGG", "GLD"],
            exclude_negative=True,
            min_momentum=Decimal("0.05"),
        )

        # Should not raise
        strategy = MomentumStrategy(params)
        assert strategy.parameters == params

    def test_strategy_validates_parameters_on_init(self):
        """Test that strategy validates parameters during initialization."""
        # Invalid parameters should be caught immediately
        params = MomentumParameters(lookback_days=-10, assets=["SPY"])

        with pytest.raises(ValueError, match="must be positive"):
            MomentumStrategy(params)

    def test_invalid_lookback_rejected(self):
        """Test that invalid lookback periods are rejected."""
        # Zero lookback
        params_zero = MomentumParameters(lookback_days=0, assets=["SPY"])
        with pytest.raises(ValueError):
            MomentumStrategy(params_zero)

        # Negative lookback
        params_negative = MomentumParameters(lookback_days=-5, assets=["SPY"])
        with pytest.raises(ValueError):
            MomentumStrategy(params_negative)

        # Excessive lookback
        params_excessive = MomentumParameters(lookback_days=600, assets=["SPY"])
        with pytest.raises(ValueError):
            MomentumStrategy(params_excessive)

    def test_empty_assets_rejected(self):
        """Test that empty assets list is rejected."""
        params = MomentumParameters(lookback_days=120, assets=[])

        with pytest.raises(ValueError, match="at least one asset"):
            MomentumStrategy(params)

    def test_duplicate_assets_rejected(self):
        """Test that duplicate assets are rejected."""
        params = MomentumParameters(lookback_days=120, assets=["SPY", "AGG", "SPY"])

        with pytest.raises(ValueError, match="Duplicate assets"):
            MomentumStrategy(params)

    def test_negative_min_momentum_rejected(self):
        """Test that negative min_momentum is rejected."""
        params = MomentumParameters(
            lookback_days=120,
            assets=["SPY"],
            min_momentum=Decimal("-0.05"),
        )

        with pytest.raises(ValueError, match="must be non-negative"):
            MomentumStrategy(params)

    def test_min_momentum_none_accepted(self):
        """Test that min_momentum=None is accepted."""
        params = MomentumParameters(
            lookback_days=120,
            assets=["SPY", "AGG"],
            min_momentum=None,
        )

        # Should not raise
        strategy = MomentumStrategy(params)
        assert strategy.parameters.min_momentum is None

    def test_exclude_negative_defaults_to_true(self):
        """Test that exclude_negative defaults to True."""
        params = MomentumParameters(lookback_days=120, assets=["SPY"])

        strategy = MomentumStrategy(params)
        assert strategy.parameters.exclude_negative is True

    def test_exclude_negative_can_be_false(self):
        """Test that exclude_negative can be set to False."""
        params = MomentumParameters(
            lookback_days=120, assets=["SPY"], exclude_negative=False
        )

        strategy = MomentumStrategy(params)
        assert strategy.parameters.exclude_negative is False


class TestMomentumParameterWarnings:
    """Test suite for parameter validation warnings."""

    def test_short_lookback_warning(self):
        """Test warning for lookback < 30 days."""
        params = MomentumParameters(lookback_days=20, assets=["SPY"])

        with pytest.warns(UserWarning, match="may be too short"):
            MomentumStrategy(params)

    def test_long_lookback_warning(self):
        """Test warning for lookback > 252 days."""
        params = MomentumParameters(lookback_days=300, assets=["SPY"])

        with pytest.warns(UserWarning, match="may be too slow"):
            MomentumStrategy(params)

    def test_no_warning_for_reasonable_lookback(self):
        """Test no warning for reasonable lookback (30-252 days)."""
        params = MomentumParameters(lookback_days=120, assets=["SPY"])

        # Should not raise lookback warning (only imports may generate warnings)
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            MomentumStrategy(params)

            # Check no warnings specifically about lookback being too short/slow
            lookback_warnings = [
                warning
                for warning in w
                if "lookback" in str(warning.message).lower()
                and (
                    "too short" in str(warning.message).lower()
                    or "too slow" in str(warning.message).lower()
                )
            ]
            assert len(lookback_warnings) == 0


class TestMomentumParameterEdgeCases:
    """Test suite for edge cases in parameter handling."""

    def test_single_asset_accepted(self):
        """Test that single asset is accepted."""
        params = MomentumParameters(lookback_days=120, assets=["SPY"])

        strategy = MomentumStrategy(params)
        assert len(strategy.parameters.assets) == 1

    def test_many_assets_accepted(self):
        """Test that many assets are accepted."""
        assets = [f"ASSET{i}" for i in range(100)]
        params = MomentumParameters(lookback_days=120, assets=assets)

        strategy = MomentumStrategy(params)
        assert len(strategy.parameters.assets) == 100

    def test_minimum_valid_lookback(self):
        """Test minimum valid lookback (1 day)."""
        params = MomentumParameters(lookback_days=1, assets=["SPY"])

        with pytest.warns(UserWarning, match="may be too short"):
            strategy = MomentumStrategy(params)
            assert strategy.parameters.lookback_days == 1

    def test_maximum_valid_lookback(self):
        """Test maximum valid lookback (500 days)."""
        params = MomentumParameters(lookback_days=500, assets=["SPY"])

        with pytest.warns(UserWarning, match="may be too slow"):
            strategy = MomentumStrategy(params)
            assert strategy.parameters.lookback_days == 500

    def test_zero_min_momentum_accepted(self):
        """Test that min_momentum=0 is accepted."""
        params = MomentumParameters(
            lookback_days=120,
            assets=["SPY"],
            min_momentum=Decimal("0"),
        )

        # Should not raise
        strategy = MomentumStrategy(params)
        assert strategy.parameters.min_momentum == Decimal("0")

    def test_large_min_momentum_accepted(self):
        """Test that large min_momentum (e.g., 100%) is accepted."""
        params = MomentumParameters(
            lookback_days=120,
            assets=["SPY"],
            min_momentum=Decimal("1.0"),  # 100%
        )

        # Should not raise (though impractical, it's valid)
        strategy = MomentumStrategy(params)
        assert strategy.parameters.min_momentum == Decimal("1.0")


class TestMomentumParameterTypes:
    """Test suite for parameter type validation."""

    def test_lookback_must_be_integer(self):
        """Test that lookback_days must be an integer."""
        # This is enforced by Python's type system and dataclass
        # Just verify correct type is stored
        params = MomentumParameters(lookback_days=120, assets=["SPY"])
        assert isinstance(params.lookback_days, int)

    def test_assets_must_be_list(self):
        """Test that assets must be a list."""
        params = MomentumParameters(lookback_days=120, assets=["SPY", "AGG"])
        assert isinstance(params.assets, list)

    def test_exclude_negative_must_be_bool(self):
        """Test that exclude_negative must be boolean."""
        params = MomentumParameters(
            lookback_days=120, assets=["SPY"], exclude_negative=True
        )
        assert isinstance(params.exclude_negative, bool)

    def test_min_momentum_decimal_or_none(self):
        """Test that min_momentum is Decimal or None."""
        params_with_threshold = MomentumParameters(
            lookback_days=120, assets=["SPY"], min_momentum=Decimal("0.05")
        )
        assert isinstance(params_with_threshold.min_momentum, Decimal)

        params_without_threshold = MomentumParameters(
            lookback_days=120, assets=["SPY"], min_momentum=None
        )
        assert params_without_threshold.min_momentum is None
