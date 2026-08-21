# config/settings.py
import os
import json
from pathlib import Path

class VaultKeeperSettings:
    """Centralized settings management for VaultKeeper"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.vaultkeeper'
        self.config_file = self.config_dir / 'settings.json'
        self.default_settings = {
            'security': {
                'auto_lock_timeout': 900,  # 15 minutes in seconds
                'clipboard_clear_timeout': 30,  # 30 seconds
                'clipboard_clear_enabled': True,
                'auto_lock_enabled': True,
                'password_strength_requirement': 4,  # 1-5 scale
                'enable_audit_logging': True,
                'session_timeout': 3600  # 1 hour
            },
            'ui': {
                'theme': 'dark',
                'window_size': '1000x700',
                'auto_save_window_position': True,
                'show_password_strength': True,
                'confirm_deletions': True
            },
            'biometric': {
                'enable_touch_id': False,
                'touch_id_for_unlock': True,
                'touch_id_for_critical_operations': False,
                'biometric_timeout': 30
            },
            'backup': {
                'auto_backup_enabled': True,
                'backup_frequency_days': 7,
                'max_backup_files': 5,
                'backup_location': str(Path.home() / 'VaultKeeper_Backups')
            },
            'advanced': {
                'encryption_algorithm': 'AES-256',
                'key_derivation_iterations': 100000,
                'memory_protection': True,
                'secure_delete': True
            }
        }
        self.settings = self.load_settings()
    
    def ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(exist_ok=True)
    
    def load_settings(self):
        """Load settings from file or create defaults"""
        self.ensure_config_dir()
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                # Merge with defaults to handle new settings
                return self._merge_settings(self.default_settings, loaded_settings)
            except (json.JSONDecodeError, IOError):
                return self.default_settings.copy()
        else:
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save current settings to file"""
        self.ensure_config_dir()
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except IOError:
            return False
    
    def _merge_settings(self, default, loaded):
        """Merge loaded settings with defaults"""
        for key, value in default.items():
            if key not in loaded:
                loaded[key] = value
            elif isinstance(value, dict) and isinstance(loaded[key], dict):
                loaded[key] = self._merge_settings(value, loaded[key])
        return loaded
    
    def get(self, category, key, default=None):
        """Get a specific setting value"""
        return self.settings.get(category, {}).get(key, default)
    
    def set(self, category, key, value):
        """Set a specific setting value"""
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
        self.save_settings()
    
    def get_all(self, category):
        """Get all settings in a category"""
        return self.settings.get(category, {})
    
    def reset_to_defaults(self, category=None):
        """Reset settings to defaults"""
        if category:
            self.settings[category] = self.default_settings[category].copy()
        else:
            self.settings = self.default_settings.copy()
        self.save_settings()

# Global settings instance
settings = VaultKeeperSettings()
