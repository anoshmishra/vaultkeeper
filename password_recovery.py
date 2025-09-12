#!/usr/bin/env python3
# password_recovery.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced.encryption_advanced import ZeroKnowledgeEncryption
from advanced.database_advanced import get_user_advanced

def test_password_systematically():
    """Test password variations systematically"""
    
    print("🔐 VaultKeeper Password Recovery Tool")
    print("=" * 50)
    
    # Initialize encryption
    encryption = ZeroKnowledgeEncryption()
    
    # Get stored hash from database
    try:
        user_data = get_user_advanced()
        if not user_data:
            print("❌ No user data found in database")
            return False
        
        master_hash = user_data[0]  # First element is master_password_hash
        print("✅ Database loaded successfully")
        
    except Exception as e:
        print(f"❌ Could not read database: {e}")
        return False
    
    # Get base passwords from user
    print("\n📝 Enter potential passwords (one per line)")
    print("💡 Think about passwords you used in late 2024/early 2025")
    print("💡 Include variations you typically use")
    print("💡 Press Enter on empty line when done:")
    
    base_passwords = []
    while True:
        password = input("Password guess: ").strip()
        if not password:
            break
        base_passwords.append(password)
    
    if not base_passwords:
        print("❌ No passwords provided")
        return False
    
    # Generate variations
    variations = []
    for base in base_passwords:
        variations.extend([
            base,
            base.lower(),
            base.upper(),
            base.capitalize(),
            f"{base}123",
            f"{base}2024",
            f"{base}2025",
            f"{base}!",
            f"{base}@",
            f"{base}#",
            f"123{base}",
            f"!{base}",
            f"{base}1",
            f"{base}12",
            f"1{base}",
            f"{base.capitalize()}123",
            f"{base.capitalize()}2024",
            f"{base.capitalize()}2025",
            f"{base.capitalize()}!",
        ])
    
    # Remove duplicates
    variations = list(set(variations))
    
    print(f"\n🔍 Testing {len(variations)} password variations...")
    print("⏳ This may take a moment...")
    
    for i, password in enumerate(variations, 1):
        try:
            encryption.ph.verify(master_hash, password)
            print(f"\n🎉 SUCCESS! Your master password is: '{password}'")
            print("✅ You can now log into VaultKeeper!")
            return True
        except:
            if i % 5 == 0:
                print(f"   Tested {i}/{len(variations)} variations...")
            continue
    
    print(f"\n❌ No matches found in {len(variations)} variations")
    print("💡 Try different base passwords or contact for additional recovery options")
    return False

if __name__ == "__main__":
    test_password_systematically()


