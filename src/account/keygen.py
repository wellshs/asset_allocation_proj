"""Encryption key generator utility."""

from src.account.crypto import generate_key

if __name__ == "__main__":
    key = generate_key()
    print(f"Generated encryption key: {key}")
    print("\nSet this as environment variable ACCOUNT_ENCRYPTION_KEY:")
    print(f'export ACCOUNT_ENCRYPTION_KEY="{key}"')
