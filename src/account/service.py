"""Account service layer for high-level operations."""

from src.account.models import (
    BrokerageAccount,
    AccountHoldings,
    AccountStatus,
    SecurityPosition,
)
from decimal import Decimal
from src.account.auth import authenticate, get_provider
from src.account.config import load_config
from src.account.logging import logger
from src.account.token_cache import TokenCache


class AccountService:
    """Service for managing brokerage account operations."""

    def __init__(self, config_path: str):
        """
        Initialize service with configuration.

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self._token_cache = TokenCache()  # File-based token cache

    def get_holdings(self, account_name: str) -> AccountHoldings:
        """
        Get holdings for a specific account.

        Args:
            account_name: Name of account in configuration

        Returns:
            AccountHoldings: Current holdings

        Raises:
            ValueError: If account not found
        """
        # Find account in config
        account_config = None
        for acc in self.config.accounts:
            if acc.name == account_name:
                account_config = acc
                break

        if not account_config or not account_config.enabled:
            raise ValueError(f"Account not found or disabled: {account_name}")

        # Try to load cached token from file
        account = self._token_cache.get(account_config.name)

        # Create new account if not cached
        if account is None:
            account = BrokerageAccount(
                account_id=account_config.name,
                provider=account_config.provider,
                account_number=account_config.credentials.account_number,
                status=AccountStatus.DISCONNECTED,
            )

        # Authenticate if needed (token expired or not authenticated)
        if not account.is_authenticated():
            logger.info(f"Authenticating account: {account_name}")
            account = authenticate(account, account_config.credentials)
            # Save to file cache for future CLI invocations
            self._token_cache.set(account)
            logger.info(f"Token cached to disk for account: {account_name}")
        else:
            logger.info(f"Using cached token from disk for account: {account_name}")

        # Fetch holdings
        provider = get_provider(account.provider)
        holdings = provider.fetch_holdings(account, account_config.credentials)

        # Validate holdings
        self._validate_holdings(holdings)

        # Detect warnings
        self._detect_warnings(holdings)

        return holdings

    def _validate_holdings(self, holdings: AccountHoldings) -> None:
        """
        Validate holdings data completeness.

        Args:
            holdings: Holdings to validate

        Raises:
            ValueError: If data is invalid
        """
        if holdings.cash_balance < 0:
            raise ValueError("Invalid cash balance")

        for position in holdings.positions:
            if position.quantity < 0:
                raise ValueError(f"Invalid quantity for {position.symbol}")

    def _detect_warnings(self, holdings: AccountHoldings) -> None:
        """
        Detect and mark incomplete or uncertain data.

        Args:
            holdings: Holdings to check
        """
        for position in holdings.positions:
            # Mark positions with missing price data
            if position.current_price == 0:
                position.has_warning = True

    def get_all_holdings(self) -> dict[str, AccountHoldings]:
        """
        Get holdings for all enabled accounts.

        Returns:
            dict: Account name -> AccountHoldings mapping
        """
        all_holdings = {}

        for account_config in self.config.accounts:
            if not account_config.enabled:
                continue

            try:
                holdings = self.get_holdings(account_config.name)
                all_holdings[account_config.name] = holdings
            except Exception as e:
                # Log error but continue with other accounts
                logger.warning(f"Failed to fetch {account_config.name}: {e}")
                continue

        return all_holdings

    def consolidate_holdings(
        self, all_holdings: dict[str, AccountHoldings]
    ) -> AccountHoldings:
        """
        Consolidate holdings from multiple accounts.

        Args:
            all_holdings: Dict of account holdings

        Returns:
            AccountHoldings: Consolidated holdings
        """
        from datetime import datetime, timezone
        from collections import defaultdict

        total_cash = Decimal("0")
        position_map = defaultdict(
            lambda: {
                "quantity": Decimal("0"),
                "value": Decimal("0"),
                "name": "",
                "symbol": "",
            }
        )

        for holdings in all_holdings.values():
            total_cash += holdings.cash_balance

            for position in holdings.positions:
                pos_data = position_map[position.symbol]
                pos_data["quantity"] += position.quantity
                pos_data["value"] += position.current_value
                pos_data["name"] = position.name
                pos_data["symbol"] = position.symbol

        # Convert to SecurityPosition list
        consolidated_positions = []
        for symbol, data in position_map.items():
            try:
                avg_price = (
                    data["value"] / data["quantity"]
                    if data["quantity"] > 0
                    else Decimal("0")
                )
                # Validate avg_price is finite
                if not avg_price.is_finite():
                    logger.warning(f"Invalid average price for {symbol}: {avg_price}")
                    avg_price = Decimal("0")
            except Exception as e:
                logger.error(f"Error calculating average price for {symbol}: {e}")
                avg_price = Decimal("0")

            position = SecurityPosition(
                symbol=symbol,
                name=data["name"],
                quantity=data["quantity"],
                average_price=avg_price,
                current_price=avg_price,
                current_value=data["value"],
            )
            consolidated_positions.append(position)

        total_value = total_cash + sum(p.current_value for p in consolidated_positions)

        return AccountHoldings(
            account_id="consolidated",
            timestamp=datetime.now(timezone.utc),
            cash_balance=total_cash,
            positions=consolidated_positions,
            total_value=total_value,
        )
