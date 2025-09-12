# encryption.py
from cryptography.fernet import Fernet
from argon2 import PasswordHasher
import base64
import os
import hashlib

ph = PasswordHasher()  # Use this for master password verification

def hash_master_password(master_password):
    return ph.hash(master_password)

def verify_master_password(hashed, input_password):
    try:
        ph.verify(hashed, input_password)
        return True
    except:
        return False

def derive_key(master_password, salt):
    # Derive a 32 byte key from the master password and salt using PBKDF2
    return base64.urlsafe_b64encode(hashlib.pbkdf2_hmac(
        'sha256', master_password.encode(), salt, 100_000, dklen=32
    ))

def generate_salt():
    return os.urandom(16)

def encrypt_password(password, key):
    f = Fernet(key)
    return f.encrypt(password.encode())

def decrypt_password(token, key):
    f = Fernet(key)
    return f.decrypt(token).decode()
