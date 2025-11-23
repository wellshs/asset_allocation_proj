"""Backtest configuration models."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from . import RebalancingFrequency


@dataclass
class TransactionCosts:
    """Transaction costs configuration.

    Attributes:
        fixed_per_trade: Fixed cost per trade (e.g., $0)
        percentage: Percentage of trade value (e.g., 0.001 = 0.1%)
    """

    fixed_per_trade: Decimal
    percentage: Decimal

    def __post_init__(self):
        if self.fixed_per_trade < 0:
            raise ValueError("fixed_per_trade cannot be negative")
        if self.percentage < 0:
            raise ValueError("percentage cannot be negative")


@dataclass
class BacktestConfiguration:
    """Parameters for configuring and executing a backtest simulation.

    Attributes:
        start_date: Start date of backtest period
        end_date: End date of backtest period
        initial_capital: Starting capital in base currency
        rebalancing_frequency: How often to rebalance portfolio
        base_currency: ISO 4217 currency code for reporting
        transaction_costs: Transaction cost parameters
        risk_free_rate: Risk-free rate for Sharpe ratio calculation (default: 0.02 = 2%)
    """

    start_date: date
    end_date: date
    initial_capital: Decimal
    rebalancing_frequency: RebalancingFrequency
    base_currency: str
    transaction_costs: TransactionCosts = None
    risk_free_rate: Decimal = Decimal("0.02")

    def __post_init__(self):
        # Set default transaction costs if not provided
        if self.transaction_costs is None:
            self.transaction_costs = TransactionCosts(Decimal("0"), Decimal("0"))

        # Validate date range
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")

        # Validate initial capital
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")

        # Validate risk-free rate
        if self.risk_free_rate < 0:
            raise ValueError("risk_free_rate cannot be negative")

        # Validate currency code
        if len(self.base_currency) != 3:
            raise ValueError("base_currency must be ISO 4217 code (3 letters)")
