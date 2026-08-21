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
    
    # Test biometric setup with a random vault key.  Master passwords are never
    # stored in Keychain for biometric unlock.
    print("\n🔧 Setting up biometric authentication...")
    test_vault_key = encryption.generate_vault_key()
    success, message = bio_auth.setup_secure_enclave_vault_key(test_vault_key)
    print(f"Setup Result: {'✅ Success' if success else '❌ Failed'}")
    
    if success:
        print("\n🔓 Testing biometric retrieval...")
        print("Note: Touch ID prompt should appear...")
        
        vault_data, message = bio_auth.authenticate_with_touchid()
        retrieved_key = vault_data and vault_data['vault_key']
        
        if retrieved_key:
            print(f"✅ Biometric authentication successful!")
            print(f"Retrieved key length: {len(retrieved_key)} bytes")
        else:
            print(f"❌ Biometric retrieval failed")

if __name__ == "__main__":
    test_biometric_setup()
