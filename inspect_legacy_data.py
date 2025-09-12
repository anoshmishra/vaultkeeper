#!/usr/bin/env python3
import sqlite3

def inspect_legacy_data():
    conn = sqlite3.connect('vaultkeeper.db')
    cursor = conn.cursor()
    
    # Get table structure
    cursor.execute("PRAGMA table_info(credentials)")
    columns = cursor.fetchall()
    print("📋 Legacy Database Structure:")
    for col in columns:
        print(f"   • {col[1]} ({col[2]})")
    
    # Get all credentials with details
    cursor.execute("SELECT * FROM credentials")
    creds = cursor.fetchall()
    
    print(f"\n🔐 Found {len(creds)} credentials:")
    for i, cred in enumerate(creds, 1):
        print(f"\n📝 Credential {i}:")
        for j, value in enumerate(cred):
            col_name = columns[j][1] if j < len(columns) else f"col_{j}"
            if isinstance(value, bytes):
                print(f"   {col_name}: [encrypted data - {len(value)} bytes]")
            else:
                print(f"   {col_name}: {value}")
    
    conn.close()

if __name__ == "__main__":
    inspect_legacy_data()
