"""Calculated weights model for dynamic allocation strategies."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class CalculatedWeights:
    """Result of dynamic weight calculation with metadata for auditability.

    Attributes:
        calculation_date: Date weights were calculated for
        weights: Asset symbol → allocation weight (sum = 1.0)
        strategy_name: Strategy that produced weights
        parameters_snapshot: Parameters used for calculation (JSON-serializable)
        excluded_assets: Assets excluded due to data issues
        used_previous_weights: True if insufficient data, used prior weights
        metadata: Strategy-specific calculation metadata
    """

    calculation_date: date
    weights: dict[str, Decimal]
    strategy_name: str
    parameters_snapshot: dict
    excluded_assets: list[str] = field(default_factory=list)
    used_previous_weights: bool = False
    metadata: dict = field(default_factory=dict)

    def validate(self) -> None:
        """Validate calculated weights meet requirements.

        Raises:
            ValueError: If weights invalid
        """
        # Check sum = 1.0 within tolerance
        # Check all weights non-negative and <= 1.0 first
        for symbol, weight in self.weights.items():
            if weight < 0:
                raise ValueError(f"Weight for {symbol} is negative: {weight}")
            if weight > Decimal("1.0"):
                raise ValueError(f"Weight for {symbol} exceeds 1.0: {weight}")

        # Then check sum
        weight_sum = sum(self.weights.values())
        tolerance = Decimal("0.0001")

        if abs(weight_sum - Decimal("1.0")) > tolerance:
            raise ValueError(
                f"Weights must sum to 1.0 (±{tolerance}), got {weight_sum}"
            )

        # Check calculation_date is valid
        if not isinstance(self.calculation_date, date):
            raise ValueError(
                f"calculation_date must be datetime.date, got {type(self.calculation_date)}"
            )

    def to_dict(self) -> dict:
        """Export to JSON-serializable dict for logging/debugging."""
        return {
            "calculation_date": self.calculation_date.isoformat(),
            "weights": {k: str(v) for k, v in self.weights.items()},
            "strategy_name": self.strategy_name,
            "parameters_snapshot": self.parameters_snapshot,
            "excluded_assets": self.excluded_assets,
            "used_previous_weights": self.used_previous_weights,
            "metadata": self.metadata,
        }

    def get_asset_weight(self, symbol: str) -> Decimal:
        """Get weight for specific asset, return 0 if not present."""
        return self.weights.get(symbol, Decimal("0"))
