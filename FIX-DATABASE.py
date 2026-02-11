#!/usr/bin/env python3
"""
HookUpZA Database Fix Script
Run this ONCE to fix your broken database schema.
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = 'hookupza.db'

print("=" * 50)
print("🔧 HookUpZA Database Fix Script")
print("=" * 50)

db = sqlite3.connect(DATABASE)
db.row_factory = sqlite3.Row
cursor = db.cursor()

# ---- STEP 1: Check what we currently have ----
print("\n📊 Checking current database state...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"   Tables found: {[t['name'] for t in tables]}")

if 'users' in [t['name'] for t in tables]:
    cursor.execute('PRAGMA table_info(users)')
    columns = cursor.fetchall()
    print(f"   Users columns: {[c[1] for c in columns]}")
else:
    print("   No users table found")

# ---- STEP 2: Drop and recreate tables ----
print("\n⚠️  Dropping old tables and recreating with correct schema...")
cursor.execute('DROP TABLE IF EXISTS ads')
cursor.execute('DROP TABLE IF EXISTS users')
print("   ✅ Old tables dropped")

# ---- STEP 3: Create correct users table ----
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
print("   ✅ Users table created with correct schema")

# ---- STEP 4: Create correct ads table ----
cursor.execute('''
    CREATE TABLE ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT NOT NULL,
        contact TEXT NOT NULL,
        rate TEXT DEFAULT '',
        photos TEXT DEFAULT '[]',
        services TEXT DEFAULT '[]',
        is_premium INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')
print("   ✅ Ads table created with correct schema")

# ---- STEP 5: Create admin account ----
admin_password = generate_password_hash('admin123')
cursor.execute(
    "INSERT INTO users (username, password, role) VALUES ('admin', ?, 'admin')",
    (admin_password,)
)
print("   ✅ Admin account created (admin / admin123)")

# ---- STEP 6: Create a test user ----
test_password = generate_password_hash('test123')
cursor.execute(
    "INSERT INTO users (username, password, role) VALUES ('test1', ?, 'user')",
    (test_password,)
)
print("   ✅ Test user created (test1 / test123)")

db.commit()
db.close()

print("\n" + "=" * 50)
print("✅ DATABASE FIXED SUCCESSFULLY!")
print("=" * 50)
print("\nAccounts ready:")
print("  🔑 Admin:  username=admin    password=admin123")
print("  👤 User:   username=test1    password=test123")
print("\nNow run: python3 app.py")
print("=" * 50)
