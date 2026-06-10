"""AES-256-GCM encryption utilities for credential storage."""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


def _get_key() -> bytes:
    """Get encryption key from settings."""
    key_hex = settings.ENCRYPTION_KEY
    return bytes.fromhex(key_hex)


def encrypt(plaintext: str) -> str:
    """Encrypt a string using AES-256-GCM. Returns base64-encoded ciphertext."""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    # Store nonce + ciphertext together
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt(encrypted: str) -> str:
    """Decrypt a base64-encoded AES-256-GCM ciphertext."""
    key = _get_key()
    data = base64.b64decode(encrypted)
    nonce = data[:12]
    ciphertext = data[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()


def mask_token(token: str) -> str:
    """Mask a token for display. Shows first 10 chars + '...'."""
    if len(token) <= 10:
        return token[:3] + "..."
    return token[:10] + "..."
