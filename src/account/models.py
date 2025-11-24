"""Data models for brokerage account integration."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict


class AccountStatus(Enum):
    """Status of brokerage account connection."""

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    ERROR = "error"


class AssetType(Enum):
    """Type of asset/security."""

    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    OPTION = "option"
    FUTURE = "future"
    FOREIGN = "foreign"
    OTHER = "other"


@dataclass
class BrokerageAccount:
    """
    Represents a connection to a specific brokerage account.

    Attributes:
        account_id: Unique identifier for this account configuration
        provider: Provider identifier (e.g., "korea_investment")
        account_number: Brokerage account number
        status: Current connection status
        access_token: API access token (if authenticated)
        token_expiry: Expiry time of access token
        last_fetch: Timestamp of last successful data fetch
    """

    account_id: str
    provider: str
    account_number: str
    status: AccountStatus
    access_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    last_fetch: Optional[datetime] = None

    def is_authenticated(self) -> bool:
        """
        Check if account has valid authentication.

        Returns:
            bool: True if connected with valid token, False otherwise
        """
        if self.status != AccountStatus.CONNECTED:
            return False
        if self.access_token is None or self.token_expiry is None:
            return False
        return datetime.now() < self.token_expiry


@dataclass
class SecurityPosition:
    """
    Represents a holding of a specific security.

    Attributes:
        symbol: Security identifier/symbol
        name: Security name
        quantity: Number of shares/units held
        average_price: Average purchase price
        current_price: Current market price
        current_value: Total current value (quantity * current_price)
        asset_type: Type of asset
        profit_loss: Unrealized profit/loss
        has_warning: Flag indicating incomplete/uncertain data
    """

    symbol: str
    name: str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal
    current_value: Decimal
    asset_type: AssetType = AssetType.STOCK
    profit_loss: Optional[Decimal] = None
    has_warning: bool = False


@dataclass
class AccountHoldings:
    """
    Represents the current state of assets in a brokerage account.

    Attributes:
        account_id: Account identifier
        timestamp: Time when data was retrieved
        cash_balance: Available cash balance
        positions: List of security positions
        total_value: Total account value (cash + positions)
    """

    account_id: str
    timestamp: datetime
    cash_balance: Decimal
    positions: list[SecurityPosition]
    total_value: Decimal

    def to_portfolio_state(self):
        """
        Convert AccountHoldings to PortfolioState format.

        Returns:
            PortfolioState: Portfolio state compatible with backtesting engine
        """
        from src.models.portfolio_state import PortfolioState

        # Convert positions to asset_holdings dict {symbol: quantity}
        asset_holdings: Dict[str, Decimal] = {}
        current_prices: Dict[str, Decimal] = {}

        for position in self.positions:
            asset_holdings[position.symbol] = position.quantity
            current_prices[position.symbol] = position.current_price

        return PortfolioState(
            timestamp=self.timestamp.date(),  # Convert datetime to date
            cash_balance=self.cash_balance,
            asset_holdings=asset_holdings,
            current_prices=current_prices,
        )
