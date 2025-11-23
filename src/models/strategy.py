"""Allocation strategy models."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class AllocationStrategy:
    """Defines target portfolio weights for asset allocation.

    Attributes:
        name: Strategy name
        asset_weights: Dictionary mapping asset symbols to target weights (must sum to 1.0)
        rebalance_threshold: Optional threshold for drift-based rebalancing (future enhancement)
    """

    name: str
    asset_weights: dict[str, Decimal]
    rebalance_threshold: Optional[Decimal] = None

    def __post_init__(self):
        # Validate name
        if not self.name:
            raise ValueError("name cannot be empty")

        # Validate weights dict
        if not self.asset_weights:
            raise ValueError("asset_weights cannot be empty")

        # Check that weights sum to 1.0 (with tolerance for floating-point errors)
        total_weight = sum(self.asset_weights.values())
        if not (Decimal("0.9999") <= total_weight <= Decimal("1.0001")):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        # Check all weights are non-negative
        if any(w < 0 for w in self.asset_weights.values()):
            raise ValueError("All weights must be non-negative")

        # Validate rebalance threshold if provided
        if self.rebalance_threshold is not None:
            if not (0 < self.rebalance_threshold <= 1):
                raise ValueError("rebalance_threshold must be between 0 and 1")
