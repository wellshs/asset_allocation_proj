"""Portfolio state models."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class PortfolioState:
    """Snapshot of portfolio holdings and value at a specific point in time.

    Attributes:
        timestamp: Date of this portfolio state
        cash_balance: Cash holdings in base currency
        asset_holdings: Quantity of each asset held (symbol -> quantity)
        current_prices: Current price of each asset in base currency (symbol -> price)
    """

    timestamp: date
    cash_balance: Decimal
    asset_holdings: dict[str, Decimal]
    current_prices: dict[str, Decimal]

    @property
    def total_value(self) -> Decimal:
        """Compute total portfolio value in base currency.

        Returns:
            Total value = cash + sum(holdings × prices)
        """
        holdings_value = sum(
            qty * self.current_prices.get(symbol, Decimal(0))
            for symbol, qty in self.asset_holdings.items()
        )
        return self.cash_balance + holdings_value

    def get_current_weights(self) -> dict[str, Decimal]:
        """Calculate current portfolio weights.

        Returns:
            Dictionary mapping asset symbols to current weights
        """
        total = self.total_value
        if total == 0:
            return {}
        return {
            symbol: (qty * self.current_prices[symbol]) / total
            for symbol, qty in self.asset_holdings.items()
        }
