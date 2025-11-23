"""Data models for backtesting engine."""

from enum import Enum


class RebalancingFrequency(Enum):
    """Frequency at which portfolio is rebalanced."""
    NEVER = "never"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


__all__ = [
    "RebalancingFrequency",
]
