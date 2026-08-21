# advanced/database_advanced.py
import sqlite3
import json
from datetime import datetime, timedelta
import os
import time

from advanced.encryption_advanced import ZeroKnowledgeEncryption

# Database file name
DB_NAME = "vaultkeeper_advanced.db"
_audit_encryption_key = None


def set_audit_encryption_key(vault_key):
    """Keep the audit-log key only for the unlocked process session."""
    global _audit_encryption_key
    _audit_encryption_key = vault_key

def get_db_path():
    """Get the full path to the database file"""
    return os.path.join(os.path.dirname(__file__), '..', DB_NAME)

def init_advanced_db():
    """Initialize the advanced database with all required tables"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Enhanced user table with biometric support
    c.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            master_password_hash TEXT NOT NULL,
            salt BLOB NOT NULL,
            vault_key BLOB NOT NULL,
            biometric_enabled BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            login_attempts INTEGER DEFAULT 0
        )
    """)

    # Enhanced credentials table with TOTP and metadata
    c.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY,
            site TEXT NOT NULL,
            username TEXT,
            password BLOB NOT NULL,
            notes BLOB,
            totp_secret BLOB,
            tags TEXT,
            favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            password_strength INTEGER DEFAULT 0
        )
    """)
    
    # Secure shares table for one-time password sharing
    c.execute("""
        CREATE TABLE IF NOT EXISTS secure_shares (
            id INTEGER PRIMARY KEY,
            share_id TEXT UNIQUE NOT NULL,
            encrypted_data BLOB NOT NULL,
            encryption_key BLOB NOT NULL,
            expiry_time TIMESTAMP NOT NULL,
            max_views INTEGER DEFAULT 1,
            view_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            share_type TEXT DEFAULT 'password'
        )
    """)
    
    # Audit log table for security monitoring
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            success BOOLEAN DEFAULT TRUE,
            details TEXT
        )
    """)

    # Additive migrations keep existing user vaults and audit entries readable.
    user_columns = {row[1] for row in c.execute("PRAGMA table_info(user)")}
    if "login_locked_until" not in user_columns:
        c.execute("ALTER TABLE user ADD COLUMN login_locked_until REAL")
    audit_columns = {row[1] for row in c.execute("PRAGMA table_info(audit_log)")}
    if "encrypted_entry" not in audit_columns:
        c.execute("ALTER TABLE audit_log ADD COLUMN encrypted_entry BLOB")
    
    # Password history table for tracking password changes
    c.execute("""
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY,
            credential_id INTEGER,
            old_password BLOB NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (credential_id) REFERENCES credentials (id)
        )
    """)
    
    # Settings table for application configuration
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# User Management Functions
def save_user_advanced(master_hash, salt, encrypted_vault_key, biometric_enabled=False):
    """Save user data to advanced database"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        INSERT INTO user (master_password_hash, salt, vault_key, biometric_enabled) 
        VALUES (?, ?, ?, ?)
    """, (master_hash, salt, encrypted_vault_key, biometric_enabled))
    conn.commit()
    conn.close()

def get_user_advanced():
    """Get user data from advanced database"""
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT master_password_hash, salt, vault_key, biometric_enabled FROM user LIMIT 1")
        user = c.fetchone()
        conn.close()
        return user
    except sqlite3.Error:
        return None

