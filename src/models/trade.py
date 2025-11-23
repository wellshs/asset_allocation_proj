"""Trade models."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Trade:
    """Record of a buy or sell transaction executed during backtesting.

    Attributes:
        timestamp: Date trade was executed
        asset_symbol: Symbol of asset traded
        quantity: Quantity traded (+ for buy, - for sell)
        price: Execution price per unit in asset currency
        currency: Currency of the price (ISO 4217)
        transaction_cost: Total cost incurred for this trade
    """

    timestamp: date
    asset_symbol: str
    quantity: Decimal
    price: Decimal
    currency: str
    transaction_cost: Decimal

    def __post_init__(self):
        # Validate quantity
        if self.quantity == 0:
            raise ValueError("quantity cannot be zero")

        # Validate price
        if self.price <= 0:
            raise ValueError("price must be positive")

        # Validate transaction cost
        if self.transaction_cost < 0:
            raise ValueError("transaction_cost cannot be negative")

        # Validate currency code
        if len(self.currency) != 3:
            raise ValueError("currency must be ISO 4217 code")

    @property
    def trade_value(self) -> Decimal:
        """Absolute value of trade in asset currency."""
        return abs(self.quantity * self.price)

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy trade."""
        return self.quantity > 0

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell trade."""
        return self.quantity < 0
