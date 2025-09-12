# tests/test_password_gen.py
import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from advanced.password_generator import AdvancedPasswordGenerator

class TestPasswordGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = AdvancedPasswordGenerator()
    
    def test_password_generation(self):
        """Test basic password generation"""
        password = self.generator.generate_secure_password(16)
        self.assertEqual(len(password), 16)
        self.assertIsInstance(password, str)
    
    def test_password_strength(self):
        """Test password strength checking"""
        weak_password = "123"
        strong_password = "MySecureP@ssw0rd2025!"
        
        weak_result = self.generator.check_password_strength(weak_password)
        strong_result = self.generator.check_password_strength(strong_password)
        
        self.assertIn('strength', weak_result)
        self.assertIn('strength', strong_result)
        self.assertGreater(strong_result['score'], weak_result['score'])

if __name__ == '__main__':
    unittest.main()