def update_user_login(success=True):
    """Update user login timestamp and attempts"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    if success:
        c.execute("""
            UPDATE user SET last_login = CURRENT_TIMESTAMP, login_attempts = 0,
            login_locked_until = NULL WHERE id = 1
        """)
    else:
        record_login_failure(conn, c)
    
    conn.commit()
    conn.close()


def get_login_delay_seconds():
    """Return the remaining persisted exponential login delay."""
    conn = sqlite3.connect(get_db_path())
    row = conn.execute("SELECT login_locked_until FROM user WHERE id = 1").fetchone()
    conn.close()
    if not row or row[0] is None:
        return 0
    return max(0, int(row[0] - time.time() + 0.999))


def record_login_failure(conn=None, cursor=None):
    """Record a failure and delay the next try (1, 2, 4 ... seconds, max 5 min)."""
    owns_connection = conn is None
    if owns_connection:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
    cursor.execute("SELECT login_attempts FROM user WHERE id = 1")
    row = cursor.fetchone()
    attempts = (row[0] if row else 0) + 1
    delay = min(300, 2 ** min(attempts - 1, 8))
    cursor.execute(
        "UPDATE user SET login_attempts = ?, login_locked_until = ? WHERE id = 1",
        (attempts, time.time() + delay),
    )
    if owns_connection:
        conn.commit()
        conn.close()
    return delay


def update_encrypted_vault_key(encrypted_vault_key):
    """Persist an upgraded Argon2id/AES-GCM vault-key wrapper."""
    conn = sqlite3.connect(get_db_path())
    conn.execute("UPDATE user SET vault_key = ? WHERE id = 1", (encrypted_vault_key,))
    conn.commit()
    conn.close()


def update_master_password_data(master_hash, salt, encrypted_vault_key):
    """Atomically replace the password verifier and wrapped vault key."""
    conn = sqlite3.connect(get_db_path())
    conn.execute(
        "UPDATE user SET master_password_hash = ?, salt = ?, vault_key = ? WHERE id = 1",
        (master_hash, salt, encrypted_vault_key),
    )
    conn.commit()
    conn.close()

def enable_biometric_for_user():
    """Enable biometric authentication for user"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE user SET biometric_enabled = TRUE WHERE id = 1")
    conn.commit()
    conn.close()

def set_biometric_for_user(enabled):
    """Synchronize the UI preference with native Keychain setup state."""
    conn = sqlite3.connect(get_db_path())
    conn.execute("UPDATE user SET biometric_enabled = ? WHERE id = 1", (bool(enabled),))
    conn.commit()
    conn.close()

# Credential Management Functions
def add_credential_advanced(site, username, encrypted_password, notes=None, 
                          encrypted_totp_secret=None, tags=None, password_strength=0):
    """Add a new credential with advanced features"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    tags_json = json.dumps(tags) if tags else None
    
    c.execute("""
        INSERT INTO credentials 
        (site, username, password, notes, totp_secret, tags, password_strength) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (site, username, encrypted_password, notes,
          encrypted_totp_secret, tags_json, password_strength))
    
    credential_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # Log the action
    log_audit_action("CREATE", "credential", credential_id, success=True, 
                    details=f"Added credential for {site}")
    
    return credential_id

def get_credentials_advanced():
    """Get all credentials with metadata"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT id, site, username, password, notes, totp_secret, tags, 
               favorite, created_at, updated_at, last_used, password_strength
        FROM credentials 
        ORDER BY favorite DESC, last_used DESC, site ASC
    """)
    credentials = c.fetchall()
    conn.close()
    return credentials

def update_credential_advanced(credential_id, site=None, username=None, 
                             encrypted_password=None, notes=None, 
                             encrypted_totp_secret=None, tags=None):
    """Update an existing credential"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Build dynamic update query
    updates = []
    params = []
    
    if site is not None:
        updates.append("site = ?")
        params.append(site)
    if username is not None:
        updates.append("username = ?")
        params.append(username)
    if encrypted_password is not None:
        updates.append("password = ?")
        params.append(encrypted_password)
    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)
    if encrypted_totp_secret is not None:
        updates.append("totp_secret = ?")
        params.append(encrypted_totp_secret)
    if tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(tags) if tags else None)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(credential_id)
        
        query = f"UPDATE credentials SET {', '.join(updates)} WHERE id = ?"
        c.execute(query, params)
        conn.commit()
        
        # Log the action
        log_audit_action("UPDATE", "credential", credential_id, success=True,
                        details=f"Updated credential {credential_id}")
    
    conn.close()

def delete_credential_advanced(credential_id):
    """Delete a credential and log the action"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get credential info before deletion
    c.execute("SELECT site FROM credentials WHERE id = ?", (credential_id,))
    result = c.fetchone()
    
    if result:
        site = result[0]
        c.execute("DELETE FROM credentials WHERE id = ?", (credential_id,))
        conn.commit()
        
        # Log the action
        log_audit_action("DELETE", "credential", credential_id, success=True,
                        details=f"Deleted credential for {site}")
        conn.close()
        return True
    
    conn.close()
    return False

