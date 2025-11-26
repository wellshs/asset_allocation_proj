"""Configuration management with pydantic validation."""

from typing import List
from pydantic import BaseModel, Field, field_validator
import yaml
from pathlib import Path

from src.account.crypto import decrypt, get_encryption_key_from_env


class AccountCredentials(BaseModel):
    """Brokerage account credentials."""

    app_key: str
    app_secret: str
    account_number: str


class AccountSettings(BaseModel):
    """Account-specific settings."""

    rate_limit_delay: float = Field(default=1.1, ge=0.1)
    timeout_seconds: int = Field(default=30, ge=1)


class BrokerageAccountConfig(BaseModel):
    """Configuration for a single brokerage account."""

    name: str
    provider: str
    enabled: bool = True
    credentials: AccountCredentials
    settings: AccountSettings = Field(default_factory=AccountSettings)


class SlackConfig(BaseModel):
    """Slack notification configuration."""

    enabled: bool = False
    webhook_url: str = ""
    triggers: List[str] = Field(default_factory=list)
    format: str = "detailed"  # "detailed" or "summary"


class NotificationConfig(BaseModel):
    """Notification settings."""

    slack: SlackConfig


class RefreshConfig(BaseModel):
    """Automatic refresh settings."""

    auto_enabled: bool = False
    interval_minutes: int = Field(default=60, ge=1)


class Config(BaseModel):
    """Root configuration model."""

    version: str
    accounts: List[BrokerageAccountConfig]
    notifications: NotificationConfig = Field(
        default_factory=lambda: NotificationConfig(
            slack=SlackConfig(
                enabled=False, webhook_url="", triggers=[], format="summary"
            )
        )
    )
    refresh: RefreshConfig = Field(default_factory=RefreshConfig)

    @field_validator("accounts")
    @classmethod
    def validate_accounts(
        cls, accounts: List[BrokerageAccountConfig]
    ) -> List[BrokerageAccountConfig]:
        """Validate that at least one account is configured."""
        if not accounts:
            raise ValueError("At least one account must be configured")
        return accounts


def load_config(config_path: str) -> Config:
    """
    Load configuration from YAML file and decrypt credentials.

    Args:
        config_path: Path to configuration file

    Returns:
        Config: Parsed and validated configuration

    Raises:
        ValueError: If encryption key is not set or config is invalid
        FileNotFoundError: If config file doesn't exist
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load YAML
    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)

    # Parse with pydantic
    config = Config(**config_data)

    # Decrypt credentials if they appear to be encrypted
    encryption_key = get_encryption_key_from_env()

    for account in config.accounts:
        account.credentials = decrypt_credentials(account.credentials, encryption_key)

    return config


def decrypt_credentials(
    credentials: AccountCredentials, encryption_key: str
) -> AccountCredentials:
    """
    Decrypt encrypted credentials.

    Args:
        credentials: Credentials object (may contain encrypted values)
        encryption_key: Encryption key for decryption

    Returns:
        AccountCredentials: Credentials with decrypted values
    """
    try:
        # Try to decrypt each field
        app_key = decrypt(credentials.app_key, encryption_key)
        app_secret = decrypt(credentials.app_secret, encryption_key)
        account_number = decrypt(credentials.account_number, encryption_key)

        return AccountCredentials(
            app_key=app_key, app_secret=app_secret, account_number=account_number
        )
    except Exception:
        # If decryption fails, assume credentials are plaintext
        # This allows for backwards compatibility and initial setup
        return credentials
