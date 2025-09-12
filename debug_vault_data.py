# debug_vault_data.py
import sqlite3
import sys
import os

def check_database_contents():
    """Check what's actually stored in the databases"""
    
    db_files = [
        'vaultkeeper_advanced.db',
        'vaultkeeper_universal.db', 
        'vaultkeeper.db'
    ]
    
    print("🔍 VaultKeeper Database Diagnostic Report")
    print("=" * 60)
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"\n📁 Database: {db_file}")
            print(f"📊 Size: {os.path.getsize(db_file)} bytes")
            
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                print(f"📋 Tables: {len(tables)}")
                
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"   • {table_name}: {count} records")
                    
                    # Show sample data for credentials table
                    if table_name == 'credentials':
                        cursor.execute(f"SELECT id, site, username FROM {table_name} LIMIT 5")
                        samples = cursor.fetchall()
                        for sample in samples:
                            print(f"     - ID: {sample[0]}, Site: {sample[1]}, User: {sample[2]}")
                
                conn.close()
                
            except Exception as e:
                print(f"❌ Error reading {db_file}: {e}")
        else:
            print(f"\n❌ Database file missing: {db_file}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_database_contents()
