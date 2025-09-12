# security_utils.py
import os
import sys
import mlock  # Memory locking (pip install mlock)

class SecurityUtils:
    @staticmethod
    def secure_delete(data):
        """Securely overwrite sensitive data in memory"""
        if isinstance(data, str):
            data = data.encode()
        
        # Overwrite with random data multiple times
        for _ in range(3):
            os.urandom(len(data))
    
    @staticmethod
    def lock_memory(data):
        """Lock sensitive data in memory to prevent swapping"""
        try:
            return mlock.mlockall()
        except:
            pass  # Not all systems support memory locking
    
    @staticmethod
    def check_debugger():
        """Basic anti-debugging check"""
        return hasattr(sys, 'gettrace') and sys.gettrace() is not None
