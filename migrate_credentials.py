#!/usr/bin/env python3
# migrate_credentials.py
import sqlite3
import sys
import os
from datetime import datetime

def migrate_credentials():
    """Migrate credentials from legacy database to advanced database"""
    
    print("🔄 VaultKeeper Credentials Migration Tool")
    print("=" * 50)
    
    # Check if databases exist
    if not os.path.exists('vaultkeeper.db'):
        print("❌ Legacy database (vaultkeeper.db) not found")
        return False
    
    if not os.path.exists('vaultkeeper_advanced.db'):
        print("❌ Advanced database (vaultkeeper_advanced.db) not found")
        return False
    
    try:
        # Connect to both databases
        legacy_conn = sqlite3.connect('vaultkeeper.db')
        advanced_conn = sqlite3.connect('vaultkeeper_advanced.db')
        
        legacy_cursor = legacy_conn.cursor()
        advanced_cursor = advanced_conn.cursor()
        
        # Get credentials from legacy database
        legacy_cursor.execute("SELECT * FROM credentials")
        legacy_creds = legacy_cursor.fetchall()
        
        print(f"📊 Found {len(legacy_creds)} credentials in legacy database")
        
        if not legacy_creds:
            print("⚠️  No credentials found in legacy database")
            return False
        
        # Check current credentials in advanced database
        advanced_cursor.execute("SELECT COUNT(*) FROM credentials")
        current_count = advanced_cursor.fetchone()[0]
        print(f"📊 Current credentials in advanced database: {current_count}")
        
        # Get the structure of both tables
        legacy_cursor.execute("PRAGMA table_info(credentials)")
        legacy_columns = [col[1] for col in legacy_cursor.fetchall()]
        print(f"🏗️  Legacy columns: {legacy_columns}")
        
        advanced_cursor.execute("PRAGMA table_info(credentials)")
        advanced_columns = [col[1] for col in advanced_cursor.fetchall()]
        print(f"🏗️  Advanced columns: {advanced_columns}")
        
        # Migrate each credential
        migrated_count = 0
        
        for cred in legacy_creds:
            try:
                # Extract basic fields (adjust based on your schema)
                if len(cred) >= 4:
                    cred_id, site, username, password = cred[:4]
                    
                    # Skip if site and username are empty
                    if not site and not username:
                        print(f"⚠️  Skipping empty credential (ID: {cred_id})")
                        continue
                    
                    # Insert into advanced database with proper structure
                    advanced_cursor.execute("""
                        INSERT INTO credentials 
                        (site, username, password, encrypted_notes, encrypted_totp, 
                         tags, favorite, created_at, updated_at, password_strength)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        site or 'Unknown Site',
                        username or 'Unknown User', 
                        password,
                        None,  # encrypted_notes
                        None,  # encrypted_totp
                        None,  # tags
                        0,     # favorite
                        datetime.now().isoformat(),  # created_at
                        datetime.now().isoformat(),  # updated_at
                        0      # password_strength
                    ))
                    
                    migrated_count += 1
                    print(f"✅ Migrated: {site or 'Unknown Site'}")
                
            except Exception as e:
                print(f"❌ Error migrating credential {cred_id}: {e}")
                continue
        
        # Commit changes
        advanced_conn.commit()
        
        print(f"\n🎉 Migration Complete!")
        print(f"✅ Successfully migrated {migrated_count} credentials")
        print(f"📊 Total credentials in advanced database: {current_count + migrated_count}")
        
        # Close connections
        legacy_conn.close()
        advanced_conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_credentials()
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. Restart VaultKeeper")
        print("2. Login with your master password")
        print("3. Check if your credentials now appear")
        print("4. If successful, you can archive the legacy database")
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Check that both database files exist")
        print("2. Ensure VaultKeeper is not running")
        print("3. Verify file permissions")

