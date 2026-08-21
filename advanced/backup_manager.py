"""Encrypted, portable backups for VaultKeeper databases."""

import io
import os
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from advanced.encryption_advanced import ZeroKnowledgeEncryption


class EncryptedBackupManager:
    def __init__(self, vault_key, database_paths):
        self.vault_key = vault_key
        self.database_paths = [Path(path) for path in database_paths]
        self.encryption = ZeroKnowledgeEncryption()

    def create_backup(self, destination):
        """Create an AES-GCM encrypted backup without a plaintext archive on disk."""
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for db_path in self.database_paths:
                if not db_path.exists():
                    continue
                # A SQLite backup creates a consistent snapshot without copying a
                # partially-written database or its WAL files.
                with tempfile.NamedTemporaryFile(suffix=".sqlite") as snapshot:
                    source = sqlite3.connect(db_path)
                    target = sqlite3.connect(snapshot.name)
                    try:
                        source.backup(target)
                    finally:
                        target.close()
                        source.close()
                    bundle.write(snapshot.name, arcname=db_path.name)

        encrypted = self.encryption.encrypt_data(archive.getvalue(), self.vault_key, b"vaultkeeper-backup-v1")
        filename = f"vaultkeeper-{datetime.now().strftime('%Y%m%d-%H%M%S')}.vkbak"
        output = destination / filename
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as backup_file:
            backup_file.write(encrypted)
        return output
