"""Native macOS Touch ID storage backed by Keychain access controls.

The Keychain item contains only the randomly generated vault key.  The master
password is never persisted for biometric unlock.
"""

import threading


class BiometricAuth:
    keychain_service = "com.vaultkeeper.secure"
    keychain_account = "vault-key"
    _MISSING_ENTITLEMENT = -34018

    def __init__(self):
        self._debug_mode = False
        self._native = None
        self._native_loaded = False

    @staticmethod
    def _load_native_frameworks():
        try:
            from Foundation import NSData
            from LocalAuthentication import LAContext, LAPolicyDeviceOwnerAuthenticationWithBiometrics
            from Security import (
                SecAccessControlCreateWithFlags, SecItemAdd, SecItemCopyMatching, SecItemDelete,
                errSecSuccess, errSecItemNotFound, kSecAttrAccessControl,
                kSecAttrAccessibleWhenUnlockedThisDeviceOnly, kSecAttrAccount, kSecAttrService,
                kSecClass, kSecClassGenericPassword, kSecMatchLimit, kSecMatchLimitOne,
                kSecReturnData, kSecUseAuthenticationContext, kSecValueData,
                kSecAccessControlBiometryCurrentSet,
            )
            return locals()
        except ImportError:
            return None

    def _frameworks(self):
        """Load optional macOS bridges only when Touch ID is actually used."""
        if not self._native_loaded:
            self._native = self._load_native_frameworks()
            self._native_loaded = True
        return self._native

    def enable_debug(self, enabled=True):
        self._debug_mode = enabled

    def _debug_print(self, message):
        if self._debug_mode:
            print(f"[BiometricAuth] {message}")

    def _evaluate_touchid(self, reason):
        native = self._frameworks()
        if not native:
            return None, "Native macOS authentication support is not installed"
        context = native["LAContext"].alloc().init()
        policy = native["LAPolicyDeviceOwnerAuthenticationWithBiometrics"]
        available, error = context.canEvaluatePolicy_error_(policy, None)
        if not available:
            return None, f"Touch ID is unavailable: {error}" if error else "Touch ID is unavailable"

        complete = threading.Event()
        result = {"success": False, "error": None}

        def reply(success, error):
            result["success"] = bool(success)
            result["error"] = error
            complete.set()

        context.evaluatePolicy_localizedReason_reply_(policy, reason, reply)
        if not complete.wait(30):
            return None, "Touch ID authentication timed out"
        if not result["success"]:
            return None, "Touch ID authentication was cancelled or failed"
        return context, "Authentication successful"

    def is_touchid_available(self):
        native = self._frameworks()
        if not native:
            return False
        context = native["LAContext"].alloc().init()
        available, _ = context.canEvaluatePolicy_error_(
            native["LAPolicyDeviceOwnerAuthenticationWithBiometrics"], None
        )
        return bool(available)

    def _query(self):
        native = self._frameworks()
        return {
            native["kSecClass"]: native["kSecClassGenericPassword"],
            native["kSecAttrService"]: self.keychain_service,
            native["kSecAttrAccount"]: self.keychain_account,
        }

    @staticmethod
    def _status_code(result):
        """Normalize PyObjC's status-only and (status, value) return forms."""
        return result[0] if isinstance(result, tuple) else result

    def _keychain_error(self, result):
        status = self._status_code(result)
        if status == self._MISSING_ENTITLEMENT:
            return (
                "Touch ID requires VaultKeeper to run as a signed macOS .app "
                "with a Keychain Access Groups entitlement. It cannot be enabled "
                "from an unsigned Python script."
            )
        return f"Keychain storage failed (status {status})"

    def setup_secure_enclave_vault_key(self, vault_key):
        """Store a vault key protected by the current enrolled biometrics.

        The Secure Enclave enforces the Keychain access-control policy.  A
        changed biometric enrollment invalidates the item automatically.
        """
        native = self._frameworks()
        if not native:
            return False, "Install PyObjC LocalAuthentication and Security frameworks to use Touch ID"
        context, message = self._evaluate_touchid("Enable Touch ID for VaultKeeper")
        if context is None:
            return False, message
        access, error = native["SecAccessControlCreateWithFlags"](
            None,
            native["kSecAttrAccessibleWhenUnlockedThisDeviceOnly"],
            native["kSecAccessControlBiometryCurrentSet"],
            None,
        )
        if access is None:
            return False, f"Unable to configure Keychain access control: {error}"
        self.remove_touchid_data()
        query = self._query()
        query.update({
            native["kSecAttrAccessControl"]: access,
            native["kSecValueData"]: native["NSData"].dataWithBytes_length_(vault_key, len(vault_key)),
            native["kSecUseAuthenticationContext"]: context,
        })
        status = self._status_code(native["SecItemAdd"](query, None))
        if status != native["errSecSuccess"]:
            return False, self._keychain_error(status)
        return True, "Touch ID enabled with Secure Enclave-protected Keychain access"

    def authenticate_with_touchid(self):
        native = self._frameworks()
        if not native:
            return None, "Native macOS authentication support is not installed"
        context, message = self._evaluate_touchid("Unlock VaultKeeper")
        if context is None:
            return None, message
        query = self._query()
        query.update({
            native["kSecReturnData"]: True,
            native["kSecMatchLimit"]: native["kSecMatchLimitOne"],
            native["kSecUseAuthenticationContext"]: context,
        })
        result = native["SecItemCopyMatching"](query, None)
        status, data = result if isinstance(result, tuple) else (result, None)
        if status != native["errSecSuccess"]:
            return None, "No Touch ID vault key is configured" if status == native["errSecItemNotFound"] else f"Keychain access failed (status {status})"
        return {"vault_key": bytes(data)}, "Authentication successful"

    def remove_touchid_data(self):
        native = self._frameworks()
        if not native:
            return False
        status = self._status_code(native["SecItemDelete"](self._query()))
        return status in (native["errSecSuccess"], native["errSecItemNotFound"])

    def get_touchid_status(self):
        configured = False
        native = self._frameworks()
        if native:
            result = native["SecItemCopyMatching"](self._query(), None)
            status = self._status_code(result)
            configured = status == native["errSecSuccess"]
        return {
            "available": self.is_touchid_available(),
            "keychain_item_exists": configured,
            "secure_enclave_protected": configured,
            "service_name": self.keychain_service,
            "account_name": self.keychain_account,
        }

    # Old callers passed a master password and salt.  Reject that unsafe API so
    # no future code can put the master password in Keychain.
    def setup_touchid_keychain(self, _master_password, _salt):
        return False, "Touch ID setup requires the vault key; master passwords are never stored in Keychain"
