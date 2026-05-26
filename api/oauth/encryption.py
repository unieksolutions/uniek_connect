"""
Token encryption/decryption using Fernet (AES-128).
Encrypts OAuth refresh tokens before storing in database.
"""

from cryptography.fernet import Fernet
from api.config import get_settings

settings = get_settings()


def get_fernet() -> Fernet:
    """Get Fernet cipher for encryption/decryption."""
    if not settings.token_encryption_key:
        raise ValueError(
            "TOKEN_ENCRYPTION_KEY not set. Generate with: "
            "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )

    return Fernet(settings.token_encryption_key.encode())


def encrypt_token(token: str) -> str:
    """
    Encrypt a token string.

    Args:
        token: Plain text token to encrypt

    Returns:
        Encrypted token as string
    """
    fernet = get_fernet()
    encrypted = fernet.encrypt(token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a token string.

    Args:
        encrypted_token: Encrypted token string

    Returns:
        Decrypted plain text token
    """
    fernet = get_fernet()
    decrypted = fernet.decrypt(encrypted_token.encode())
    return decrypted.decode()
