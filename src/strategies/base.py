"""Base class for dynamic allocation strategies."""

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd

from ..models.calculated_weights import CalculatedWeights
from ..models.strategy_params import StrategyParameters


class DynamicAllocationStrategy(ABC):
    """Abstract base class for dynamic allocation strategies.

    Dynamic strategies calculate portfolio weights based on historical price data,
    adapting allocations over time based on market conditions.

    Subclasses must implement calculate_weights() method to define the
    strategy logic.
    """

    def __init__(self, parameters: StrategyParameters):
        """Initialize strategy with parameters.

        Args:
            parameters: Strategy-specific parameters

        Raises:
            ValueError: If parameters are invalid
        """
        self.parameters = parameters
        self.parameters.validate()  # Validate on initialization

    @abstractmethod
    def calculate_weights(
        self, calculation_date: date, price_data: pd.DataFrame
    ) -> CalculatedWeights:
        """Calculate portfolio weights for given date.

        Args:
            calculation_date: Date for weight calculation
            price_data: Historical price data (columns: date, symbol, price, currency)

        Returns:
            CalculatedWeights with target allocations

        Raises:
            InsufficientDataError: If not enough historical data for calculation
        """
        pass

    def _create_parameters_snapshot(self) -> dict:
        """Create snapshot of strategy parameters for audit trail.

        Returns:
            Dictionary with parameter names and values
        """
        # Convert dataclass to dict
        params_dict = {}
        for field in self.parameters.__dataclass_fields__:
            value = getattr(self.parameters, field)
            # Convert to JSON-serializable types
            if isinstance(value, list):
                params_dict[field] = value.copy()
            else:
                params_dict[field] = value

        return params_dict
