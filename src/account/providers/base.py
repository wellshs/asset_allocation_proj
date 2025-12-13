"""Base provider interface for brokerage integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from src.account.models import BrokerageAccount, AccountHoldings
from src.account.config import AccountCredentials


@dataclass
class BrokerageProvider:
    """
    Metadata for a brokerage provider.

    Attributes:
        name: Provider identifier (e.g., "korea_investment")
        display_name: Human-readable provider name
        api_base_url: Base URL for API endpoints
        rate_limit_delay: Seconds to wait between API requests
    """

    name: str
    display_name: str
    api_base_url: str
    rate_limit_delay: float = 1.1


class AccountProvider(ABC):
    """
    Abstract base class for brokerage account providers.

    All brokerage-specific implementations must inherit from this class
    and implement the required methods.
    """

    @abstractmethod
    def authenticate(self, account: BrokerageAccount) -> BrokerageAccount:
        """
        Authenticate with the brokerage and obtain access token.

        Args:
            account: Account to authenticate

        Returns:
            BrokerageAccount: Updated account with access token and expiry

        Raises:
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    def fetch_holdings(
        self, account: BrokerageAccount, credentials: AccountCredentials = None
    ) -> AccountHoldings:
        """
        Fetch current holdings for the authenticated account.

        Args:
            account: Authenticated account
            credentials: API credentials (optional, provider-dependent)

        Returns:
            AccountHoldings: Current holdings and cash balance

        Raises:
            AuthenticationError: If account is not authenticated
            APIError: If API request fails
        """
        pass
