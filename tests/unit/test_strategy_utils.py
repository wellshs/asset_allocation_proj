"""Unit tests for strategy utilities."""

from decimal import Decimal

import pandas as pd
import pytest

from src.strategies.utils import filter_complete_assets, normalize_weights


class TestNormalizeWeights:
    """Test suite for normalize_weights function."""

    def test_normalize_positive_weights(self):
        """Test normalization of positive weights."""
        raw_weights = {"SPY": 10.0, "AGG": 5.0, "GLD": 2.0}

        normalized = normalize_weights(raw_weights)

        # Should sum to 1.0
        assert sum(normalized.values()) == Decimal("1.0")

        # Check proportions (10:5:2 = 0.588:0.294:0.118)
        assert abs(normalized["SPY"] - Decimal("0.5882")) <= Decimal("0.0001")
        assert abs(normalized["AGG"] - Decimal("0.2941")) <= Decimal("0.0001")
        assert abs(normalized["GLD"] - Decimal("0.1176")) <= Decimal("0.0001")

    def test_normalize_equal_weights(self):
        """Test normalization with equal weights."""
        raw_weights = {"SPY": 1.0, "AGG": 1.0, "GLD": 1.0}

        normalized = normalize_weights(raw_weights)

        assert normalized["SPY"] == Decimal("0.3333")
        assert normalized["AGG"] == Decimal("0.3333")
        assert normalized["GLD"] == Decimal("0.3334")  # Adjusted for sum = 1.0
        assert sum(normalized.values()) == Decimal("1.0")

    def test_normalize_single_asset(self):
        """Test normalization with single asset."""
        raw_weights = {"SPY": 100.0}

        normalized = normalize_weights(raw_weights)

        assert normalized["SPY"] == Decimal("1.0")

    def test_all_zero_weights_raises_error(self):
        """Test error when all weights are zero."""
        raw_weights = {"SPY": 0.0, "AGG": 0.0}

        with pytest.raises(ValueError, match="all weights are zero or negative"):
            normalize_weights(raw_weights)

    def test_negative_weights_raises_error(self):
        """Test error when sum is negative."""
        raw_weights = {"SPY": -5.0, "AGG": 2.0}

        with pytest.raises(ValueError, match="all weights are zero or negative"):
            normalize_weights(raw_weights)

    def test_weights_sum_to_exactly_one(self):
        """Test that normalized weights sum to exactly 1.0."""
        # Use weights that might cause rounding issues
        raw_weights = {"A": 1.0, "B": 1.0, "C": 1.0}

        normalized = normalize_weights(raw_weights)

        # Must be exactly 1.0, not 0.9999 or 1.0001
        assert sum(normalized.values()) == Decimal("1.0")

    def test_decimal_precision_four_places(self):
        """Test that weights are rounded to 4 decimal places."""
        raw_weights = {"SPY": 0.123456789, "AGG": 1.0}

        normalized = normalize_weights(raw_weights)

        # Check that values have at most 4 decimal places
        for weight in normalized.values():
            # Convert to string and check decimal places
            weight_str = str(weight)
            if "." in weight_str:
                decimal_part = weight_str.split(".")[1]
                assert len(decimal_part) <= 4


class TestFilterCompleteAssets:
    """Test suite for filter_complete_assets function."""

    def test_all_assets_complete(self):
        """Test when all assets have complete data."""
        window_data = pd.DataFrame(
            {"SPY": [100.0, 102.0, 105.0], "AGG": [110.0, 111.0, 112.0]},
            index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        )

        complete = filter_complete_assets(window_data, required_days=3)

        assert "SPY" in complete
        assert "AGG" in complete
        assert len(complete) == 2

    def test_some_assets_incomplete(self):
        """Test filtering when some assets have missing data."""
        window_data = pd.DataFrame(
            {
                "SPY": [100.0, 102.0, 105.0],
                "AGG": [110.0, None, 112.0],  # Missing data
                "GLD": [150.0, 148.0, 145.0],
            },
            index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        )

        complete = filter_complete_assets(window_data, required_days=3)

        assert "SPY" in complete
        assert "GLD" in complete
        assert "AGG" not in complete  # Has missing data
        assert len(complete) == 2

    def test_required_days_threshold(self):
        """Test filtering with required_days threshold."""
        window_data = pd.DataFrame(
            {
                "SPY": [100.0, 102.0, None, 108.0, 110.0],  # 4 non-null
                "AGG": [110.0, 111.0, 112.0, 113.0, 114.0],  # 5 non-null
            },
            index=pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05"]
            ),
        )

        # Require 5 days - only AGG qualifies
        complete = filter_complete_assets(window_data, required_days=5)
        assert "AGG" in complete
        assert "SPY" not in complete
        assert len(complete) == 1

        # Require 4 days - both qualify
        complete = filter_complete_assets(window_data, required_days=4)
        assert "SPY" in complete
        assert "AGG" in complete
        assert len(complete) == 2

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        window_data = pd.DataFrame()

        complete = filter_complete_assets(window_data, required_days=1)

        assert len(complete) == 0

    def test_all_assets_incomplete(self):
        """Test when no assets meet the threshold."""
        window_data = pd.DataFrame(
            {"SPY": [100.0, None, None], "AGG": [None, 111.0, None]},
            index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        )

        complete = filter_complete_assets(window_data, required_days=3)

        assert len(complete) == 0
