"""Strategy parameter models for dynamic allocation strategies."""

import warnings
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class StrategyParameters:
    """Base configuration for all dynamic strategies.

    Attributes:
        lookback_days: Historical data window size
        assets: Asset symbols to allocate
    """

    lookback_days: int
    assets: list[str]

    def validate(self) -> None:
        """Validate common parameters.

        Raises:
            ValueError: If validation fails
        """
        # Lookback days must be positive
        if self.lookback_days < 1:
            raise ValueError(
                f"lookback_days must be positive, got {self.lookback_days}"
            )

        # Lookback days must be in reasonable range
        if self.lookback_days > 500:
            raise ValueError(
                f"lookback_days must be ≤ 500 (likely error), got {self.lookback_days}"
            )

        # Warn if lookback is too short or too long
        if self.lookback_days < 30:
            warnings.warn(
                f"lookback_days={self.lookback_days} may be too short for stable estimates "
                "(recommended ≥ 30)"
            )

        if self.lookback_days > 252:
            warnings.warn(
                f"lookback_days={self.lookback_days} may be too slow to adapt "
                "(recommended ≤ 252)"
            )

        # Assets list must not be empty
        if not self.assets:
            raise ValueError("Must specify at least one asset")

        # Assets must be unique
        if len(self.assets) != len(set(self.assets)):
            raise ValueError("Duplicate assets not allowed")

    def get_required_history_days(self) -> int:
        """Calculate minimum historical data required.

        Returns:
            Number of days needed before first calculation
        """
        return self.lookback_days


@dataclass
class MomentumParameters(StrategyParameters):
    """Configuration for momentum-based strategy.

    Attributes:
        exclude_negative: Zero out assets with negative momentum
        min_momentum: Minimum momentum to include asset (if set)
    """

    exclude_negative: bool = True
    min_momentum: Optional[Decimal] = None

    def validate(self) -> None:
        """Validate momentum-specific parameters."""
        super().validate()

        # If min_momentum is set, must be non-negative
        if self.min_momentum is not None and self.min_momentum < 0:
            raise ValueError(
                f"min_momentum must be non-negative, got {self.min_momentum}"
            )


@dataclass
class RiskParityParameters(StrategyParameters):
    """Configuration for volatility-adjusted (risk parity) strategy.

    Attributes:
        target_volatility: Target portfolio volatility (annualized), optional
        min_volatility_threshold: Minimum volatility to include asset
        annualization_factor: Trading days per year for annualizing
    """

    target_volatility: Optional[Decimal] = None
    min_volatility_threshold: Decimal = Decimal("0.0001")
    annualization_factor: int = 252

    def validate(self) -> None:
        """Validate risk parity-specific parameters."""
        super().validate()

        # If target_volatility is set, must be in reasonable range
        if self.target_volatility is not None:
            if self.target_volatility < Decimal("0.01"):
                raise ValueError(
                    f"target_volatility must be ≥ 0.01 (1%), got {self.target_volatility}"
                )
            if self.target_volatility > Decimal("0.50"):
                raise ValueError(
                    f"target_volatility must be ≤ 0.50 (50%), got {self.target_volatility}"
                )

        # min_volatility_threshold must be positive
        if self.min_volatility_threshold <= 0:
            raise ValueError(
                f"min_volatility_threshold must be positive, got {self.min_volatility_threshold}"
            )

        # annualization_factor must be positive
        if self.annualization_factor <= 0:
            raise ValueError(
                f"annualization_factor must be positive, got {self.annualization_factor}"
            )


@dataclass
class DualMomentumParameters(StrategyParameters):
    """Configuration for dual moving average strategy.

    Attributes:
        short_window: Short-term moving average period
        long_window: Long-term moving average period
        use_signal_strength: Weight by signal strength (vs binary)
    """

    short_window: int = 0  # Required, no default
    long_window: int = 0  # Required, no default
    use_signal_strength: bool = False

    def validate(self) -> None:
        """Validate dual momentum-specific parameters."""
        super().validate()

        # Windows must be positive
        if self.short_window < 1:
            raise ValueError(f"short_window must be positive, got {self.short_window}")
        if self.long_window < 1:
            raise ValueError(f"long_window must be positive, got {self.long_window}")

        # Short window must be less than long window
        if self.short_window >= self.long_window:
            raise ValueError(
                f"short_window ({self.short_window}) must be < long_window ({self.long_window})"
            )

        # lookback_days must be >= long_window
        if self.lookback_days < self.long_window:
            raise ValueError(
                f"lookback_days ({self.lookback_days}) must be ≥ long_window ({self.long_window})"
            )

    def get_required_history_days(self) -> int:
        """Return long window as minimum required history."""
        return self.long_window
