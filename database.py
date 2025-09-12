# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect("vaultkeeper.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            master_password_hash TEXT NOT NULL,
            salt BLOB NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY,
            site TEXT,
            username TEXT,
            password BLOB,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_master_password(master_hash, salt):
    conn = sqlite3.connect("vaultkeeper.db")
    c = conn.cursor()
    c.execute("INSERT INTO user (master_password_hash, salt) VALUES (?, ?)", (master_hash, salt))
    conn.commit()
    conn.close()

def get_user():
    conn = sqlite3.connect("vaultkeeper.db")
    c = conn.cursor()
    c.execute("SELECT master_password_hash, salt FROM user LIMIT 1")
    user = c.fetchone()
    conn.close()
    return user

def add_credential(site, username, password, notes):
    conn = sqlite3.connect("vaultkeeper.db")
    c = conn.cursor()
    c.execute("INSERT INTO credentials (site, username, password, notes) VALUES (?, ?, ?, ?)", (site, username, password, notes))
    conn.commit()
    conn.close()

def get_credentials():
    conn = sqlite3.connect("vaultkeeper.db")
    c = conn.cursor()
    c.execute("SELECT id, site, username, password, notes FROM credentials")
    items = c.fetchall()
    conn.close()
    return items
