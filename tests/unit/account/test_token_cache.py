"""Unit tests for TokenCache."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory

from src.account.token_cache import TokenCache
from src.account.models import BrokerageAccount, AccountStatus
from src.account.crypto import generate_key


class TestTokenCacheGet:
    """Test TokenCache.get() method."""

    @patch("src.account.token_cache.get_encryption_key_from_env")
    def test_get_valid_token(self, mock_get_key):
        """Test getting a valid cached token."""
        # Use a valid Fernet key
        mock_get_key.return_value = generate_key()

        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            # Create a valid account
            account = BrokerageAccount(
                account_id="test_account",
                provider="korea_investment",
                account_number="1234567890",
                status=AccountStatus.CONNECTED,
                access_token="test_token",
                token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            )

            # Cache it
            cache.set(account)

            # Retrieve it
            cached = cache.get("test_account")

            assert cached is not None
            assert cached.account_id == "test_account"
            assert cached.access_token == "test_token"
            assert cached.is_authenticated()

    @patch("src.account.token_cache.get_encryption_key_from_env")
    def test_get_expired_token(self, mock_get_key):
        """Test getting an expired token returns None."""
        mock_get_key.return_value = generate_key()

        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            # Create an expired account
            account = BrokerageAccount(
                account_id="test_account",
                provider="korea_investment",
                account_number="1234567890",
                status=AccountStatus.CONNECTED,
                access_token="expired_token",
                token_expiry=datetime.now(timezone.utc) - timedelta(hours=1),
            )

            # Cache it
            cache.set(account)

            # Try to retrieve - should return None
            cached = cache.get("test_account")

            assert cached is None

    def test_get_nonexistent_account(self):
        """Test getting a non-existent account returns None."""
        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            cached = cache.get("nonexistent")

            assert cached is None

    def test_get_no_cache_file(self):
        """Test getting when cache file doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            cached = cache.get("test_account")

            assert cached is None

    @patch("src.account.token_cache.get_encryption_key_from_env")
    def test_get_corrupted_cache_file(self, mock_get_key):
        """Test handling of corrupted cache file."""
        mock_get_key.return_value = generate_key()

        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)
            cache_file = Path(tmpdir) / "tokens.enc"

            # Write corrupted data
            cache_file.write_text("corrupted_data_not_valid_encryption")

            # Should return None without crashing
            cached = cache.get("test_account")

            assert cached is None

    @patch("src.account.token_cache.get_encryption_key_from_env")
    def test_get_missing_encryption_key(self, mock_get_key):
        """Test handling when encryption key is missing."""
        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            # Create a valid cached token first with a valid Fernet key
            key1 = generate_key()  # Generate a proper Fernet key
            mock_get_key.return_value = key1
            account = BrokerageAccount(
                account_id="test",
                provider="korea_investment",
                account_number="1234567890",
                status=AccountStatus.CONNECTED,
                access_token="token",
                token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            cache.set(account)

            # Now try to get with a different valid key (simulates key mismatch)
            key2 = generate_key()  # Different key
            mock_get_key.return_value = key2

            # Should return None due to decryption failure
            cached = cache.get("test")
            assert cached is None


class TestTokenCacheSet:
    """Test TokenCache.set() method."""

    @patch("src.account.token_cache.get_encryption_key_from_env")
    def test_set_valid_account(self, mock_get_key):
        """Test caching a valid authenticated account."""
        mock_get_key.return_value = generate_key()

        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            account = BrokerageAccount(
                account_id="test_account",
                provider="korea_investment",
                account_number="1234567890",
                status=AccountStatus.CONNECTED,
                access_token="test_token",
                token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            )

            cache.set(account)

            # Verify cache file exists
            cache_file = Path(tmpdir) / "tokens.enc"
            assert cache_file.exists()

            # Verify we can retrieve it
            cached = cache.get("test_account")
            assert cached is not None
            assert cached.access_token == "test_token"

    def test_set_unauthenticated_account(self):
        """Test setting an unauthenticated account does nothing."""
        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            account = BrokerageAccount(
                account_id="test_account",
                provider="korea_investment",
                account_number="1234567890",
                status=AccountStatus.DISCONNECTED,
            )

            cache.set(account)

            # Cache file should not exist
            cache_file = Path(tmpdir) / "tokens.enc"
            assert not cache_file.exists()

    @patch("src.account.token_cache.get_encryption_key_from_env")
    def test_set_multiple_accounts(self, mock_get_key):
        """Test caching multiple accounts."""
        mock_get_key.return_value = generate_key()

        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            account1 = BrokerageAccount(
                account_id="account1",
                provider="korea_investment",
                account_number="1111111111",
                status=AccountStatus.CONNECTED,
                access_token="token1",
                token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            )

            account2 = BrokerageAccount(
                account_id="account2",
                provider="korea_investment",
                account_number="2222222222",
                status=AccountStatus.CONNECTED,
                access_token="token2",
                token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            )

            cache.set(account1)
            cache.set(account2)

            # Verify both can be retrieved
            cached1 = cache.get("account1")
            cached2 = cache.get("account2")

            assert cached1.access_token == "token1"
            assert cached2.access_token == "token2"

    @patch("src.account.token_cache.get_encryption_key_from_env")
    def test_set_updates_existing_account(self, mock_get_key):
        """Test updating an existing cached account."""
        mock_get_key.return_value = generate_key()

        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            # Cache initial account
            account = BrokerageAccount(
                account_id="test_account",
                provider="korea_investment",
                account_number="1234567890",
                status=AccountStatus.CONNECTED,
                access_token="old_token",
                token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            cache.set(account)

            # Update with new token
            account.access_token = "new_token"
            account.token_expiry = datetime.now(timezone.utc) + timedelta(hours=2)
            cache.set(account)

            # Verify updated token
            cached = cache.get("test_account")
            assert cached.access_token == "new_token"


class TestTokenCacheRemove:
    """Test TokenCache.remove() method."""

    @patch("src.account.token_cache.get_encryption_key_from_env")
    def test_remove_existing_account(self, mock_get_key):
        """Test removing an existing cached account."""
        mock_get_key.return_value = generate_key()

        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            # Cache two accounts
            account1 = BrokerageAccount(
                account_id="account1",
                provider="korea_investment",
                account_number="1111111111",
                status=AccountStatus.CONNECTED,
                access_token="token1",
                token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            account2 = BrokerageAccount(
                account_id="account2",
                provider="korea_investment",
                account_number="2222222222",
                status=AccountStatus.CONNECTED,
                access_token="token2",
                token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            )

            cache.set(account1)
            cache.set(account2)

            # Remove account1
            cache.remove("account1")

            # Verify account1 is gone but account2 remains
            assert cache.get("account1") is None
            assert cache.get("account2") is not None

    def test_remove_nonexistent_account(self):
        """Test removing a non-existent account doesn't crash."""
        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            # Should not crash
            cache.remove("nonexistent")

    def test_remove_no_cache_file(self):
        """Test removing when cache file doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            # Should not crash
            cache.remove("test_account")


class TestTokenCacheClear:
    """Test TokenCache.clear() method."""

    @patch("src.account.token_cache.get_encryption_key_from_env")
    def test_clear_removes_cache_file(self, mock_get_key):
        """Test clearing removes the cache file."""
        mock_get_key.return_value = generate_key()

        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            # Cache an account
            account = BrokerageAccount(
                account_id="test_account",
                provider="korea_investment",
                account_number="1234567890",
                status=AccountStatus.CONNECTED,
                access_token="test_token",
                token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            cache.set(account)

            # Verify cache file exists
            cache_file = Path(tmpdir) / "tokens.enc"
            assert cache_file.exists()

            # Clear cache
            cache.clear()

            # Verify cache file is gone
            assert not cache_file.exists()

    def test_clear_no_cache_file(self):
        """Test clearing when cache file doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            # Should not crash
            cache.clear()


class TestTokenCacheEncryption:
    """Test encryption/decryption in TokenCache."""

    @patch("src.account.token_cache.get_encryption_key_from_env")
    def test_cache_file_is_encrypted(self, mock_get_key):
        """Test that cache file content is encrypted."""
        mock_get_key.return_value = generate_key()

        with TemporaryDirectory() as tmpdir:
            cache = TokenCache(cache_dir=tmpdir)

            account = BrokerageAccount(
                account_id="test_account",
                provider="korea_investment",
                account_number="1234567890",
                status=AccountStatus.CONNECTED,
                access_token="secret_token_12345",
                token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            )

            cache.set(account)

            # Read raw cache file
            cache_file = Path(tmpdir) / "tokens.enc"
            raw_content = cache_file.read_text()

            # Verify token is not in plain text
            assert "secret_token_12345" not in raw_content
            assert "test_account" not in raw_content

    def test_cache_dir_creation(self):
        """Test that cache directory is created if it doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "new_cache_dir"
            assert not cache_dir.exists()

            TokenCache(cache_dir=str(cache_dir))

            # Directory should be created
            assert cache_dir.exists()
            assert cache_dir.is_dir()
