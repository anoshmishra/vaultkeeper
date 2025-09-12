# secure_sharing.py
import secrets
import json
import base64
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import hashlib

class SecureSharing:
    def __init__(self):
        self.shares = {}  # In production, use secure database
    
    def create_one_time_share(self, data, expiry_hours=24, max_views=1):
        """Create a one-time secure share"""
        
        # Generate unique share ID
        share_id = secrets.token_urlsafe(32)
        
        # Generate encryption key for this share
        share_key = Fernet.generate_key()
        cipher = Fernet(share_key)
        
        # Encrypt the data
        encrypted_data = cipher.encrypt(json.dumps(data).encode())
        
        # Create expiry time
        expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        # Store share info
        self.shares[share_id] = {
            'encrypted_data': encrypted_data,
            'key': share_key,
            'expiry': expiry_time,
            'max_views': max_views,
            'view_count': 0,
            'created': datetime.utcnow()
        }
        
        # Create shareable link (in production, this would be a web URL)
        share_link = f"vaultkeeper://share/{share_id}"
        
        return {
            'share_id': share_id,
            'share_link': share_link,
            'expiry': expiry_time,
            'max_views': max_views
        }
    
    def retrieve_share(self, share_id):
        """Retrieve and decrypt shared data"""
        
        if share_id not in self.shares:
            return {'error': 'Share not found'}
        
        share = self.shares[share_id]
        
        # Check expiry
        if datetime.utcnow() > share['expiry']:
            del self.shares[share_id]
            return {'error': 'Share has expired'}
        
        # Check view limit
        if share['view_count'] >= share['max_views']:
            del self.shares[share_id]
            return {'error': 'Share view limit exceeded'}
        
        # Decrypt data
        cipher = Fernet(share['key'])
        decrypted_data = json.loads(cipher.decrypt(share['encrypted_data']).decode())
        
        # Increment view count
        share['view_count'] += 1
        
        # Delete if max views reached
        if share['view_count'] >= share['max_views']:
            del self.shares[share_id]
        
        return {
            'data': decrypted_data,
            'remaining_views': share['max_views'] - share['view_count'],
            'expires_at': share['expiry']
        }
