# tests/test_encryption.py
import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import base64

# Add the parent directory to the path so we can import from advanced/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced.encryption_advanced import ZeroKnowledgeEncryption

class TestEncryption(unittest.TestCase):
    """Comprehensive test suite for VaultKeeper encryption functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.encryption = ZeroKnowledgeEncryption()
        self.test_password = "MySecureTestPassword2025!"
        self.test_data = "This is sensitive test data that needs encryption"
        self.test_binary_data = b"Binary test data \x00\x01\x02\xff"
    
    def test_master_salt_generation(self):
        """Test master salt generation"""
        salt1 = self.encryption.generate_master_salt()
        salt2 = self.encryption.generate_master_salt()
        
        # Each salt should be 32 bytes
        self.assertEqual(len(salt1), 32)
        self.assertEqual(len(salt2), 32)
        
        # Salts should be different (cryptographically random)
        self.assertNotEqual(salt1, salt2)
        
        # Salt should be bytes type
        self.assertIsInstance(salt1, bytes)
        self.assertIsInstance(salt2, bytes)
    
    def test_master_key_derivation(self):
        """Test master key derivation from password and salt"""
        salt = self.encryption.generate_master_salt()
        
        # Derive master key
        master_key = self.encryption.derive_master_key(self.test_password, salt)
        
        # Key should be base64 encoded (44 characters for 32 bytes)
        self.assertEqual(len(master_key), 44)
        self.assertIsInstance(master_key, bytes)
        
        # Same password and salt should produce same key
        master_key2 = self.encryption.derive_master_key(self.test_password, salt)
        self.assertEqual(master_key, master_key2)
        
        # Different salt should produce different key
        different_salt = self.encryption.generate_master_salt()
        different_key = self.encryption.derive_master_key(self.test_password, different_salt)
        self.assertNotEqual(master_key, different_key)
    
    def test_master_key_derivation_with_iterations(self):
        """Test master key derivation with custom iterations"""
        salt = self.encryption.generate_master_salt()
        
        # Test with different iteration counts
        key_1000 = self.encryption.derive_master_key(self.test_password, salt, iterations=1000)
        key_50000 = self.encryption.derive_master_key(self.test_password, salt, iterations=50000)
        
        # Different iteration counts should produce different keys
        self.assertNotEqual(key_1000, key_50000)
        
        # Same iteration count should produce same key
        key_1000_repeat = self.encryption.derive_master_key(self.test_password, salt, iterations=1000)
        self.assertEqual(key_1000, key_1000_repeat)
    
    def test_vault_key_generation(self):
        """Test vault key generation"""
        vault_key1 = self.encryption.generate_vault_key()
        vault_key2 = self.encryption.generate_vault_key()
        
        # Vault keys should be different
        self.assertNotEqual(vault_key1, vault_key2)
        
        # Should be Fernet-compatible keys (44 characters base64)
        self.assertEqual(len(vault_key1), 44)
        self.assertEqual(len(vault_key2), 44)
        
        # Should be bytes type
        self.assertIsInstance(vault_key1, bytes)
        self.assertIsInstance(vault_key2, bytes)
    
    def test_vault_key_encryption_decryption(self):
        """Test vault key encryption and decryption with master key"""
        salt = self.encryption.generate_master_salt()
        master_key = self.encryption.derive_master_key(self.test_password, salt)
        vault_key = self.encryption.generate_vault_key()
        
        # Encrypt vault key with master key
        encrypted_vault_key = self.encryption.encrypt_vault_key(vault_key, master_key)
        
        # Encrypted key should be different from original
        self.assertNotEqual(vault_key, encrypted_vault_key)
        
        # Decrypt vault key
        decrypted_vault_key = self.encryption.decrypt_vault_key(encrypted_vault_key, master_key)
        
        # Decrypted key should match original
        self.assertEqual(vault_key, decrypted_vault_key)
    
    def test_data_encryption_decryption_string(self):
        """Test data encryption and decryption with string data"""
        vault_key = self.encryption.generate_vault_key()
        
        # Encrypt string data
        encrypted_data = self.encryption.encrypt_data(self.test_data, vault_key)
        
        # Encrypted data should be different from original
        self.assertNotEqual(self.test_data.encode(), encrypted_data)
        self.assertIsInstance(encrypted_data, bytes)
        
        # Decrypt data
        decrypted_data = self.encryption.decrypt_data(encrypted_data, vault_key)
        
        # Decrypted data should match original
        self.assertEqual(self.test_data.encode(), decrypted_data)
        self.assertEqual(self.test_data, decrypted_data.decode())
    
    def test_data_encryption_decryption_binary(self):
        """Test data encryption and decryption with binary data"""
        vault_key = self.encryption.generate_vault_key()
        
        # Encrypt binary data
        encrypted_data = self.encryption.encrypt_data(self.test_binary_data, vault_key)
        
        # Encrypted data should be different from original
        self.assertNotEqual(self.test_binary_data, encrypted_data)
        self.assertIsInstance(encrypted_data, bytes)
        
        # Decrypt data
        decrypted_data = self.encryption.decrypt_data(encrypted_data, vault_key)
        
        # Decrypted data should match original
        self.assertEqual(self.test_binary_data, decrypted_data)
    
    def test_encryption_with_wrong_key(self):
        """Test that decryption fails with wrong key"""
        vault_key1 = self.encryption.generate_vault_key()
        vault_key2 = self.encryption.generate_vault_key()
        
        # Encrypt with first key
        encrypted_data = self.encryption.encrypt_data(self.test_data, vault_key1)
        
        # Try to decrypt with second key (should fail)
        with self.assertRaises(Exception):
            self.encryption.decrypt_data(encrypted_data, vault_key2)
    
    def test_password_hashing(self):
        """Test password hashing functionality"""
        # Hash a password
        password_hash = self.encryption.ph.hash(self.test_password)
        
        # Hash should be string
        self.assertIsInstance(password_hash, str)
        
        # Hash should contain Argon2 identifier
        self.assertIn("$argon2", password_hash)
        
        # Same password should verify successfully
        self.assertTrue(self.encryption.ph.verify(password_hash, self.test_password))
        
        # Wrong password should fail verification
        with self.assertRaises(Exception):
            self.encryption.ph.verify(password_hash, "wrong_password")
    
    def test_password_hashing_different_passwords(self):
        """Test that different passwords produce different hashes"""
        hash1 = self.encryption.ph.hash("password1")
        hash2 = self.encryption.ph.hash("password2")
        hash3 = self.encryption.ph.hash("password1")  # Same as first
        
        # Different passwords should produce different hashes
        self.assertNotEqual(hash1, hash2)
        
        # Same password should produce different hashes (due to salt)
        self.assertNotEqual(hash1, hash3)
        
        # But both hashes should verify the same password
        self.assertTrue(self.encryption.ph.verify(hash1, "password1"))
        self.assertTrue(self.encryption.ph.verify(hash3, "password1"))
    
    def test_encryption_deterministic(self):
        """Test that encryption is non-deterministic (includes IV/nonce)"""
        vault_key = self.encryption.generate_vault_key()
        
        # Encrypt same data twice
        encrypted1 = self.encryption.encrypt_data(self.test_data, vault_key)
        encrypted2 = self.encryption.encrypt_data(self.test_data, vault_key)
        
        # Encrypted results should be different (due to random IV)
        self.assertNotEqual(encrypted1, encrypted2)
        
        # But both should decrypt to same plaintext
        decrypted1 = self.encryption.decrypt_data(encrypted1, vault_key)
        decrypted2 = self.encryption.decrypt_data(encrypted2, vault_key)
        self.assertEqual(decrypted1, decrypted2)
        self.assertEqual(self.test_data, decrypted1.decode())
    
    def test_empty_data_encryption(self):
        """Test encryption of empty data"""
        vault_key = self.encryption.generate_vault_key()
        empty_data = ""
        
        # Encrypt empty string
        encrypted = self.encryption.encrypt_data(empty_data, vault_key)
        
        # Should still produce encrypted result
        self.assertIsInstance(encrypted, bytes)
        self.assertGreater(len(encrypted), 0)
        
        # Decrypt should return empty string
        decrypted = self.encryption.decrypt_data(encrypted, vault_key)
        self.assertEqual(empty_data.encode(), decrypted)
    
    def test_large_data_encryption(self):
        """Test encryption of large data"""
        vault_key = self.encryption.generate_vault_key()
        large_data = "A" * 10000  # 10KB of data
        
        # Encrypt large data
        encrypted = self.encryption.encrypt_data(large_data, vault_key)
        
        # Decrypt and verify
        decrypted = self.encryption.decrypt_data(encrypted, vault_key)
        self.assertEqual(large_data, decrypted.decode())
    
    def test_unicode_data_encryption(self):
        """Test encryption of unicode data"""
        vault_key = self.encryption.generate_vault_key()
        unicode_data = "Hello 🔐 World! Ñiño español 中文 العربية"
        
        # Encrypt unicode data
        encrypted = self.encryption.encrypt_data(unicode_data, vault_key)
        
        # Decrypt and verify
        decrypted = self.encryption.decrypt_data(encrypted, vault_key)
        self.assertEqual(unicode_data, decrypted.decode())
    
    def test_key_derivation_consistency(self):
        """Test that key derivation is consistent across multiple calls"""
        salt = b"test_salt_16_bytes_123456"[:32]  # Ensure 32 bytes
        password = "consistent_password"
        
        # Derive key multiple times
        key1 = self.encryption.derive_master_key(password, salt)
        key2 = self.encryption.derive_master_key(password, salt)
        key3 = self.encryption.derive_master_key(password, salt)
        
        # All keys should be identical
        self.assertEqual(key1, key2)
        self.assertEqual(key2, key3)
    
    def test_corrupted_data_handling(self):
        """Test handling of corrupted encrypted data"""
        vault_key = self.encryption.generate_vault_key()
        
        # Encrypt some data
        encrypted = self.encryption.encrypt_data(self.test_data, vault_key)
        
        # Corrupt the encrypted data
        corrupted = bytearray(encrypted)
        corrupted[10] = corrupted[10] ^ 1  # Flip one bit
        corrupted_bytes = bytes(corrupted)
        
        # Decryption should fail
        with self.assertRaises(Exception):
            self.encryption.decrypt_data(corrupted_bytes, vault_key)
    
    def test_invalid_key_handling(self):
        """Test handling of invalid keys"""
        # Test with invalid vault key
        with self.assertRaises(Exception):
            self.encryption.encrypt_data(self.test_data, b"invalid_key")
        
        # Test with None key
        with self.assertRaises(Exception):
            self.encryption.encrypt_data(self.test_data, None)
    
    def test_encryption_metadata(self):
        """Test that encrypted data contains proper Fernet metadata"""
        vault_key = self.encryption.generate_vault_key()
        encrypted = self.encryption.encrypt_data(self.test_data, vault_key)
        
        # Fernet tokens should be base64 decodable
        try:
            base64.urlsafe_b64decode(encrypted)
        except Exception:
            self.fail("Encrypted data is not valid base64")
        
        # Should be proper Fernet format (starts with version byte)
        decoded = base64.urlsafe_b64decode(encrypted)
        self.assertGreaterEqual(len(decoded), 45)  # Minimum Fernet token size
    
    def test_master_key_base64_encoding(self):
        """Test that master keys are properly base64 encoded"""
        salt = self.encryption.generate_master_salt()
        master_key = self.encryption.derive_master_key(self.test_password, salt)
        
        # Should be decodable as base64
        try:
            decoded = base64.urlsafe_b64decode(master_key)
            self.assertEqual(len(decoded), 32)  # Should be 32 bytes when decoded
        except Exception:
            self.fail("Master key is not valid base64")
    
    def test_argon2_parameters(self):
        """Test Argon2 password hashing parameters"""
        # Check that Argon2 is properly configured
        ph = self.encryption.ph
        
        # Should have reasonable security parameters
        self.assertGreaterEqual(ph.time_cost, 2)
        self.assertGreaterEqual(ph.memory_cost, 65536)
        self.assertEqual(ph.parallelism, 1)
        self.assertEqual(ph.hash_len, 32)
        self.assertEqual(ph.salt_len, 16)

class TestEncryptionIntegration(unittest.TestCase):
    """Integration tests for encryption workflow"""
    
    def setUp(self):
        self.encryption = ZeroKnowledgeEncryption()
    
    def test_full_encryption_workflow(self):
        """Test complete encryption workflow from password to data"""
        # Simulate full VaultKeeper encryption workflow
        master_password = "MyMasterPassword123!"
        sensitive_data = "Top secret password: SuperSecret123!"
        
        # 1. Generate master salt
        master_salt = self.encryption.generate_master_salt()
        
        # 2. Derive master key from password
        master_key = self.encryption.derive_master_key(master_password, master_salt)
        
        # 3. Generate vault key
        vault_key = self.encryption.generate_vault_key()
        
        # 4. Encrypt vault key with master key
        encrypted_vault_key = self.encryption.encrypt_vault_key(vault_key, master_key)
        
        # 5. Encrypt sensitive data with vault key
        encrypted_data = self.encryption.encrypt_data(sensitive_data, vault_key)
        
        # 6. Simulate storage and retrieval
        # (In real app, encrypted_vault_key and encrypted_data would be stored)
        
        # 7. Decrypt workflow
        # Derive master key again (user enters password)
        derived_master_key = self.encryption.derive_master_key(master_password, master_salt)
        self.assertEqual(master_key, derived_master_key)
        
        # Decrypt vault key
        decrypted_vault_key = self.encryption.decrypt_vault_key(encrypted_vault_key, derived_master_key)
        self.assertEqual(vault_key, decrypted_vault_key)
        
        # Decrypt sensitive data
        decrypted_data = self.encryption.decrypt_data(encrypted_data, decrypted_vault_key)
        self.assertEqual(sensitive_data, decrypted_data.decode())
    
    def test_password_change_workflow(self):
        """Test password change workflow"""
        old_password = "OldPassword123!"
        new_password = "NewPassword456!"
        test_data = "Sensitive information"
        
        # Initial setup with old password
        master_salt = self.encryption.generate_master_salt()
        old_master_key = self.encryption.derive_master_key(old_password, master_salt)
        vault_key = self.encryption.generate_vault_key()
        encrypted_vault_key_old = self.encryption.encrypt_vault_key(vault_key, old_master_key)
        encrypted_data = self.encryption.encrypt_data(test_data, vault_key)
        
        # Password change process
        # 1. Verify old password
        verified_old_key = self.encryption.derive_master_key(old_password, master_salt)
        decrypted_vault_key = self.encryption.decrypt_vault_key(encrypted_vault_key_old, verified_old_key)
        
        # 2. Re-encrypt vault key with new password
        new_master_key = self.encryption.derive_master_key(new_password, master_salt)
        encrypted_vault_key_new = self.encryption.encrypt_vault_key(decrypted_vault_key, new_master_key)
        
        # 3. Verify new password can access data
        new_derived_key = self.encryption.derive_master_key(new_password, master_salt)
        final_vault_key = self.encryption.decrypt_vault_key(encrypted_vault_key_new, new_derived_key)
        final_data = self.encryption.decrypt_data(encrypted_data, final_vault_key)
        
        self.assertEqual(test_data, final_data.decode())
        
        # 4. Verify old password no longer works
        with self.assertRaises(Exception):
            self.encryption.decrypt_vault_key(encrypted_vault_key_new, old_master_key)

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
