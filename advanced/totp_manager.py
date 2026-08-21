# totp_manager.py
import io
import base64
import time

from advanced.encryption_advanced import ZeroKnowledgeEncryption

class TOTPManager:
    def __init__(self, encryption_key):
        self.encryption_key = encryption_key
        self.encryption = ZeroKnowledgeEncryption()

    @staticmethod
    def _pyotp():
        try:
            import pyotp
            return pyotp
        except ImportError as exc:
            raise RuntimeError("TOTP support requires the pyotp package") from exc
    
    def generate_secret(self):
        """Generate a new TOTP secret"""
        return self._pyotp().random_base32()
    
    def encrypt_secret(self, secret):
        """Encrypt TOTP secret for storage"""
        return self.encryption.encrypt_data(secret, self.encryption_key)
    
    def decrypt_secret(self, encrypted_secret):
        """Decrypt TOTP secret"""
        return self.encryption.decrypt_data(encrypted_secret, self.encryption_key).decode()
    
    def generate_qr_code(self, secret, account_name, issuer_name):
        """Generate QR code for TOTP setup"""
        pyotp = self._pyotp()
        try:
            import qrcode
        except ImportError as exc:
            raise RuntimeError("QR-code generation requires the qrcode package") from exc
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
        totp = self._pyotp().TOTP(secret)
        return totp.now()
    
    def verify_code(self, secret, code):
        """Verify TOTP code"""
        totp = self._pyotp().TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    def get_time_remaining(self):
        """Get seconds until next TOTP refresh"""
        return 30 - (int(time.time()) % 30)
