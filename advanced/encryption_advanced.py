# encryption_advanced.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from argon2 import PasswordHasher
import os
import base64
import secrets

class ZeroKnowledgeEncryption:
    def __init__(self):
        self.ph = PasswordHasher(
            time_cost=3,      # Number of iterations
            memory_cost=65536, # Memory usage in KB
            parallelism=1,    # Number of parallel threads
            hash_len=32,      # Length of hash
            salt_len=16       # Length of salt
        )
    
    def generate_master_salt(self):
        """Generate cryptographically secure salt"""
        return os.urandom(32)
    
    def derive_master_key(self, master_password, salt, iterations=100000):
        """Derive master key using PBKDF2 with high iteration count"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    
    def generate_vault_key(self):
        """Generate unique vault encryption key"""
        return Fernet.generate_key()
    
    def encrypt_vault_key(self, vault_key, master_key):
        """Encrypt vault key with master key (key wrapping)"""
        f = Fernet(master_key)
        return f.encrypt(vault_key)
    
    def decrypt_vault_key(self, encrypted_vault_key, master_key):
        """Decrypt vault key using master key"""
        f = Fernet(master_key)
        return f.decrypt(encrypted_vault_key)
    
    def encrypt_data(self, data, key):
        """Encrypt sensitive data"""
        f = Fernet(key)
        return f.encrypt(data.encode() if isinstance(data, str) else data)
    
    def decrypt_data(self, encrypted_data, key):
        """Decrypt sensitive data"""
        f = Fernet(key)
        return f.decrypt(encrypted_data)
