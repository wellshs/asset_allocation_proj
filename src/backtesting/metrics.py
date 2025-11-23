"""Performance metric calculations."""

import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP


def calculate_total_return(initial_value: Decimal, final_value: Decimal) -> Decimal:
    """Calculate total return over backtest period.

    Formula: (final - initial) / initial

    Args:
        initial_value: Starting portfolio value
        final_value: Ending portfolio value

    Returns:
        Total return as decimal (e.g., 0.5 = 50%)
    """
    if initial_value == 0:
        raise ValueError("Initial value cannot be zero")

    return (final_value - initial_value) / initial_value


def calculate_annualized_return(
    total_return: Decimal, num_trading_days: int
) -> Decimal:
    """Calculate annualized return from total return.

    Formula: (1 + total_return)^(252/num_days) - 1
    Assumes 252 trading days per year.

    Args:
        total_return: Total return over period
        num_trading_days: Number of trading days in period

    Returns:
        Annualized return as decimal
    """
    if num_trading_days <= 0:
        raise ValueError("Number of trading days must be positive")

    # Convert to float for power calculation, then back to Decimal
    annualized = float(1 + total_return) ** (252 / num_trading_days) - 1
    result = Decimal(str(annualized))

    # Round to 4 decimal places
    return result.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_volatility(daily_returns: pd.Series) -> Decimal:
    """Calculate annualized volatility from daily returns.

    Formula: std(daily_returns) × sqrt(252)

    Args:
        daily_returns: Series of daily returns

    Returns:
        Annualized volatility as decimal
    """
    if len(daily_returns) < 2:
        return Decimal("0")

    # Calculate standard deviation
    daily_std = daily_returns.std()

    # Annualize using square-root-of-time rule
    annualized_vol = daily_std * np.sqrt(252)

    result = Decimal(str(annualized_vol))

    # Round to 4 decimal places
    return result.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_max_drawdown(portfolio_values: pd.Series) -> Decimal:
    """Calculate maximum peak-to-trough decline.

    Formula: min((value - peak) / peak)

    Args:
        portfolio_values: Series of portfolio values over time

    Returns:
        Maximum drawdown as decimal (negative value or zero)
    """
    if len(portfolio_values) < 2:
        return Decimal("0")

    # Calculate running maximum
    running_max = portfolio_values.expanding().max()

    # Calculate drawdown at each point
    drawdown = (portfolio_values - running_max) / running_max

    # Get maximum drawdown (most negative value)
    max_dd = drawdown.min()

    result = Decimal(str(max_dd))

    # Round to 4 decimal places
    return result.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_sharpe_ratio(
    annualized_return: Decimal, volatility: Decimal, risk_free_rate: Decimal
) -> Decimal:
    """Calculate Sharpe ratio (risk-adjusted return).

    Formula: (annualized_return - risk_free_rate) / volatility

    Reference: Sharpe, William F. (1994). "The Sharpe Ratio".

    Args:
        annualized_return: Annualized return
        volatility: Annualized volatility
        risk_free_rate: Risk-free rate (annual)

    Returns:
        Sharpe ratio rounded to 2 decimal places

    Raises:
        ZeroDivisionError: If volatility is zero
    """
    if volatility == 0:
        raise ZeroDivisionError("Cannot calculate Sharpe ratio with zero volatility")

    excess_return = annualized_return - risk_free_rate
    sharpe = excess_return / volatility

    # Round to 2 decimal places
    return sharpe.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
