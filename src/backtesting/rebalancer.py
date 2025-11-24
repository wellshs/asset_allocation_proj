"""Rebalancing logic for portfolio management."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

from ..models import RebalancingFrequency
from ..models.portfolio_state import PortfolioState


def generate_rebalancing_dates(
    start_date: date, end_date: date, frequency: RebalancingFrequency
) -> list[date]:
    """Generate list of rebalancing dates based on frequency.

    Args:
        start_date: Start date of backtest
        end_date: End date of backtest
        frequency: Rebalancing frequency

    Returns:
        List of dates when rebalancing should occur
    """
    if frequency == RebalancingFrequency.NEVER:
        return []

    dates = []

    if frequency == RebalancingFrequency.DAILY:
        # Every business day
        date_range = pd.bdate_range(start=start_date, end=end_date)
        dates = [d.date() for d in date_range]

    elif frequency == RebalancingFrequency.WEEKLY:
        # Every Monday
        date_range = pd.bdate_range(start=start_date, end=end_date, freq="W-MON")
        dates = [d.date() for d in date_range]
        # Include start date if not already included
        if start_date not in dates:
            dates.insert(0, start_date)

    elif frequency == RebalancingFrequency.MONTHLY:
        # First business day of each month
        date_range = pd.bdate_range(start=start_date, end=end_date, freq="BMS")
        dates = [d.date() for d in date_range]
        # Include start date if not already included
        if start_date not in dates:
            dates.insert(0, start_date)

    elif frequency == RebalancingFrequency.QUARTERLY:
        # First business day of each quarter
        date_range = pd.bdate_range(start=start_date, end=end_date, freq="BQS")
        dates = [d.date() for d in date_range]
        # Include start date if not already included
        if start_date not in dates:
            dates.insert(0, start_date)

    elif frequency == RebalancingFrequency.ANNUALLY:
        # First business day of each year
        date_range = pd.bdate_range(start=start_date, end=end_date, freq="BAS-JAN")
        dates = [d.date() for d in date_range]
        # Include start date if not already included
        if start_date not in dates:
            dates.insert(0, start_date)

    return dates


def calculate_rebalancing_trades(
    current_state: PortfolioState,
    target_weights: dict[str, Decimal],
) -> dict[str, Decimal]:
    """Calculate trades needed to rebalance portfolio to target weights.

    Args:
        current_state: Current portfolio state
        target_weights: Target allocation weights

    Returns:
        Dictionary mapping symbol to quantity change (+ for buy, - for sell)
    """
    total_value = current_state.total_value

    if total_value == 0:
        return {symbol: Decimal("0") for symbol in target_weights.keys()}

    trades = {}

    for symbol, target_weight in target_weights.items():
        # Calculate target value for this asset
        target_value = total_value * target_weight

        # Calculate current value
        current_quantity = current_state.asset_holdings.get(symbol, Decimal("0"))
        current_price = current_state.current_prices[symbol]
        current_value = current_quantity * current_price

        # Calculate value difference
        value_diff = target_value - current_value

        # Convert to quantity
        quantity_change = value_diff / current_price

        # Round to 6 decimal places
        quantity_change = quantity_change.quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_UP
        )

        trades[symbol] = quantity_change

    return trades
