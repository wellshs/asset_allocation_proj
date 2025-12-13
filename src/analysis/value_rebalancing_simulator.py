"""Value Rebalancing simulation utility.

This module provides a reusable simulator for Value Rebalancing strategy
based on Michael Edleson's Value Averaging methodology.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import pandas as pd


# Constants - Extract magic numbers with explanatory comments
REBALANCE_THRESHOLD = Decimal("0.10")  # 10% allocation deviation triggers rebalance
STOCK_ALLOCATION_MULTIPLIER = Decimal("1.1")  # Stock 10% above target triggers sell
STOCK_ALLOCATION_FLOOR = Decimal("0.9")  # Stock 10% below target triggers buy
CASH_RESERVE_PCT = Decimal("0.95")  # Keep 5% cash reserve
TRANSACTION_COST_PCT = Decimal("0.001")  # 0.1% commission
TARGET_STOCK_ALLOCATION = Decimal("0.8")  # Target 80% in stocks
DAYS_PER_YEAR = Decimal("365.0")


@dataclass
class ValueRebalancingParameters:
    """Parameters for Value Rebalancing strategy.

    Attributes:
        value_growth_rate: Annual target growth rate (e.g., 0.07 for 7%)
        rebalance_frequency_days: Check rebalancing every N days (e.g., 30 for monthly)
        initial_capital: Starting capital amount
    """

    value_growth_rate: Decimal
    rebalance_frequency_days: int
    initial_capital: Decimal = Decimal("10000")


@dataclass
class SimulationResult:
    """Result of a Value Rebalancing simulation.

    Attributes:
        portfolio_values: DataFrame with daily portfolio values and metrics
        final_value: Final total portfolio value
        final_shares: Final number of shares held
        final_cash: Final cash amount
        rebalance_count: Number of rebalancing trades executed
        actions: List of rebalancing actions ('buy' or 'sell')
    """

    portfolio_values: pd.DataFrame
    final_value: Decimal
    final_shares: Decimal
    final_cash: Decimal
    rebalance_count: int
    actions: list[str]


class ValueRebalancingSimulator:
    """Simulator for Value Rebalancing strategy.

    This class implements the Value Rebalancing (Value Averaging) strategy
    with proper Decimal arithmetic for financial precision.
    """

    def __init__(self, params: ValueRebalancingParameters):
        """Initialize the simulator.

        Args:
            params: Strategy parameters
        """
        self.params = params

    def simulate(
        self,
        price_data: pd.DataFrame,
        price_column: str = "Close",
    ) -> SimulationResult:
        """Run Value Rebalancing simulation.

        Args:
            price_data: DataFrame with price data, must have DatetimeIndex
            price_column: Name of column containing prices

        Returns:
            SimulationResult with portfolio history and final values

        Raises:
            ValueError: If price_data is empty or invalid
            KeyError: If price_column not found in price_data
        """
        # Validate input
        if price_data.empty:
            raise ValueError("Price data cannot be empty")
        if price_column not in price_data.columns:
            raise KeyError(f"Price column '{price_column}' not found in data")

        # Initialize portfolio
        cash_pool = self.params.initial_capital
        stock_value = Decimal("0")
        shares = Decimal("0")

        start_date = price_data.index[0]
        last_rebalance: Optional[pd.Timestamp] = None

        # Track history
        portfolio_values = []
        rebalance_dates = []
        actions = []

        for current_date in price_data.index:
            try:
                # Get current price and convert to Decimal
                current_price = Decimal(str(price_data.loc[current_date, price_column]))

                if current_price <= 0:
                    # Skip invalid prices
                    continue

                # Update stock value
                stock_value = shares * current_price
                current_total = stock_value + cash_pool

                # Calculate target value (using total portfolio as reference)
                days_since_start = (current_date - start_date).days
                years = Decimal(str(days_since_start)) / DAYS_PER_YEAR

                # Target: start at 80% stocks, grow at target rate
                base_target = self.params.initial_capital * (
                    (Decimal("1") + self.params.value_growth_rate) ** years
                )
                target_stock_value = base_target * TARGET_STOCK_ALLOCATION

                # Check if rebalancing needed
                needs_rebalance = False
                if last_rebalance is None:
                    # Initial investment
                    needs_rebalance = True
                else:
                    days_since_rebalance = (current_date - last_rebalance).days
                    if days_since_rebalance >= self.params.rebalance_frequency_days:
                        # Check if stock allocation is too far from target
                        if current_total > 0:
                            target_allocation = target_stock_value / current_total
                            current_allocation = stock_value / current_total

                            if (
                                abs(current_allocation - target_allocation)
                                > REBALANCE_THRESHOLD
                            ):
                                needs_rebalance = True

                # Rebalance if needed
                action = "hold"
                if needs_rebalance:
                    # Calculate target shares based on target stock value
                    target_shares = target_stock_value / current_price

                    if stock_value > target_stock_value * STOCK_ALLOCATION_MULTIPLIER:
                        # Stock allocation too high, sell some
                        shares_to_sell = shares - target_shares

                        if shares_to_sell > 0:
                            # Apply transaction cost
                            cash_from_sale = (
                                shares_to_sell
                                * current_price
                                * (Decimal("1") - TRANSACTION_COST_PCT)
                            )
                            cash_pool += cash_from_sale
                            shares = target_shares
                            action = "sell"

                    elif stock_value < target_stock_value * STOCK_ALLOCATION_FLOOR:
                        # Stock allocation too low, buy more
                        cash_needed = target_stock_value - stock_value
                        cash_to_use = min(cash_needed, cash_pool * CASH_RESERVE_PCT)

                        if cash_to_use > 0:
                            # Apply transaction cost
                            shares_to_buy = (
                                cash_to_use
                                * (Decimal("1") - TRANSACTION_COST_PCT)
                                / current_price
                            )
                            shares += shares_to_buy
                            cash_pool -= cash_to_use
                            action = "buy"

                    if action != "hold":
                        last_rebalance = current_date
                        rebalance_dates.append(current_date)
                        actions.append(action)

                # Update stock value after rebalance
                stock_value = shares * current_price
                total_value = stock_value + cash_pool

                portfolio_values.append(
                    {
                        "date": current_date,
                        "total_value": float(total_value),
                        "stock_value": float(stock_value),
                        "cash_pool": float(cash_pool),
                        "shares": float(shares),
                        "price": float(current_price),
                        "target_stock_value": float(target_stock_value),
                        "base_target": float(base_target),
                        "action": action,
                    }
                )

            except (ValueError, TypeError, KeyError) as e:
                # Skip problematic dates but log warning
                print(f"Warning: Skipping date {current_date} due to error: {e}")
                continue

        if not portfolio_values:
            raise ValueError("Simulation produced no valid portfolio values")

        return SimulationResult(
            portfolio_values=pd.DataFrame(portfolio_values),
            final_value=total_value,
            final_shares=shares,
            final_cash=cash_pool,
            rebalance_count=len(rebalance_dates),
            actions=actions,
        )
