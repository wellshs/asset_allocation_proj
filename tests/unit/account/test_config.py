"""Unit tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import yaml


class TestConfigurationParsing:
    """Test configuration file parsing with pydantic."""

    def test_parse_valid_config(self):
        """Test parsing a valid configuration file."""
        from src.account.config import Config

        config_data = {
            "version": "1.0",
            "accounts": [
                {
                    "name": "Test Account",
                    "provider": "korea_investment",
                    "enabled": True,
                    "credentials": {
                        "app_key": "test_key",
                        "app_secret": "test_secret",
                        "account_number": "1234567890",
                    },
                    "settings": {
                        "rate_limit_delay": 1.1,
                        "timeout_seconds": 30,
                    },
                }
            ],
            "notifications": {
                "slack": {
                    "enabled": True,
                    "webhook_url": "https://hooks.slack.com/services/T/B/X",
                    "triggers": ["manual_refresh"],
                    "format": "detailed",
                }
            },
            "refresh": {"auto_enabled": False, "interval_minutes": 60},
        }

        config = Config(**config_data)

        assert config.version == "1.0"
        assert len(config.accounts) == 1
        assert config.accounts[0].name == "Test Account"
        assert config.accounts[0].provider == "korea_investment"
        assert config.notifications.slack.enabled is True
        assert config.refresh.auto_enabled is False

    def test_config_validation_missing_required_field(self):
        """Test that missing required fields raise validation errors."""
        from src.account.config import Config
        from pydantic import ValidationError

        config_data = {
            "version": "1.0",
            "accounts": [
                {
                    "name": "Test Account",
                    # Missing 'provider' field
                    "enabled": True,
                    "credentials": {
                        "app_key": "test_key",
                        "app_secret": "test_secret",
                        "account_number": "1234567890",
                    },
                }
            ],
        }

        with pytest.raises(ValidationError):
            Config(**config_data)

    def test_config_default_values(self):
        """Test that default values are applied."""
        from src.account.config import BrokerageAccountConfig

        account_config = BrokerageAccountConfig(
            name="Test",
            provider="korea_investment",
            enabled=True,
            credentials={
                "app_key": "key",
                "app_secret": "secret",
                "account_number": "1234567890",
            },
        )

        # Default settings should be applied
        assert account_config.settings.rate_limit_delay == 1.1
        assert account_config.settings.timeout_seconds == 30


class TestEncryptedCredentialLoading:
    """Test loading encrypted credentials from configuration."""

    def test_load_encrypted_credentials(self):
        """Test loading and decrypting credentials."""
        from src.account.config import load_config
        from src.account.crypto import encrypt, generate_key
        import os

        # Generate a test key
        key = generate_key()
        os.environ["ACCOUNT_ENCRYPTION_KEY"] = key

        # Create a temp config file with encrypted credentials
        encrypted_key = encrypt("my_app_key", key)
        encrypted_secret = encrypt("my_app_secret", key)
        encrypted_account = encrypt("1234567890", key)

        config_data = {
            "version": "1.0",
            "accounts": [
                {
                    "name": "Test Account",
                    "provider": "korea_investment",
                    "enabled": True,
                    "credentials": {
                        "app_key": encrypted_key,
                        "app_secret": encrypted_secret,
                        "account_number": encrypted_account,
                    },
                }
            ],
            "notifications": {
                "slack": {
                    "enabled": False,
                    "webhook_url": "",
                    "triggers": [],
                    "format": "summary",
                }
            },
            "refresh": {"auto_enabled": False, "interval_minutes": 60},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            config = load_config(config_path)
            credentials = config.accounts[0].credentials

            # Credentials should be decrypted
            assert credentials.app_key == "my_app_key"
            assert credentials.app_secret == "my_app_secret"
            assert credentials.account_number == "1234567890"
        finally:
            Path(config_path).unlink()
            del os.environ["ACCOUNT_ENCRYPTION_KEY"]

    def test_load_config_missing_encryption_key_raises_error(self):
        """Test that missing encryption key environment variable raises error."""
        from src.account.config import load_config
        from src.account.crypto import encrypt, generate_key
        import os

        # Make sure key is not in environment
        os.environ.pop("ACCOUNT_ENCRYPTION_KEY", None)

        # Create a config with encrypted data
        key = generate_key()
        encrypted_key = encrypt("my_app_key", key)

        config_data = {
            "version": "1.0",
            "accounts": [
                {
                    "name": "Test",
                    "provider": "korea_investment",
                    "enabled": True,
                    "credentials": {
                        "app_key": encrypted_key,
                        "app_secret": "secret",
                        "account_number": "1234567890",
                    },
                }
            ],
            "notifications": {
                "slack": {
                    "enabled": False,
                    "webhook_url": "",
                    "triggers": [],
                    "format": "summary",
                }
            },
            "refresh": {"auto_enabled": False, "interval_minutes": 60},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            with pytest.raises(
                (ValueError, KeyError)
            ):  # Should raise error for missing key
                load_config(config_path)
        finally:
            Path(config_path).unlink()
