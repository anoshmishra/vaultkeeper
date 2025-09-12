# test_core.py
from advanced.encryption_advanced import ZeroKnowledgeEncryption
from advanced.password_generator import AdvancedPasswordGenerator
from advanced.database_advanced import init_advanced_db

# Test encryption
encryption = ZeroKnowledgeEncryption()
print("✓ Encryption module loaded")

# Test password generator
generator = AdvancedPasswordGenerator()
test_password = generator.generate_password(16)
print(f"✓ Generated password: {test_password}")

# Test database
init_advanced_db()
print("✓ Advanced database initialized")
