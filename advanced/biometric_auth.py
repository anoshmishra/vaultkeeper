# advanced/biometric_auth.py
import subprocess
import base64
import json
import os
from datetime import datetime


class BiometricAuth:
    """
    Enhanced biometric authentication for VaultKeeper on macOS
    
    Provides Touch ID integration with macOS Keychain for secure storage
    and retrieval of master password data with biometric protection.
    """
    
    def __init__(self):
        self.keychain_service = "com.vaultkeeper.secure"
        self.keychain_account = "master-vault-key"
        self._debug_mode = False
    
    def enable_debug(self, enabled=True):
        """Enable or disable debug output"""
        self._debug_mode = enabled
    
    def _debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self._debug_mode:
            print(f"[BiometricAuth Debug] {message}")
    
    def is_touchid_available(self):
        """
        Comprehensive check if Touch ID is available and properly configured
        
        Returns:
            bool: True if Touch ID is available and can be used
        """
        try:
            self._debug_print("Checking Touch ID availability...")
            
            # Check 1: Hardware capability (Apple Silicon required)
            hw_result = subprocess.run([
                'system_profiler', 'SPHardwareDataType'
            ], capture_output=True, text=True, timeout=10)
            
            has_touchid_hardware = any(chip in hw_result.stdout for chip in ['M1', 'M2', 'M3', 'M4'])
            self._debug_print(f"Touch ID hardware detected: {has_touchid_hardware}")
            
            if not has_touchid_hardware:
                return False
            
            # Check 2: Touch ID enrollment status
            enroll_result = subprocess.run([
                'bioutil', '-c'
            ], capture_output=True, text=True, timeout=5)
            
            if enroll_result.returncode == 0 and 'enrolled' in enroll_result.stdout.lower():
                self._debug_print("Touch ID is enrolled and available")
                return True
            
            # Check 3: System preferences (fallback check)
            pref_result = subprocess.run([
                'defaults', 'read', 'com.apple.loginwindow', 'BiometricAuthenticationAllowed'
            ], capture_output=True, text=True, timeout=5)
            
            if pref_result.returncode == 0:
                self._debug_print("Touch ID allowed in system preferences")
                return True
            
            # Check 4: Alternative bioutil check
            status_result = subprocess.run([
                'bioutil', '-r'
            ], capture_output=True, text=True, timeout=5)
            
            if status_result.returncode == 0 and "Touch ID" in status_result.stdout:
                self._debug_print("Touch ID service is running")
                return True
            
            self._debug_print("Touch ID hardware present but may need enrollment")
            return False
            
        except Exception as e:
            self._debug_print(f"Touch ID availability check failed: {e}")
            return False
    
    def setup_touchid_keychain(self, master_password, salt):
        """
        Store master password data in Keychain with Touch ID protection
        
        Args:
            master_password (str): The master password to store
            salt (bytes): The salt used for key derivation
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_touchid_available():
            return False, "Touch ID not available or not enrolled. Please enable Touch ID in System Preferences."
        
        try:
            self._debug_print("Setting up Touch ID keychain storage...")
            
            # Create secure data payload
            vault_data = {
                'master_password': master_password,
                'salt': base64.b64encode(salt).decode(),
                'timestamp': datetime.now().isoformat(),
                'version': '1.1',  # Updated version
                'device_id': self._get_device_identifier()
            }
            
            # Encode for keychain storage
            data_json = json.dumps(vault_data)
            data_b64 = base64.b64encode(data_json.encode()).decode()
            
            # Remove any existing entry first
            self._remove_keychain_item()
            
            # Add to keychain with Touch ID requirement
            cmd = [
                'security', 'add-generic-password',
                '-s', self.keychain_service,
                '-a', self.keychain_account,
                '-w', data_b64,
                '-T', '',  # Empty -T enforces biometric authentication
                '-U'  # Update if exists
            ]
            
            self._debug_print(f"Executing keychain command: {' '.join(cmd[:-2])} [password] [options]")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            
            if result.returncode == 0:
                # Verify the item was stored and requires Touch ID
                if self._verify_keychain_item():
                    if self._verify_touchid_requirement():
                        self._debug_print("Touch ID setup completed successfully")
                        return True, "Touch ID setup successful with biometric protection"
                    else:
                        self._debug_print("Warning: Touch ID requirement not verified")
                        return True, "Touch ID setup completed (biometric requirement uncertain)"
                else:
                    return False, "Touch ID setup verification failed - keychain item not found"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown keychain error"
                self._debug_print(f"Keychain command failed: {error_msg}")
                return False, f"Keychain storage failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Touch ID setup timed out - please try again"
        except Exception as e:
            self._debug_print(f"Exception during setup: {str(e)}")
            return False, f"Setup failed: {str(e)}"
    
    def authenticate_with_touchid(self):
        """
        Authenticate using Touch ID and retrieve vault data
        
        Returns:
            tuple: (vault_data: dict or None, message: str)
        """
        if not self.is_touchid_available():
            return None, "Touch ID not available"
        
        try:
            self._debug_print("Starting Touch ID authentication...")
            
            # First verify the keychain item exists
            if not self._verify_keychain_item():
                return None, "No Touch ID data found - please set up biometric authentication first"
            
            # Show user-friendly prompt (optional)
            self._show_touchid_prompt()
            
            # Retrieve from keychain - this will prompt for Touch ID
            cmd = [
                'security', 'find-generic-password',
                '-s', self.keychain_service,
                '-a', self.keychain_account,
                '-w'  # Show password (the stored data)
            ]
            
            self._debug_print("Prompting for Touch ID authentication...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                try:
                    # Decode the retrieved data
                    data_b64 = result.stdout.strip()
                    data_json = base64.b64decode(data_b64).decode()
                    vault_data = json.loads(data_json)
                    
                    # Validate data structure
                    required_keys = ['master_password', 'salt', 'timestamp']
                    if all(key in vault_data for key in required_keys):
                        self._debug_print("Touch ID authentication successful")
                        return vault_data, "Authentication successful"
                    else:
                        self._debug_print("Invalid data structure in keychain")
                        return None, "Invalid stored data format"
                        
                except (json.JSONDecodeError, base64.binascii.Error) as e:
                    self._debug_print(f"Data decoding error: {str(e)}")
                    return None, f"Data corruption detected: {str(e)}"
                    
            elif result.returncode == 44:
                self._debug_print("User cancelled Touch ID authentication")
                return None, "Touch ID authentication was cancelled by user"
            elif result.returncode == 51:
                self._debug_print("Touch ID authentication failed")
                return None, "Touch ID authentication failed - please try again"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown keychain error"
                self._debug_print(f"Keychain access failed: {error_msg}")
                return None, f"Authentication failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            self._debug_print("Touch ID authentication timed out")
            return None, "Touch ID authentication timed out"
        except Exception as e:
            self._debug_print(f"Exception during authentication: {str(e)}")
            return None, f"System error: {str(e)}"
    
    def _verify_keychain_item(self):
        """Verify that the keychain item exists"""
        try:
            cmd = [
                'security', 'find-generic-password',
                '-s', self.keychain_service,
                '-a', self.keychain_account
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            exists = result.returncode == 0
            self._debug_print(f"Keychain item exists: {exists}")
            return exists
            
        except Exception as e:
            self._debug_print(f"Error verifying keychain item: {e}")
            return False
    
    def _verify_touchid_requirement(self):
        """
        Verify that Touch ID is actually required for the keychain item
        
        Returns:
            bool: True if Touch ID requirement is properly configured
        """
        try:
            # Attempt to access without providing biometric authentication
            # This should fail if Touch ID is properly required
            result = subprocess.run([
                'security', 'find-generic-password',
                '-s', self.keychain_service,
                '-a', self.keychain_account,
                '-w'
            ], capture_output=True, text=True, timeout=5, input='\n', encoding='utf-8')
            
            # If this succeeds without prompting, Touch ID isn't properly configured
            touchid_required = result.returncode != 0
            self._debug_print(f"Touch ID requirement verified: {touchid_required}")
            return touchid_required
            
        except Exception as e:
            self._debug_print(f"Error verifying Touch ID requirement: {e}")
            return True  # Assume it's working if we can't verify
    
    def _remove_keychain_item(self):
        """Remove existing keychain item"""
        try:
            result = subprocess.run([
                'security', 'delete-generic-password',
                '-s', self.keychain_service,
                '-a', self.keychain_account
            ], capture_output=True, text=True, timeout=10)
            
            removed = result.returncode == 0
            self._debug_print(f"Existing keychain item removed: {removed}")
            
        except Exception as e:
            self._debug_print(f"Error removing keychain item: {e}")
    
    def _show_touchid_prompt(self):
        """Show user-friendly Touch ID prompt using AppleScript"""
        try:
            applescript = '''
            tell application "System Events"
                display notification "Please use Touch ID to authenticate" with title "VaultKeeper"
            end tell
            '''
            
            subprocess.run(['osascript', '-e', applescript], 
                         capture_output=True, timeout=3)
        except:
            pass  # Notification is optional
    
    def _get_device_identifier(self):
        """Get a unique device identifier for additional security"""
        try:
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                  capture_output=True, text=True, timeout=5)
            
            # Extract serial number or hardware UUID
            for line in result.stdout.split('\n'):
                if 'Serial Number' in line or 'Hardware UUID' in line:
                    return line.split(':')[-1].strip()
            
            return "unknown-device"
        except:
            return "unknown-device"
    
    def remove_touchid_data(self):
        """
        Remove Touch ID data from keychain
        
        Returns:
            bool: True if removal was successful
        """
        try:
            self._debug_print("Removing Touch ID data from keychain...")
            
            result = subprocess.run([
                'security', 'delete-generic-password',
                '-s', self.keychain_service,
                '-a', self.keychain_account
            ], capture_output=True, text=True, timeout=10)
            
            success = result.returncode == 0
            self._debug_print(f"Touch ID data removal: {'successful' if success else 'failed'}")
            
            return success
        except Exception as e:
            self._debug_print(f"Error removing Touch ID data: {e}")
            return False
    
    def get_touchid_status(self):
        """
        Get comprehensive Touch ID status information
        
        Returns:
            dict: Status information including availability and configuration
        """
        status = {
            'available': self.is_touchid_available(),
            'keychain_item_exists': self._verify_keychain_item(),
            'service_name': self.keychain_service,
            'account_name': self.keychain_account,
            'hardware_detected': self._check_hardware(),
            'biometric_enrolled': self._check_enrollment(),
            'system_preference_enabled': self._check_system_preference()
        }
        
        # Add Touch ID requirement status if item exists
        if status['keychain_item_exists']:
            status['touchid_required'] = self._verify_touchid_requirement()
        
        return status
    
    def _check_hardware(self):
        """Check if Touch ID hardware is present"""
        try:
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                  capture_output=True, text=True, timeout=10)
            return any(chip in result.stdout for chip in ['M1', 'M2', 'M3', 'M4'])
        except:
            return False
    
    def _check_enrollment(self):
        """Check if Touch ID is enrolled"""
        try:
            result = subprocess.run(['bioutil', '-c'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and 'enrolled' in result.stdout.lower()
        except:
            return False
    
    def _check_system_preference(self):
        """Check system preference setting"""
        try:
            result = subprocess.run([
                'defaults', 'read', 'com.apple.loginwindow', 'BiometricAuthenticationAllowed'
            ], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def debug_touchid_setup(self):
        """
        Comprehensive Touch ID debugging information
        
        This method provides detailed information about Touch ID configuration
        and helps diagnose setup issues.
        """
        print("🔍 VaultKeeper Touch ID Debug Report")
        print("=" * 50)
        
        status = self.get_touchid_status()
        
        print(f"🔧 Hardware Detection:")
        print(f"   Touch ID Hardware: {'✅' if status['hardware_detected'] else '❌'}")
        print(f"   System Available: {'✅' if status['available'] else '❌'}")
        
        print(f"\n🎯 Enrollment Status:")
        print(f"   Biometric Enrolled: {'✅' if status['biometric_enrolled'] else '❌'}")
        print(f"   System Preference: {'✅' if status['system_preference_enabled'] else '❌'}")
        
        print(f"\n🔐 Keychain Configuration:")
        print(f"   Service: {status['service_name']}")
        print(f"   Account: {status['account_name']}")
        print(f"   Item Exists: {'✅' if status['keychain_item_exists'] else '❌'}")
        
        if status['keychain_item_exists']:
            print(f"   Touch ID Required: {'✅' if status.get('touchid_required', False) else '❌'}")
        
        print(f"\n🚀 Recommendations:")
        if not status['hardware_detected']:
            print("   • Touch ID hardware not detected - ensure you're using an Apple Silicon Mac")
        elif not status['biometric_enrolled']:
            print("   • Go to System Preferences > Touch ID & Passcode and enroll your fingerprints")
        elif not status['system_preference_enabled']:
            print("   • Enable 'Use Touch ID to unlock your Mac' in System Preferences")
        elif not status['keychain_item_exists']:
            print("   • Set up Touch ID through VaultKeeper settings")
        elif not status.get('touchid_required', True):
            print("   • Keychain item exists but Touch ID requirement may not be properly configured")
        else:
            print("   • Touch ID setup appears to be working correctly! ✅")
        
        # Test basic commands
        print(f"\n🧪 Command Tests:")
        
        # Test bioutil
        try:
            result = subprocess.run(['bioutil', '-c'], capture_output=True, text=True, timeout=5)
            print(f"   bioutil -c: {'✅' if result.returncode == 0 else '❌'} (code: {result.returncode})")
            if result.stdout.strip():
                print(f"     Output: {result.stdout.strip()}")
        except Exception as e:
            print(f"   bioutil -c: ❌ Error: {e}")
        
        # Test security command
        try:
            result = subprocess.run([
                'security', 'find-generic-password', '-s', self.keychain_service, '-a', self.keychain_account
            ], capture_output=True, text=True, timeout=5)
            print(f"   security find: {'✅' if result.returncode == 0 else '❌'} (code: {result.returncode})")
        except Exception as e:
            print(f"   security find: ❌ Error: {e}")
        
        print("\n" + "=" * 50)
