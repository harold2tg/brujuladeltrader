"""Tests for cTrader module."""

import pytest

from app.shared.crypto import decrypt, encrypt, mask_token


class TestCrypto:
    """Tests for AES-256-GCM encryption utilities."""

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "my_secret_api_key_12345"
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertext(self):
        plaintext = "same_text"
        enc1 = encrypt(plaintext)
        enc2 = encrypt(plaintext)
        # Different nonces should produce different ciphertext
        assert enc1 != enc2

    def test_mask_token_long(self):
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        masked = mask_token(token)
        assert masked == "eyJhbGciOi..."
        assert len(masked) == 13

    def test_mask_token_short(self):
        token = "abc"
        masked = mask_token(token)
        assert masked == "abc..."

    def test_encrypt_empty_string(self):
        encrypted = encrypt("")
        decrypted = decrypt(encrypted)
        assert decrypted == ""

    def test_encrypt_unicode(self):
        plaintext = "ñáéíóú"
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)
        assert decrypted == plaintext
