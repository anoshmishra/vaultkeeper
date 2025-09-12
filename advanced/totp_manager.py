# totp_manager.py
import pyotp
import qrcode
import io
import base64
from cryptography.fernet import Fernet
import time
import json

class TOTPManager:
    def __init__(self, encryption_key):
        self.encryption_key = encryption_key
        self.cipher = Fernet(encryption_key)
    
    def generate_secret(self):
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def encrypt_secret(self, secret):
        """Encrypt TOTP secret for storage"""
        return self.cipher.encrypt(secret.encode())
    
    def decrypt_secret(self, encrypted_secret):
        """Decrypt TOTP secret"""
        return self.cipher.decrypt(encrypted_secret).decode()
    
    def generate_qr_code(self, secret, account_name, issuer_name):
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=account_name,
            issuer_name=issuer_name
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for display
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    
    def get_current_code(self, secret):
        """Get current TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.now()
    
    def verify_code(self, secret, code):
        """Verify TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    def get_time_remaining(self):
        """Get seconds until next TOTP refresh"""
        return 30 - (int(time.time()) % 30)
