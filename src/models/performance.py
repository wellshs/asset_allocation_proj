"""Performance metrics models."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class PerformanceMetrics:
    """Calculated performance statistics for a completed backtest.

    Attributes:
        total_return: Total return over backtest period
        annualized_return: Return annualized to yearly basis
        volatility: Annualized standard deviation
        max_drawdown: Maximum peak-to-trough decline
        sharpe_ratio: Risk-adjusted return metric
        num_trades: Total number of trades executed
        start_date: Backtest start date
        end_date: Backtest end date
        start_value: Initial portfolio value
        end_value: Final portfolio value
    """
    total_return: Decimal
    annualized_return: Decimal
    volatility: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    num_trades: int
    start_date: date
    end_date: date
    start_value: Decimal
    end_value: Decimal

    def to_dict(self) -> dict:
        """Format metrics for display.

        Returns:
            Dictionary with formatted metric strings
        """
        return {
            "Total Return": f"{float(self.total_return):.2%}",
            "Annualized Return": f"{float(self.annualized_return):.2%}",
            "Volatility": f"{float(self.volatility):.2%}",
            "Maximum Drawdown": f"{float(self.max_drawdown):.2%}",
            "Sharpe Ratio": f"{float(self.sharpe_ratio):.2f}",
            "Number of Trades": self.num_trades,
            "Period": f"{self.start_date} to {self.end_date}",
            "Start Value": f"${float(self.start_value):,.2f}",
            "End Value": f"${float(self.end_value):,.2f}",
        }
