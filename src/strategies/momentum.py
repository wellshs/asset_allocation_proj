"""Momentum-based dynamic allocation strategy."""

from datetime import date
from decimal import Decimal

import pandas as pd

from ..backtesting.price_window import get_price_window, InsufficientDataError
from ..models.calculated_weights import CalculatedWeights
from ..models.strategy_params import MomentumParameters
from .base import DynamicAllocationStrategy
from .utils import normalize_weights, filter_complete_assets


class MomentumStrategy(DynamicAllocationStrategy):
    """Momentum-based allocation strategy.

    Allocates weights proportional to historical returns over lookback period.
    Assets with negative momentum can be excluded (defensive mode).
    When all assets have negative momentum, allocates 100% to cash.

    Formula: Momentum = (End Price / Start Price) - 1
    Weights: Proportional to positive momentum scores
    """

    def __init__(self, parameters: MomentumParameters):
        """Initialize momentum strategy.

        Args:
            parameters: Momentum-specific parameters
        """
        super().__init__(parameters)
        self.parameters: MomentumParameters = parameters  # Type hint for IDE

    def calculate_weights(
        self, calculation_date: date, price_data: pd.DataFrame
    ) -> CalculatedWeights:
        """Calculate portfolio weights based on momentum.

        Args:
            calculation_date: Date for weight calculation
            price_data: Historical price data

        Returns:
            CalculatedWeights with momentum-based allocations

        Raises:
            InsufficientDataError: If not enough historical data
        """
        # Get price window for lookback period
        # Try all assets first, if that fails, try each asset individually
        try:
            price_window = get_price_window(
                prices_df=price_data,
                calculation_date=calculation_date,
                lookback_days=self.parameters.lookback_days,
                assets=self.parameters.assets,
            )
            complete_assets = filter_complete_assets(
                price_window.prices, required_days=self.parameters.lookback_days
            )
        except InsufficientDataError:
            # Some assets have insufficient data - try each individually
            complete_assets = []
            for asset in self.parameters.assets:
                try:
                    asset_window = get_price_window(
                        prices_df=price_data,
                        calculation_date=calculation_date,
                        lookback_days=self.parameters.lookback_days,
                        assets=[asset],
                    )
                    # Check if asset has complete data
                    asset_complete = filter_complete_assets(
                        asset_window.prices, required_days=self.parameters.lookback_days
                    )
                    if asset in asset_complete:
                        complete_assets.append(asset)
                except InsufficientDataError:
                    # This asset doesn't have enough data
                    pass

            # If still no complete assets, raise error
            if not complete_assets:
                raise InsufficientDataError(
                    f"No assets have sufficient data for {self.parameters.lookback_days}-day lookback"
                )

            # Get price window for complete assets only
            price_window = get_price_window(
                prices_df=price_data,
                calculation_date=calculation_date,
                lookback_days=self.parameters.lookback_days,
                assets=complete_assets,
            )

        # Track excluded assets
        excluded_assets = [
            asset for asset in self.parameters.assets if asset not in complete_assets
        ]

        # Calculate momentum scores for complete assets
        momentum_scores = self._calculate_momentum_scores(
            price_window.prices, complete_assets
        )

        # Filter by minimum momentum threshold if specified
        if self.parameters.min_momentum is not None:
            filtered_scores = {
                asset: score
                for asset, score in momentum_scores.items()
                if score >= float(self.parameters.min_momentum)
            }
            # Track assets excluded by min_momentum
            for asset in momentum_scores:
                if asset not in filtered_scores:
                    excluded_assets.append(asset)
            momentum_scores = filtered_scores

        # Exclude negative momentum assets if configured
        if self.parameters.exclude_negative:
            positive_scores = {
                asset: score for asset, score in momentum_scores.items() if score > 0
            }
            # Track assets excluded by negative momentum
            for asset in momentum_scores:
                if asset not in positive_scores:
                    if asset not in excluded_assets:
                        excluded_assets.append(asset)
            momentum_scores = positive_scores

        # Handle all-negative scenario (allocate to cash)
        if not momentum_scores:
            return CalculatedWeights(
                calculation_date=calculation_date,
                weights={"CASH": Decimal("1.0")},
                strategy_name="momentum",
                parameters_snapshot=self._create_parameters_snapshot(),
                excluded_assets=excluded_assets,
                metadata={"momentum_scores": {}, "reason": "all_negative_momentum"},
            )

        # Normalize momentum scores to weights
        weights = normalize_weights(momentum_scores)

        # Create CalculatedWeights result
        return CalculatedWeights(
            calculation_date=calculation_date,
            weights=weights,
            strategy_name="momentum",
            parameters_snapshot=self._create_parameters_snapshot(),
            excluded_assets=excluded_assets,
            metadata={"momentum_scores": momentum_scores},
        )

    def _calculate_momentum_scores(
        self, price_window: pd.DataFrame, assets: list[str]
    ) -> dict[str, float]:
        """Calculate momentum scores for assets.

        Momentum = (End Price / Start Price) - 1

        Args:
            price_window: DataFrame with date index, asset columns
            assets: List of assets to calculate momentum for

        Returns:
            Dictionary mapping asset to momentum score
        """
        momentum_scores = {}

        for asset in assets:
            asset_prices = price_window[asset].dropna()

            if len(asset_prices) < 2:
                # Skip if insufficient data
                continue

            start_price = asset_prices.iloc[0]
            end_price = asset_prices.iloc[-1]

            # Calculate momentum: (end/start) - 1
            if start_price > 0:  # Avoid division by zero
                momentum = (end_price / start_price) - 1.0
                momentum_scores[asset] = float(momentum)

        return momentum_scores
