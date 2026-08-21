# password_generator.py
import secrets
import string
import re

class AdvancedPasswordGenerator:
    def __init__(self):
        self.lowercase = string.ascii_lowercase
        self.uppercase = string.ascii_uppercase
        self.digits = string.digits
        self.symbols = "!@#$%^&*()-_=+[]{}|;:,.<>?"
        self.ambiguous = "0O1lI"  # Characters to avoid
    
    def generate_password(self, length=16, use_symbols=True, use_numbers=True, 
                         use_uppercase=True, use_lowercase=True, 
                         avoid_ambiguous=True, custom_requirements=None):
        """Generate cryptographically secure password"""
        
        if length < 8:
            raise ValueError("Password length must be at least 8 characters")
        
        charset = ""
        required_chars = []
        
        if use_lowercase:
            chars = self.lowercase
            if avoid_ambiguous:
                chars = ''.join(c for c in chars if c not in self.ambiguous)
            charset += chars
            required_chars.append(secrets.choice(chars))
        
        if use_uppercase:
            chars = self.uppercase
            if avoid_ambiguous:
                chars = ''.join(c for c in chars if c not in self.ambiguous)
            charset += chars
            required_chars.append(secrets.choice(chars))
        
        if use_numbers:
            chars = self.digits
            if avoid_ambiguous:
                chars = ''.join(c for c in chars if c not in self.ambiguous)
            charset += chars
            required_chars.append(secrets.choice(chars))
        
        if use_symbols:
            charset += self.symbols
            required_chars.append(secrets.choice(self.symbols))
        
        if not charset:
            raise ValueError("At least one character type must be selected")
        
        # Generate remaining characters
        remaining_length = length - len(required_chars)
        password_chars = required_chars + [
            secrets.choice(charset) for _ in range(remaining_length)
        ]
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password_chars)
        password = ''.join(password_chars)
        
        return password

    def generate_secure_password(self, length=16, **options):
        """Compatibility name used by the existing UI and tests."""
        aliases = {
            'include_symbols': 'use_symbols',
            'include_numbers': 'use_numbers',
            'include_uppercase': 'use_uppercase',
            'include_lowercase': 'use_lowercase',
            'exclude_ambiguous': 'avoid_ambiguous',
        }
        options = {aliases.get(key, key): value for key, value in options.items()}
        return self.generate_password(length, **options)
    
    def generate_passphrase(self, word_count=4, separator="-", capitalize=True):
        """Generate memorable passphrase"""
        # Simple word list - in production, use a proper word list
        words = [
            "apple", "bridge", "candle", "dragon", "energy", "forest", "guitar",
            "house", "island", "jungle", "kite", "laser", "mountain", "ocean",
            "piano", "queen", "river", "sunset", "tiger", "umbrella", "valley",
            "winter", "xenon", "yellow", "zebra"
        ]
        
        selected_words = [secrets.choice(words) for _ in range(word_count)]
        
        if capitalize:
            selected_words = [word.capitalize() for word in selected_words]
        
        # Add random numbers
        passphrase = separator.join(selected_words) + str(secrets.randbelow(9999))
        return passphrase
    
    def check_password_strength(self, password):
        """Analyze password strength"""
        score = 0
        feedback = []
        
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        else:
            feedback.append("Use at least 8 characters")
        
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Add lowercase letters")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Add uppercase letters")
        
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("Add numbers")
        
        if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            score += 2
        else:
            feedback.append("Add special characters")
        
        strength_levels = {
            0: "Very Weak",
            1: "Weak", 
            2: "Weak",
            3: "Fair",
            4: "Good",
            5: "Good",
            6: "Strong",
            7: "Very Strong"
        }
        
        return {
            'score': score,
            'strength': strength_levels.get(score, "Very Strong"),
            'feedback': feedback
        }
