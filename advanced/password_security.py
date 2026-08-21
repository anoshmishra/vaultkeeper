"""Offline password-health checks and HIBP's k-anonymity lookup."""

import hashlib
import urllib.error
import urllib.request

from advanced.password_generator import AdvancedPasswordGenerator


class PasswordSecurityAnalyzer:
    def __init__(self, encryption, vault_key):
        self.encryption = encryption
        self.vault_key = vault_key
        self.generator = AdvancedPasswordGenerator()

    def analyze_credentials(self, credentials):
        """Return duplicate and weak credential IDs without persisting plaintext."""
        password_groups = {}
        weak = []
        unreadable = []
        for credential in credentials:
            credential_id, site, _, encrypted_password = credential[:4]
            try:
                password = self.encryption.decrypt_data(encrypted_password, self.vault_key).decode("utf-8")
            except Exception:
                unreadable.append(credential_id)
                continue
            fingerprint = hashlib.sha256(password.encode("utf-8")).hexdigest()
            password_groups.setdefault(fingerprint, []).append({"id": credential_id, "site": site})
            if self.generator.check_password_strength(password)["score"] < 4:
                weak.append({"id": credential_id, "site": site})

        return {
            "duplicates": [group for group in password_groups.values() if len(group) > 1],
            "weak": weak,
            "unreadable": unreadable,
        }


def check_hibp_breach(password, timeout=5, opener=urllib.request.urlopen):
    """Check a password with HIBP without transmitting the password or its hash.

    Only the first five characters of an uppercase SHA-1 digest leave the
    device.  HIBP's padding response option reduces prefix-frequency leakage.
    """
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    request = urllib.request.Request(
        f"https://api.pwnedpasswords.com/range/{digest[:5]}",
        headers={"Add-Padding": "true", "User-Agent": "VaultKeeper/1.0"},
    )
    try:
        with opener(request, timeout=timeout) as response:
            lines = response.read().decode("ascii").splitlines()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Password breach service is unavailable") from exc

    suffix = digest[5:]
    for line in lines:
        candidate, separator, count = line.partition(":")
        if separator and candidate == suffix:
            return int(count)
    return 0
