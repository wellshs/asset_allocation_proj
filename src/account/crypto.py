"""Cryptographic utilities for secure credential storage."""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        str: URL-safe base64-encoded encryption key
    """
    return Fernet.generate_key().decode("utf-8")


def encrypt(plaintext: str, key: str) -> str:
    """
    Encrypt plaintext using Fernet symmetric encryption.

    Args:
        plaintext: The text to encrypt
        key: URL-safe base64-encoded Fernet key

    Returns:
        str: Encrypted ciphertext (URL-safe base64-encoded)
    """
    f = Fernet(key.encode("utf-8"))
    encrypted = f.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt(ciphertext: str, key: str) -> str:
    """
    Decrypt ciphertext using Fernet symmetric encryption.

    Args:
        ciphertext: The encrypted text (URL-safe base64-encoded)
        key: URL-safe base64-encoded Fernet key

    Returns:
        str: Decrypted plaintext

    Raises:
        cryptography.fernet.InvalidToken: If decryption fails
    """
    f = Fernet(key.encode("utf-8"))
    decrypted = f.decrypt(ciphertext.encode("utf-8"))
    return decrypted.decode("utf-8")


def derive_key_from_password(
    password: str, salt: bytes, iterations: int = 100000
) -> str:
    """
    Derive an encryption key from a password using PBKDF2.

    Args:
        password: The password to derive key from
        salt: Salt for key derivation (should be unique per application)
        iterations: Number of PBKDF2 iterations (default: 100000)

    Returns:
        str: URL-safe base64-encoded Fernet key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key.decode("utf-8")


def get_encryption_key_from_env() -> str:
    """
    Get encryption key from ACCOUNT_ENCRYPTION_KEY environment variable.

    Returns:
        str: Encryption key

    Raises:
        ValueError: If ACCOUNT_ENCRYPTION_KEY is not set
    """
    key = os.environ.get("ACCOUNT_ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "ACCOUNT_ENCRYPTION_KEY environment variable is not set. "
            "Generate a key using: python -m src.account.keygen"
        )
    return key
