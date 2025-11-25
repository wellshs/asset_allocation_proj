"""Unit tests for PriceWindow utility."""

from datetime import date

import pandas as pd
import pytest

from src.backtesting.price_window import (
    InsufficientDataError,
    PriceWindow,
    get_price_window,
)


class TestPriceWindow:
    """Test suite for PriceWindow class."""

    def test_valid_price_window(self):
        """Test creation of valid price window."""
        prices_df = pd.DataFrame(
            {
                "SPY": [100.0, 102.0, 105.0],
                "AGG": [110.0, 111.0, 112.0],
            },
            index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        )

        window = PriceWindow(
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 3),
            prices=prices_df,
            num_days=3,
        )

        window.validate()
        assert window.num_days == 3
        assert window.has_complete_data("SPY")
        assert window.has_complete_data("AGG")

    def test_get_asset_prices(self):
        """Test retrieving prices for specific asset."""
        prices_df = pd.DataFrame(
            {"SPY": [100.0, 102.0], "AGG": [110.0, 111.0]},
            index=pd.to_datetime(["2020-01-01", "2020-01-02"]),
        )

        window = PriceWindow(
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 2),
            prices=prices_df,
            num_days=2,
        )

        spy_prices = window.get_asset_prices("SPY")
        assert len(spy_prices) == 2
        assert spy_prices.iloc[0] == 100.0

    def test_get_asset_prices_missing_symbol(self):
        """Test error when requesting non-existent asset."""
        prices_df = pd.DataFrame({"SPY": [100.0]}, index=pd.to_datetime(["2020-01-01"]))

        window = PriceWindow(
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 1),
            prices=prices_df,
            num_days=1,
        )

        with pytest.raises(ValueError, match="not found"):
            window.get_asset_prices("UNKNOWN")

    def test_has_complete_data_with_missing(self):
        """Test detection of incomplete data."""
        prices_df = pd.DataFrame(
            {"SPY": [100.0, 102.0, None], "AGG": [110.0, 111.0, 112.0]},
            index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        )

        window = PriceWindow(
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 3),
            prices=prices_df,
            num_days=3,
        )

        assert not window.has_complete_data("SPY")  # Has None
        assert window.has_complete_data("AGG")  # Complete

    def test_get_complete_assets(self):
        """Test filtering to complete assets only."""
        prices_df = pd.DataFrame(
            {
                "SPY": [100.0, 102.0, 105.0],
                "AGG": [110.0, None, 112.0],
                "GLD": [150.0, 148.0, 145.0],
            },
            index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        )

        window = PriceWindow(
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 3),
            prices=prices_df,
            num_days=3,
        )

        complete = window.get_complete_assets()
        assert "SPY" in complete
        assert "GLD" in complete
        assert "AGG" not in complete  # Has missing data

    def test_validate_rejects_empty_dataframe(self):
        """Test validation rejects empty DataFrame."""
        window = PriceWindow(
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 3),
            prices=pd.DataFrame(),
            num_days=0,
        )

        with pytest.raises(ValueError, match="empty"):
            window.validate()

    def test_validate_rejects_invalid_date_range(self):
        """Test validation rejects end_date <= start_date."""
        prices_df = pd.DataFrame({"SPY": [100.0]}, index=pd.to_datetime(["2020-01-01"]))

        window = PriceWindow(
            start_date=date(2020, 1, 3),
            end_date=date(2020, 1, 1),  # Before start!
            prices=prices_df,
            num_days=1,
        )

        with pytest.raises(ValueError, match="must be after start_date"):
            window.validate()

    def test_validate_rejects_negative_prices(self):
        """Test validation rejects negative prices."""
        prices_df = pd.DataFrame(
            {"SPY": [100.0, -10.0]}, index=pd.to_datetime(["2020-01-01", "2020-01-02"])
        )

        window = PriceWindow(
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 2),
            prices=prices_df,
            num_days=2,
        )

        with pytest.raises(ValueError, match="negative prices"):
            window.validate()


class TestGetPriceWindow:
    """Test suite for get_price_window function."""

    def test_extract_valid_window(self):
        """Test extracting valid price window."""
        # Create sample price data
        prices_df = pd.DataFrame(
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
                "price": [100.0, 110.0, 102.0, 111.0, 105.0, 112.0],
            }
        )

        window = get_price_window(
            prices_df=prices_df,
            calculation_date=date(2020, 1, 4),
            lookback_days=3,
            assets=["SPY", "AGG"],
        )

        assert window.num_days == 3
        assert "SPY" in window.prices.columns
        assert "AGG" in window.prices.columns

    def test_insufficient_data_raises_error(self):
        """Test error when insufficient data available."""
        prices_df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
                "symbol": ["SPY", "SPY"],
                "price": [100.0, 102.0],
            }
        )

        with pytest.raises(InsufficientDataError, match="only 2 days available"):
            get_price_window(
                prices_df=prices_df,
                calculation_date=date(2020, 1, 4),
                lookback_days=5,  # Need 5 but only 2 available
                assets=["SPY"],
            )

    def test_excludes_future_data(self):
        """Test that data on/after calculation_date is excluded."""
        prices_df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]
                ),
                "symbol": ["SPY"] * 4,
                "price": [100.0, 102.0, 105.0, 108.0],
            }
        )

        window = get_price_window(
            prices_df=prices_df,
            calculation_date=date(2020, 1, 3),  # Should exclude 01-03 and 01-04
            lookback_days=2,
            assets=["SPY"],
        )

        assert window.num_days == 2
        # Should only have 01-01 and 01-02
        assert window.end_date == date(2020, 1, 2)