def mark_credential_used(credential_id):
    """Mark a credential as recently used"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE credentials SET last_used = CURRENT_TIMESTAMP WHERE id = ?", 
              (credential_id,))
    conn.commit()
    conn.close()

def toggle_credential_favorite(credential_id):
    """Toggle favorite status of a credential"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        UPDATE credentials 
        SET favorite = NOT favorite 
        WHERE id = ?
    """, (credential_id,))
    conn.commit()
    conn.close()

# Secure Sharing Functions
def create_secure_share(share_id, encrypted_data, encryption_key, expiry_hours=24, 
                       max_views=1, share_type='password'):
    """Create a secure share entry"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    expiry_time = datetime.now() + timedelta(hours=expiry_hours)
    
    c.execute("""
        INSERT INTO secure_shares 
        (share_id, encrypted_data, encryption_key, expiry_time, max_views, share_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (share_id, encrypted_data, encryption_key, expiry_time, max_views, share_type))
    
    conn.commit()
    conn.close()
    
    # Log the action
    log_audit_action("CREATE", "secure_share", None, success=True,
                    details=f"Created secure share {share_id}")

def get_secure_share(share_id):
    """Retrieve and validate a secure share"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""
        SELECT encrypted_data, encryption_key, expiry_time, max_views, view_count, share_type
        FROM secure_shares 
        WHERE share_id = ?
    """, (share_id,))
    
    result = c.fetchone()
    
    if not result:
        conn.close()
        return None, "Share not found"
    
    encrypted_data, encryption_key, expiry_time, max_views, view_count, share_type = result
    
    # Check expiry
    expiry = datetime.fromisoformat(expiry_time)
    if datetime.now() > expiry:
        c.execute("DELETE FROM secure_shares WHERE share_id = ?", (share_id,))
        conn.commit()
        conn.close()
        return None, "Share has expired"
    
    # Check view limit
    if view_count >= max_views:
        c.execute("DELETE FROM secure_shares WHERE share_id = ?", (share_id,))
        conn.commit()
        conn.close()
        return None, "Share view limit exceeded"
    
    # Increment view count
    c.execute("""
        UPDATE secure_shares 
        SET view_count = view_count + 1 
        WHERE share_id = ?
    """, (share_id,))
    
    # Delete if max views reached
    if view_count + 1 >= max_views:
        c.execute("DELETE FROM secure_shares WHERE share_id = ?", (share_id,))
    
    conn.commit()
    conn.close()
    
    # Log the access
    log_audit_action("ACCESS", "secure_share", None, success=True,
                    details=f"Accessed secure share {share_id}")
    
    return {
        'encrypted_data': encrypted_data,
        'encryption_key': encryption_key,
        'remaining_views': max_views - view_count - 1,
        'share_type': share_type
    }, "Success"

def cleanup_expired_shares():
    """Remove expired secure shares"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("DELETE FROM secure_shares WHERE expiry_time < CURRENT_TIMESTAMP")
    deleted_count = c.rowcount
    conn.commit()
    conn.close()
    
    if deleted_count > 0:
        log_audit_action("CLEANUP", "secure_share", None, success=True,
                        details=f"Cleaned up {deleted_count} expired shares")
    
    return deleted_count

# Audit Logging Functions
def log_audit_action(action, resource_type=None, resource_id=None, success=True, 
                    details=None, ip_address=None, user_agent=None):
    """Log encrypted audit data while the vault is unlocked.

    Locked-state events intentionally are not written in plaintext.  SQLite's
    timestamp is retained solely for ordering; all meaningful event metadata is
    sealed with the active vault key.
    """
    if _audit_encryption_key is None:
        return False
    entry = json.dumps({
        "action": action, "resource_type": resource_type, "resource_id": resource_id,
        "success": bool(success), "details": details, "ip_address": ip_address,
        "user_agent": user_agent,
    }, separators=(",", ":")).encode()
    encrypted_entry = ZeroKnowledgeEncryption().encrypt_data(entry, _audit_encryption_key, b"vaultkeeper-audit-v1")
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO audit_log 
        (action, resource_type, resource_id, success, details, ip_address, user_agent, encrypted_entry)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("ENCRYPTED", None, None, True, None, None, None, encrypted_entry))
    
    conn.commit()
    conn.close()
    return True

