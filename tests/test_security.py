# tests/test_security.py
import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from advanced.encryption_advanced import ZeroKnowledgeEncryption

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.encryption = ZeroKnowledgeEncryption()
    
    def test_encryption_decryption(self):
        """Test encryption and decryption"""
        key = self.encryption.generate_vault_key()
        test_data = "Test sensitive data"
        
        encrypted = self.encryption.encrypt_data(test_data, key)
        decrypted = self.encryption.decrypt_data(encrypted, key).decode()
        
        self.assertEqual(test_data, decrypted)
        self.assertNotEqual(test_data, encrypted)

if __name__ == '__main__':
    unittest.main()
