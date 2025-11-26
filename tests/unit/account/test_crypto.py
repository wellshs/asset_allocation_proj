"""Unit tests for cryptographic utilities."""

import pytest


class TestCrypto:
    """Test cryptographic functions for credential encryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption are inverse operations."""
        from src.account.crypto import encrypt, decrypt, generate_key

        # Generate a key for testing
        key = generate_key()
        plaintext = "my_secret_credential"

        # Encrypt then decrypt
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)

        assert decrypted == plaintext
        assert encrypted != plaintext  # Ensure it was actually encrypted

    def test_encrypt_produces_different_ciphertext(self):
        """Test that encrypting the same plaintext twice produces different ciphertext."""
        from src.account.crypto import encrypt, generate_key

        key = generate_key()
        plaintext = "my_secret"

        encrypted1 = encrypt(plaintext, key)
        encrypted2 = encrypt(plaintext, key)

        # Fernet includes random IV, so ciphertexts should differ
        assert encrypted1 != encrypted2

    def test_decrypt_with_wrong_key_raises_error(self):
        """Test that decryption with wrong key raises an error."""
        from src.account.crypto import encrypt, decrypt, generate_key

        key1 = generate_key()
        key2 = generate_key()
        plaintext = "secret"

        encrypted = encrypt(plaintext, key1)

        with pytest.raises(Exception):  # Fernet raises InvalidToken
            decrypt(encrypted, key2)

    def test_decrypt_invalid_ciphertext_raises_error(self):
        """Test that decrypting invalid ciphertext raises an error."""
        from src.account.crypto import decrypt, generate_key

        key = generate_key()
        invalid_ciphertext = "not_valid_encrypted_data"

        with pytest.raises(Exception):
            decrypt(invalid_ciphertext, key)


class TestPBKDF2KeyDerivation:
    """Test PBKDF2 key derivation for generating encryption keys."""

    def test_derive_key_from_password(self):
        """Test that key derivation produces consistent results."""
        from src.account.crypto import derive_key_from_password

        password = "my_secure_password"
        salt = b"fixed_salt_for_testing"

        key1 = derive_key_from_password(password, salt)
        key2 = derive_key_from_password(password, salt)

        assert key1 == key2  # Same password and salt should produce same key
        assert (
            len(key1) == 44
        )  # Fernet keys are URL-safe base64 encoded (32 bytes -> 44 chars)

    def test_derive_key_different_passwords_produce_different_keys(self):
        """Test that different passwords produce different keys."""
        from src.account.crypto import derive_key_from_password

        salt = b"fixed_salt"

        key1 = derive_key_from_password("password1", salt)
        key2 = derive_key_from_password("password2", salt)

        assert key1 != key2

    def test_derive_key_different_salts_produce_different_keys(self):
        """Test that different salts produce different keys."""
        from src.account.crypto import derive_key_from_password

        password = "same_password"

        key1 = derive_key_from_password(password, b"salt1")
        key2 = derive_key_from_password(password, b"salt2")

        assert key1 != key2
