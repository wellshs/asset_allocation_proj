"""Dual Moving Average (trend-following) allocation strategy."""

from datetime import date
from decimal import Decimal

import pandas as pd

from ..backtesting.price_window import get_price_window_with_fallback
from ..models.calculated_weights import CalculatedWeights
from ..models.strategy_params import DualMomentumParameters
from .base import DynamicAllocationStrategy
from .utils import normalize_weights


class DualMomentumStrategy(DynamicAllocationStrategy):
    """Dual moving average allocation strategy.

    Generates buy/sell signals based on crossover of short and long moving averages.
    Allocates to assets when short MA > long MA (bullish signal).
    Allocates to cash when all signals are bearish.

    Formula:
    - Short MA = mean(prices over short_window)
    - Long MA = mean(prices over long_window)
    - Signal = Short MA - Long MA (positive = bullish)
    """

    def __init__(self, parameters: DualMomentumParameters):
        """Initialize dual moving average strategy.

        Args:
            parameters: Dual momentum-specific parameters
        """
        super().__init__(parameters)
        self.parameters: DualMomentumParameters = parameters  # Type hint for IDE

    def calculate_weights(
        self, calculation_date: date, price_data: pd.DataFrame
    ) -> CalculatedWeights:
        """Calculate portfolio weights based on MA crossover signals.

        Args:
            calculation_date: Date for weight calculation
            price_data: Historical price data

        Returns:
            CalculatedWeights with dual MA-based allocations

        Raises:
            InsufficientDataError: If not enough historical data
        """
        # Get price window with automatic fallback for partial data
        price_window, excluded_assets = get_price_window_with_fallback(
            prices_df=price_data,
            calculation_date=calculation_date,
            lookback_days=self.parameters.lookback_days,
            assets=self.parameters.assets,
        )

        complete_assets = [
            asset for asset in self.parameters.assets if asset not in excluded_assets
        ]

        # Calculate MA signals for complete assets
        signals = self._calculate_ma_signals(price_window.prices, complete_assets)

        # Filter bullish signals (short MA > long MA)
        bullish_signals = {
            asset: signal for asset, signal in signals.items() if signal > 0
        }

        # Track assets excluded by bearish signals
        for asset in signals:
            if asset not in bullish_signals:
                if asset not in excluded_assets:
                    excluded_assets.append(asset)

        # Handle all-bearish scenario (allocate to cash)
        if not bullish_signals:
            return CalculatedWeights(
                calculation_date=calculation_date,
                weights={"CASH": Decimal("1.0")},
                strategy_name="dual_momentum",
                parameters_snapshot=self._create_parameters_snapshot(),
                excluded_assets=excluded_assets,
                metadata={"ma_signals": signals, "reason": "all_bearish_signals"},
            )

        # Weight by signal strength if configured
        if self.parameters.use_signal_strength:
            # Weight proportional to signal strength (MA spread)
            weights = normalize_weights(bullish_signals)
        else:
            # Equal weight among bullish assets
            equal_weights = {asset: 1.0 for asset in bullish_signals.keys()}
            weights = normalize_weights(equal_weights)

        # Create CalculatedWeights result
        return CalculatedWeights(
            calculation_date=calculation_date,
            weights=weights,
            strategy_name="dual_momentum",
            parameters_snapshot=self._create_parameters_snapshot(),
            excluded_assets=excluded_assets,
            metadata={"ma_signals": signals},
        )

    def _calculate_ma_signals(
        self, price_window: pd.DataFrame, assets: list[str]
    ) -> dict[str, float]:
        """Calculate MA crossover signals for assets.

        Signal = Short MA - Long MA
        Positive signal = bullish (short MA above long MA)
        Negative signal = bearish (short MA below long MA)

        Args:
            price_window: DataFrame with date index, asset columns
            assets: List of assets to calculate signals for

        Returns:
            Dictionary mapping asset to signal strength
        """
        signals = {}

        for asset in assets:
            asset_prices = price_window[asset].dropna()

            if len(asset_prices) < self.parameters.long_window:
                # Skip if insufficient data
                continue

            # Calculate short and long moving averages
            # Use most recent data for each window
            short_ma = asset_prices.iloc[-self.parameters.short_window :].mean()
            long_ma = asset_prices.iloc[-self.parameters.long_window :].mean()

            # Signal = difference between short and long MA
            # Normalize by long MA to get relative signal strength
            signal = (short_ma - long_ma) / long_ma

            signals[asset] = float(signal)

        return signals
