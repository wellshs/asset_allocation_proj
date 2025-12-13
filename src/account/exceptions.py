"""Account-specific exceptions."""


class AccountException(Exception):
    """Base exception for account operations."""

    pass


class AccountAuthException(AccountException):
    """Exception raised when authentication fails."""

    pass


class AccountAPIException(AccountException):
    """Exception raised when API requests fail."""

    pass


class AccountRateLimitException(AccountException):
    """Exception raised when rate limit is exceeded."""

    pass
