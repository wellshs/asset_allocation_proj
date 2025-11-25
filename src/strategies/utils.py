"""Shared calculation utilities for dynamic allocation strategies."""

from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    import pandas as pd


def normalize_weights(
    raw_weights: dict[str, float], tolerance: Decimal = Decimal("0.0001")
) -> dict[str, Decimal]:
    """Normalize raw weights to sum to 1.0.

    Args:
        raw_weights: Dict of asset → raw weight (can be any positive values)
        tolerance: Maximum acceptable deviation from 1.0

    Returns:
        Dict of asset → Decimal weight (sum = 1.0)

    Raises:
        ValueError: If all weights are zero or negative
    """
    total = sum(raw_weights.values())

    if total <= 0:
        raise ValueError("Cannot normalize: all weights are zero or negative")

    # Normalize to sum = 1.0 and convert to Decimal with 4 decimal places
    normalized = {
        asset: Decimal(str(weight / total)).quantize(Decimal("0.0001"))
        for asset, weight in raw_weights.items()
    }

    # Verify sum and adjust if necessary to ensure exact sum = 1.0
    weight_sum = sum(normalized.values())
    if weight_sum != Decimal("1.0"):
        # Adjust last asset to ensure exact sum (last in insertion order)
        assets = list(normalized.keys())
        last_asset = assets[-1]
        adjustment = Decimal("1.0") - weight_sum
        normalized[last_asset] += adjustment

    return normalized


def filter_complete_assets(
    window_data: "pd.DataFrame", required_days: int
) -> list[str]:
    """Return list of assets with complete data in window.

    Args:
        window_data: DataFrame with date index, asset columns
        required_days: Minimum number of non-null observations required

    Returns:
        List of asset symbols with complete data
    """
    complete_assets = []

    for symbol in window_data.columns:
        non_null_count = window_data[symbol].notna().sum()
        if non_null_count >= required_days:
            complete_assets.append(symbol)

    return complete_assets
