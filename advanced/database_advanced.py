# advanced/database_advanced.py
import sqlite3
import json
from datetime import datetime, timedelta
import os

# Database file name
DB_NAME = "vaultkeeper_advanced.db"

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
            UPDATE user SET 
            last_login = CURRENT_TIMESTAMP, 
            login_attempts = 0 
            WHERE id = 1
        """)
    else:
        c.execute("UPDATE user SET login_attempts = login_attempts + 1 WHERE id = 1")
    
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

# Credential Management Functions
def add_credential_advanced(site, username, encrypted_password, notes=None, 
                          encrypted_totp_secret=None, tags=None, password_strength=0):
    """Add a new credential with advanced features"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    encrypted_notes = notes.encode() if notes else None
    tags_json = json.dumps(tags) if tags else None
    
    c.execute("""
        INSERT INTO credentials 
        (site, username, password, notes, totp_secret, tags, password_strength) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (site, username, encrypted_password, encrypted_notes, 
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
        params.append(notes.encode() if notes else None)
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
    """Log an audit action"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO audit_log 
        (action, resource_type, resource_id, success, details, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (action, resource_type, resource_id, success, details, ip_address, user_agent))
    
    conn.commit()
    conn.close()

def get_audit_logs(limit=100, action_filter=None):
    """Get recent audit logs"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    if action_filter:
        c.execute("""
            SELECT action, resource_type, resource_id, timestamp, success, details
            FROM audit_log 
            WHERE action = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (action_filter, limit))
    else:
        c.execute("""
            SELECT action, resource_type, resource_id, timestamp, success, details
            FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
    
    logs = c.fetchall()
    conn.close()
    return logs

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
