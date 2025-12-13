"""Token caching for persistent authentication across CLI sessions."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from cryptography.fernet import InvalidToken

from src.account.crypto import encrypt, decrypt, get_encryption_key_from_env
from src.account.models import BrokerageAccount, AccountStatus

logger = logging.getLogger(__name__)


class TokenCache:
    """
    File-based token cache for persistent authentication.

    Tokens are encrypted and stored in a cache directory to avoid
    repeated authentication requests that hit rate limits.
    """

    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize token cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(mode=0o700, exist_ok=True)  # Restrictive permissions
        self.cache_file = self.cache_dir / "tokens.enc"

    def get(self, account_id: str) -> Optional[BrokerageAccount]:
        """
        Get cached account with token if valid.

        Args:
            account_id: Account identifier

        Returns:
            BrokerageAccount if cached and valid, None otherwise
        """
        if not self.cache_file.exists():
            return None

        try:
            # Read and decrypt cache file
            with open(self.cache_file, "r") as f:
                encrypted_data = f.read()

            key = get_encryption_key_from_env()
            decrypted_json = decrypt(encrypted_data, key)
            cache_data = json.loads(decrypted_json)

            # Get account data
            account_data = cache_data.get(account_id)
            if not account_data:
                return None

            # Reconstruct account
            account = BrokerageAccount(
                account_id=account_data["account_id"],
                provider=account_data["provider"],
                account_number=account_data["account_number"],
                status=AccountStatus[account_data["status"]],
                access_token=account_data.get("access_token"),
                token_expiry=datetime.fromisoformat(account_data["token_expiry"])
                if account_data.get("token_expiry")
                else None,
            )

            # Check if still valid
            if account.is_authenticated():
                return account
            else:
                # Token expired, remove from cache
                self.remove(account_id)
                return None

        except (json.JSONDecodeError, InvalidToken) as e:
            # Cache corrupted or decryption failed
            logger.warning(f"Token cache corrupted for {account_id}: {e}")
            return None
        except (OSError, PermissionError) as e:
            # File system errors
            logger.error(f"Error reading token cache: {e}")
            return None
        except Exception as e:
            # Unexpected errors - log and re-raise to avoid hiding bugs
            logger.error(f"Unexpected error reading token cache for {account_id}: {e}")
            raise

    def set(self, account: BrokerageAccount) -> None:
        """
        Cache an authenticated account.

        Args:
            account: Authenticated account to cache
        """
        if not account.is_authenticated():
            return

        # Load existing cache
        cache_data = {}
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    encrypted_data = f.read()
                key = get_encryption_key_from_env()
                decrypted_json = decrypt(encrypted_data, key)
                cache_data = json.loads(decrypted_json)
            except (json.JSONDecodeError, InvalidToken) as e:
                # Cache corrupted, start fresh
                logger.warning(f"Token cache corrupted, starting fresh: {e}")
                cache_data = {}
            except (OSError, PermissionError) as e:
                logger.error(f"Error loading token cache: {e}")
                raise

        # Update cache with new account
        cache_data[account.account_id] = {
            "account_id": account.account_id,
            "provider": account.provider,
            "account_number": account.account_number,
            "status": account.status.name,
            "access_token": account.access_token,
            "token_expiry": account.token_expiry.isoformat()
            if account.token_expiry
            else None,
        }

        # Encrypt and save
        cache_json = json.dumps(cache_data)
        key = get_encryption_key_from_env()
        encrypted_data = encrypt(cache_json, key)

        # Write with restrictive permissions (owner read/write only)
        # Create file if it doesn't exist with proper permissions
        if not self.cache_file.exists():
            self.cache_file.touch(mode=0o600)

        with open(self.cache_file, "w") as f:
            f.write(encrypted_data)

        # Ensure permissions are correct (in case umask interfered)
        os.chmod(self.cache_file, 0o600)

    def remove(self, account_id: str) -> None:
        """
        Remove an account from cache.

        Args:
            account_id: Account identifier
        """
        if not self.cache_file.exists():
            return

        try:
            # Load existing cache
            with open(self.cache_file, "r") as f:
                encrypted_data = f.read()
            key = get_encryption_key_from_env()
            decrypted_json = decrypt(encrypted_data, key)
            cache_data = json.loads(decrypted_json)

            # Remove account
            if account_id in cache_data:
                del cache_data[account_id]

            # Save updated cache
            cache_json = json.dumps(cache_data)
            encrypted_data = encrypt(cache_json, key)

            with open(self.cache_file, "w") as f:
                f.write(encrypted_data)

        except (json.JSONDecodeError, InvalidToken) as e:
            # Cache corrupted, can't remove - log warning
            logger.warning(f"Could not remove {account_id} from corrupted cache: {e}")
        except (OSError, PermissionError) as e:
            logger.error(f"Error removing from token cache: {e}")
            raise

    def clear(self) -> None:
        """Clear all cached tokens."""
        if self.cache_file.exists():
            self.cache_file.unlink()
