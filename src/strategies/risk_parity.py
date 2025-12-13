"""Risk Parity (volatility-adjusted) allocation strategy."""

from datetime import date
from decimal import Decimal
import math

import pandas as pd

from ..backtesting.price_window import get_price_window_with_fallback
from ..models.calculated_weights import CalculatedWeights
from ..models.strategy_params import RiskParityParameters
from .base import DynamicAllocationStrategy
from .utils import normalize_weights


class RiskParityStrategy(DynamicAllocationStrategy):
    """Risk parity allocation strategy.

    Allocates weights inversely proportional to asset volatility.
    Lower volatility assets receive higher weights to equalize risk contribution.

    Formula: Weight ∝ 1 / Volatility
    Volatility: Annualized standard deviation of returns
    """

    def __init__(self, parameters: RiskParityParameters):
        """Initialize risk parity strategy.

        Args:
            parameters: Risk parity-specific parameters
        """
        super().__init__(parameters)
        self.parameters: RiskParityParameters = parameters  # Type hint for IDE

    def calculate_weights(
        self, calculation_date: date, price_data: pd.DataFrame
    ) -> CalculatedWeights:
        """Calculate portfolio weights based on inverse volatility.

        Args:
            calculation_date: Date for weight calculation
            price_data: Historical price data

        Returns:
            CalculatedWeights with risk parity allocations

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

        # Calculate volatilities for complete assets
        volatilities = self._calculate_volatilities(
            price_window.prices, complete_assets
        )

        # Filter out zero volatility assets
        non_zero_volatilities = {
            asset: vol
            for asset, vol in volatilities.items()
            if vol >= float(self.parameters.min_volatility_threshold)
        }

        # Track assets excluded by zero volatility
        for asset in volatilities:
            if asset not in non_zero_volatilities:
                if asset not in excluded_assets:
                    excluded_assets.append(asset)

        # Handle all-zero-volatility scenario
        if not non_zero_volatilities:
            return CalculatedWeights(
                calculation_date=calculation_date,
                weights={"CASH": Decimal("1.0")},
                strategy_name="risk_parity",
                parameters_snapshot=self._create_parameters_snapshot(),
                excluded_assets=excluded_assets,
                metadata={
                    "volatilities": volatilities,
                    "reason": "all_zero_volatility",
                },
            )

        # Calculate inverse volatility weights
        inverse_vol_weights = {
            asset: 1.0 / vol for asset, vol in non_zero_volatilities.items()
        }

        # Normalize to weights
        weights = normalize_weights(inverse_vol_weights)

        # Create CalculatedWeights result
        return CalculatedWeights(
            calculation_date=calculation_date,
            weights=weights,
            strategy_name="risk_parity",
            parameters_snapshot=self._create_parameters_snapshot(),
            excluded_assets=excluded_assets,
            metadata={"volatilities": volatilities},
        )

    def _calculate_volatilities(
        self, price_window: pd.DataFrame, assets: list[str]
    ) -> dict[str, float]:
        """Calculate annualized volatility for assets.

        Volatility = daily_std * sqrt(annualization_factor)

        Args:
            price_window: DataFrame with date index, asset columns
            assets: List of assets to calculate volatility for

        Returns:
            Dictionary mapping asset to annualized volatility
        """
        volatilities = {}

        for asset in assets:
            asset_prices = price_window[asset].dropna()

            if len(asset_prices) < 2:
                # Skip if insufficient data
                continue

            # Calculate daily returns
            returns = asset_prices.pct_change().dropna()

            if len(returns) < 2:
                continue

            # Calculate daily standard deviation (sample std with ddof=1)
            daily_std = returns.std(ddof=1)

            # Annualize: multiply by sqrt(trading days per year)
            annualized_vol = daily_std * math.sqrt(self.parameters.annualization_factor)

            volatilities[asset] = float(annualized_vol)

        return volatilities
