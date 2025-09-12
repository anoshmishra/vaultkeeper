# test_biometric.py (Updated)
from advanced.biometric_auth import BiometricAuth
from advanced.encryption_advanced import ZeroKnowledgeEncryption
import os

def test_biometric_setup():
    print("🔐 Testing VaultKeeper Biometric Authentication on Mac M4\n")
    
    # Initialize components
    bio_auth = BiometricAuth()
    encryption = ZeroKnowledgeEncryption()
    
    # Check Touch ID availability
    touchid_available = bio_auth.is_touchid_available()
    print(f"Touch ID Available: {'✅ Yes' if touchid_available else '❌ No'}")
    
    if not touchid_available:
        print("⚠️  Touch ID not detected. Biometric features will be disabled.")
        return
    
    # Test biometric setup with master password and salt
    print("\n🔧 Setting up biometric authentication...")
    test_master_password = "test_master_password_123"
    test_salt = b"test_salt_bytes_16ch"
    
    # Use the correct method name from your existing BiometricAuth class
    success = bio_auth.setup_biometric_unlock(test_master_password, test_salt)
    print(f"Setup Result: {'✅ Success' if success else '❌ Failed'}")
    
    if success:
        print("\n🔓 Testing biometric retrieval...")
        print("Note: Touch ID prompt should appear...")
        
        retrieved_key = bio_auth.retrieve_key_with_touchid()
        
        if retrieved_key:
            print(f"✅ Biometric authentication successful!")
            print(f"Retrieved key length: {len(retrieved_key)} bytes")
        else:
            print(f"❌ Biometric retrieval failed")

if __name__ == "__main__":
    test_biometric_setup()
