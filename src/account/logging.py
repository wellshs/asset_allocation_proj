"""Logging configuration for account operations."""

import logging
import os
import re
from functools import wraps


# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/account-integration.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("account")


def redact_credentials(text: str) -> str:
    """
    Redact sensitive credentials from log messages.

    Args:
        text: Text that may contain credentials

    Returns:
        str: Text with credentials redacted
    """
    # Redact tokens
    text = re.sub(r"Bearer [A-Za-z0-9_-]+", "Bearer [REDACTED]", text)

    # Redact API keys
    text = re.sub(r'"app_key":\s*"[^"]+', '"app_key": "[REDACTED]', text)
    text = re.sub(r'"app_secret":\s*"[^"]+', '"app_secret": "[REDACTED]', text)

    # Redact webhook URLs
    text = re.sub(
        r'https://hooks\.slack\.com/services/[^\s"]+',
        "https://hooks.slack.com/services/[REDACTED]",
        text,
    )

    return text


def log_api_call(func):
    """
    Decorator to log API calls with credential redaction.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.info(f"API call: {func_name}")

        try:
            result = func(*args, **kwargs)
            logger.info(f"API call successful: {func_name}")
            return result
        except Exception as e:
            error_msg = redact_credentials(str(e))
            logger.error(f"API call failed: {func_name} - {error_msg}")
            raise

    return wrapper
