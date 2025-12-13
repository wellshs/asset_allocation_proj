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


@dataclass
class InfiniteBuyingParameters(StrategyParameters):
    """Configuration for Infinite Buying Method (무한매수법).

    Attributes:
        divisions: Number of capital divisions (default: 40)
        take_profit_pct: Take profit percentage above average (default: 10%)
        phase_threshold: Progress threshold for switching to conservative phase (default: 50%)
        use_rsi: Whether to use RSI indicator for entry timing
        rsi_threshold: RSI threshold for entry (if use_rsi=True)
        conservative_buy_only_below_avg: In phase 2, only buy below average price
        split_sell_pct_1: First partial sell percentage at +5%
        split_sell_pct_2: Second partial sell percentage at +10%
    """

    divisions: int = 40
    take_profit_pct: Decimal = Decimal("0.10")  # 10%
    phase_threshold: Decimal = Decimal("0.50")  # 50%
    use_rsi: bool = False
    rsi_threshold: int = 30
    conservative_buy_only_below_avg: bool = True
    split_sell_pct_1: Decimal = Decimal("0.50")  # 50% at +5%
    split_sell_pct_2: Decimal = Decimal("0.50")  # 50% at +10%

    def validate(self) -> None:
        """Validate infinite buying-specific parameters."""
        super().validate()

        # Only support single asset
        if len(self.assets) != 1:
            raise ValueError(
                f"Infinite Buying Method only supports single asset, got {len(self.assets)}"
            )

        # Divisions must be positive
        if self.divisions < 1:
            raise ValueError(f"divisions must be positive, got {self.divisions}")

        # Divisions should be reasonable
        if self.divisions > 100:
            warnings.warn(
                f"divisions={self.divisions} is very high, may require large capital"
            )

        # Take profit percentage must be positive
        if self.take_profit_pct <= 0:
            raise ValueError(
                f"take_profit_pct must be positive, got {self.take_profit_pct}"
            )

        # Phase threshold must be between 0 and 1
        if not (0 < self.phase_threshold < 1):
            raise ValueError(
                f"phase_threshold must be between 0 and 1, got {self.phase_threshold}"
            )

        # RSI threshold must be valid
        if self.use_rsi and not (0 < self.rsi_threshold < 100):
            raise ValueError(
                f"rsi_threshold must be between 0 and 100, got {self.rsi_threshold}"
            )

        # Split sell percentages must sum to 1.0
        if abs(
            self.split_sell_pct_1 + self.split_sell_pct_2 - Decimal("1.0")
        ) > Decimal("0.01"):
            raise ValueError(
                f"split_sell percentages must sum to 1.0, got {self.split_sell_pct_1 + self.split_sell_pct_2}"
            )


@dataclass
class ValueRebalancingParameters(StrategyParameters):
    """Configuration for Value Rebalancing (밸류 리밸런싱).

    Attributes:
        initial_capital: Initial total capital (V0 + P0)
        gradient: Gradient value for value path (G)
        upper_band_pct: Upper band percentage above target value
        lower_band_pct: Lower band percentage below target value
        rebalance_frequency: Frequency to check and rebalance (in days)
        value_growth_rate: Expected annual growth rate for value path
    """

    initial_capital: Decimal = Decimal("10000")
    gradient: Decimal = Decimal("10")
    upper_band_pct: Decimal = Decimal("0.05")  # 5%
    lower_band_pct: Decimal = Decimal("0.05")  # 5%
    rebalance_frequency: int = 30  # Monthly
    value_growth_rate: Decimal = Decimal("0.10")  # 10% annual

    def validate(self) -> None:
        """Validate value rebalancing-specific parameters."""
        super().validate()

        # Only support single asset
        if len(self.assets) != 1:
            raise ValueError(
                f"Value Rebalancing only supports single asset, got {len(self.assets)}"
            )

        # Initial capital must be positive
        if self.initial_capital <= 0:
            raise ValueError(
                f"initial_capital must be positive, got {self.initial_capital}"
            )

        # Gradient must be positive
        if self.gradient <= 0:
            raise ValueError(f"gradient must be positive, got {self.gradient}")

        # Band percentages must be positive
        if self.upper_band_pct <= 0:
            raise ValueError(
                f"upper_band_pct must be positive, got {self.upper_band_pct}"
            )
        if self.lower_band_pct <= 0:
            raise ValueError(
                f"lower_band_pct must be positive, got {self.lower_band_pct}"
            )

        # Rebalance frequency must be positive
        if self.rebalance_frequency < 1:
            raise ValueError(
                f"rebalance_frequency must be positive, got {self.rebalance_frequency}"
            )

        # Growth rate must be reasonable
        if not (-Decimal("0.5") < self.value_growth_rate < Decimal("1.0")):
            raise ValueError(
                f"value_growth_rate must be between -0.5 and 1.0, got {self.value_growth_rate}"
            )
