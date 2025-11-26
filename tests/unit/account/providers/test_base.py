"""Unit tests for AccountProvider abstract interface."""

import pytest
from abc import ABC


class TestAccountProviderInterface:
    """Test AccountProvider abstract base class."""

    def test_account_provider_is_abstract(self):
        """Test that AccountProvider cannot be instantiated directly."""
        from src.account.providers.base import AccountProvider

        assert issubclass(AccountProvider, ABC)

        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            AccountProvider()

    def test_account_provider_defines_required_methods(self):
        """Test that AccountProvider defines required abstract methods."""
        from src.account.providers.base import AccountProvider

        # Check that abstract methods are defined
        abstract_methods = AccountProvider.__abstractmethods__
        assert "authenticate" in abstract_methods
        assert "fetch_holdings" in abstract_methods

    def test_concrete_provider_must_implement_methods(self):
        """Test that concrete providers must implement all abstract methods."""
        from src.account.providers.base import AccountProvider

        # Create a concrete class that doesn't implement required methods
        class IncompleteProvider(AccountProvider):
            pass

        # Should not be able to instantiate without implementing abstract methods
        with pytest.raises(TypeError):
            IncompleteProvider()


class TestBrokerageProviderDataclass:
    """Test BrokerageProvider dataclass."""

    def test_brokerage_provider_creation(self):
        """Test creating a BrokerageProvider instance."""
        from src.account.providers.base import BrokerageProvider

        provider = BrokerageProvider(
            name="korea_investment",
            display_name="Korea Investment & Securities",
            api_base_url="https://openapi.koreainvestment.com:9443",
            rate_limit_delay=1.1,
        )

        assert provider.name == "korea_investment"
        assert provider.display_name == "Korea Investment & Securities"
        assert provider.rate_limit_delay == 1.1
