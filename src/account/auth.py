"""Authentication logic for brokerage accounts."""

from datetime import datetime
from src.account.models import BrokerageAccount
from src.account.config import AccountCredentials
from src.account.exceptions import AccountAuthException


def get_provider(provider_name: str):
    """
    Get provider implementation by name.

    Args:
        provider_name: Provider identifier (e.g., "korea_investment")

    Returns:
        AccountProvider: Provider instance

    Raises:
        ValueError: If provider is not supported
    """
    if provider_name == "korea_investment":
        from src.account.providers.korea_investment import KoreaInvestmentProvider

        return KoreaInvestmentProvider()
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")


def authenticate(
    account: BrokerageAccount, credentials: AccountCredentials
) -> BrokerageAccount:
    """
    Authenticate with brokerage and obtain access token.

    Args:
        account: Account to authenticate
        credentials: API credentials

    Returns:
        BrokerageAccount: Updated account with access token

    Raises:
        AccountAuthException: If authentication fails
    """
    provider = get_provider(account.provider)

    try:
        authenticated_account = provider.authenticate(account, credentials)
        return authenticated_account
    except Exception as e:
        raise AccountAuthException(f"Authentication failed: {str(e)}")


def check_token_expiry(account: BrokerageAccount) -> bool:
    """
    Check if account's access token is still valid.

    Args:
        account: Account to check

    Returns:
        bool: True if token is valid, False if expired or missing
    """
    if account.token_expiry is None:
        return False
    return datetime.now() < account.token_expiry


def refresh_token(
    account: BrokerageAccount, credentials: AccountCredentials
) -> BrokerageAccount:
    """
    Refresh expired access token.

    Args:
        account: Account with expired token
        credentials: API credentials for re-authentication

    Returns:
        BrokerageAccount: Account with refreshed token
    """
    return authenticate(account, credentials)
