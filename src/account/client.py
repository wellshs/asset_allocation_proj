"""Client utilities for API requests with retry logic."""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from src.account.exceptions import AccountAPIException


def with_retry(func):
    """
    Decorator for exponential backoff retry logic.

    Retries API exceptions up to 3 times with exponential backoff (1s, 2s, 4s).
    Does not retry authentication errors.

    Args:
        func: Function to wrap with retry logic

    Returns:
        Wrapped function with retry behavior
    """
    return retry(
        stop=stop_after_attempt(3),  # 3 total attempts
        wait=wait_exponential(multiplier=1, min=1, max=4),  # 1s, 2s, 4s
        retry=retry_if_exception_type(AccountAPIException),  # Only retry API errors
        reraise=True,  # Re-raise the last exception if all retries fail
    )(func)
