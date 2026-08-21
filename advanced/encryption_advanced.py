"""Cryptographic primitives used by the advanced vault.

New ciphertext is versioned AES-256-GCM.  Fernet decryption is retained only so
existing vaults can be opened and migrated without rewriting their data.
"""

import base64
import hashlib
import os

from argon2 import PasswordHasher, Type
from argon2.low_level import hash_secret_raw
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class ZeroKnowledgeEncryption:
    """Argon2id key derivation and authenticated vault encryption."""

    _CIPHERTEXT_VERSION = b"VK1"
    _NONCE_SIZE = 12

    def __init__(self):
        self.ph = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=1,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )

    def generate_master_salt(self):
        """Generate a cryptographically secure, per-vault salt."""
        return os.urandom(32)

    def derive_master_key(self, master_password, salt, iterations=None):
        """Derive a 256-bit wrapping key with Argon2id.

        ``iterations`` is retained as a compatibility argument for callers that
        used the previous PBKDF2 API.  It maps to Argon2's time cost; it does not
        weaken the default secure configuration.
        """
        if not isinstance(master_password, str) or not master_password:
            raise ValueError("A non-empty master password is required")
        if not isinstance(salt, bytes) or len(salt) < 16:
            raise ValueError("A salt of at least 16 bytes is required")

        time_cost = 3 if iterations is None else max(1, min((int(iterations) + 9999) // 10000, 10))
        raw_key = hash_secret_raw(
            secret=master_password.encode("utf-8"),
            salt=salt,
            time_cost=time_cost,
            memory_cost=65536,
            parallelism=1,
            hash_len=32,
            type=Type.ID,
        )
        return base64.urlsafe_b64encode(raw_key)

    @staticmethod
    def derive_legacy_master_key(master_password, salt, iterations=100000):
        """Derive the previous PBKDF2 key solely to migrate existing vaults."""
        return base64.urlsafe_b64encode(
            hashlib.pbkdf2_hmac("sha256", master_password.encode("utf-8"), salt, iterations, dklen=32)
        )

    @staticmethod
    def _raw_key(key):
        if isinstance(key, str):
            key = key.encode("ascii")
        try:
            raw_key = base64.urlsafe_b64decode(key)
        except Exception as exc:
            raise ValueError("Invalid encryption key") from exc
        if len(raw_key) != 32:
            raise ValueError("AES-256 requires a 32-byte key")
        return raw_key

    def generate_vault_key(self):
        """Generate a random AES-256 key in the legacy URL-safe key format."""
        return base64.urlsafe_b64encode(os.urandom(32))

    def encrypt_data(self, data, key, associated_data=None):
        """Encrypt bytes or text with AES-256-GCM and a unique random nonce."""
        plaintext = bytearray(data.encode("utf-8") if isinstance(data, str) else data)
        nonce = os.urandom(self._NONCE_SIZE)
        try:
            ciphertext = AESGCM(self._raw_key(key)).encrypt(nonce, bytes(plaintext), associated_data)
        finally:
            plaintext[:] = b"\x00" * len(plaintext)
        return self._CIPHERTEXT_VERSION + nonce + ciphertext

    def decrypt_data(self, encrypted_data, key, associated_data=None):
        """Decrypt current AES-GCM data or legacy Fernet ciphertext."""
        encrypted_data = bytes(encrypted_data)
        if encrypted_data.startswith(self._CIPHERTEXT_VERSION):
            nonce_start = len(self._CIPHERTEXT_VERSION)
            nonce_end = nonce_start + self._NONCE_SIZE
            if len(encrypted_data) <= nonce_end:
                raise ValueError("Invalid encrypted data")
            return AESGCM(self._raw_key(key)).decrypt(
                encrypted_data[nonce_start:nonce_end], encrypted_data[nonce_end:], associated_data
            )

        # Existing VaultKeeper releases wrote Fernet tokens.  This branch is
        # intentionally decrypt-only; all subsequent writes use AES-GCM.
        return Fernet(key).decrypt(encrypted_data)

    def encrypt_vault_key(self, vault_key, master_key):
        return self.encrypt_data(vault_key, master_key, b"vaultkeeper-vault-key")

    def decrypt_vault_key(self, encrypted_vault_key, master_key):
        try:
            return self.decrypt_data(encrypted_vault_key, master_key, b"vaultkeeper-vault-key")
        except Exception:
            # Legacy vault-key wrapping did not use associated data.
            return Fernet(master_key).decrypt(encrypted_vault_key)
