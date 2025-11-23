"""Custom exceptions for backtesting engine."""


class BacktestError(Exception):
    """Base exception for backtest-related errors."""

    pass


class DataError(BacktestError):
    """Exception for data validation and loading errors."""

    pass


class CurrencyError(BacktestError):
    """Exception for currency conversion errors."""

    pass


class APIError(BacktestError):
    """Exception for external API errors."""

    pass