def get_audit_logs(limit=100, action_filter=None):
    """Decrypt audit logs for the active vault session."""
    if _audit_encryption_key is None:
        return []
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("SELECT timestamp, encrypted_entry FROM audit_log WHERE encrypted_entry IS NOT NULL ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    encryption = ZeroKnowledgeEncryption()
    logs = []
    for timestamp, encrypted_entry in rows:
        try:
            entry = json.loads(encryption.decrypt_data(encrypted_entry, _audit_encryption_key, b"vaultkeeper-audit-v1"))
        except Exception:
            continue
        if not action_filter or entry["action"] == action_filter:
            logs.append((entry["action"], entry["resource_type"], entry["resource_id"], timestamp, entry["success"], entry["details"]))
    return logs


def encrypt_legacy_audit_logs():
    """Seal pre-upgrade audit entries once their vault is unlocked."""
    if _audit_encryption_key is None:
        return 0
    conn = sqlite3.connect(get_db_path())
    rows = conn.execute("""
        SELECT id, action, resource_type, resource_id, success, details, ip_address, user_agent
        FROM audit_log WHERE encrypted_entry IS NULL
    """).fetchall()
    encryption = ZeroKnowledgeEncryption()
    for row in rows:
        entry = json.dumps({
            "action": row[1], "resource_type": row[2], "resource_id": row[3],
            "success": bool(row[4]), "details": row[5], "ip_address": row[6],
            "user_agent": row[7],
        }, separators=(",", ":")).encode()
        encrypted = encryption.encrypt_data(entry, _audit_encryption_key, b"vaultkeeper-audit-v1")
        conn.execute("""
            UPDATE audit_log SET action = 'ENCRYPTED', resource_type = NULL,
            resource_id = NULL, success = TRUE, details = NULL, ip_address = NULL,
            user_agent = NULL, encrypted_entry = ? WHERE id = ?
        """, (encrypted, row[0]))
    conn.commit()
    conn.close()
    return len(rows)

# Password History Functions
def save_password_history(credential_id, old_encrypted_password):
    """Save old password to history before updating"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO password_history (credential_id, old_password)
        VALUES (?, ?)
    """, (credential_id, old_encrypted_password))
    
    conn.commit()
    conn.close()

def get_password_history(credential_id, limit=10):
    """Get password history for a credential"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""
        SELECT old_password, changed_at
        FROM password_history 
        WHERE credential_id = ?
        ORDER BY changed_at DESC
        LIMIT ?
    """, (credential_id, limit))
    
    history = c.fetchall()
    conn.close()
    return history

# Settings Functions
def save_setting(key, value):
    """Save or update a setting"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (key, value))
    
    conn.commit()
    conn.close()

def get_setting(key, default_value=None):
    """Get a setting value"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    
    return result[0] if result else default_value

def get_all_settings():
    """Get all settings as a dictionary"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("SELECT key, value FROM settings")
    results = c.fetchall()
    conn.close()
    
    return dict(results)

# Database Maintenance Functions
def vacuum_database():
    """Optimize database performance"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("VACUUM")
    conn.close()
    
    log_audit_action("VACUUM", "database", None, success=True,
                    details="Database optimized")

def get_database_stats():
    """Get database statistics"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    stats = {}
    
    # Count records in each table
    tables = ['user', 'credentials', 'secure_shares', 'audit_log', 'password_history', 'settings']
    
    for table in tables:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        stats[f"{table}_count"] = c.fetchone()[0]
    
    # Database file size
    stats['database_size'] = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    conn.close()
    return stats

# Initialize database on import
if __name__ == "__main__":
    init_advanced_db()
    print("Advanced database initialized successfully!")
