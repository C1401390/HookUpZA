#!/usr/bin/env python3
"""
HookUpZA - Complete Database Reset Script
Run this to fix ALL database issues in one shot.

Usage:
    python3 reset_db.py
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = 'hookupza.db'

print("=" * 55)
print("🔧 HookUpZA Database Reset")
print("=" * 55)

# Delete old broken database
if os.path.exists(DATABASE):
    os.remove(DATABASE)
    print(f"🗑️  Deleted old {DATABASE}")

# Create fresh database
db = sqlite3.connect(DATABASE)
db.row_factory = sqlite3.Row
c = db.cursor()

# ---- USERS TABLE ----
c.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        age TEXT DEFAULT '25-34',
        location TEXT DEFAULT '',
        email TEXT DEFAULT '',
        account_type TEXT DEFAULT 'free',
        role TEXT DEFAULT 'user',
        vendor_data TEXT,
        vendor_paid INTEGER DEFAULT 0,
        verified INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
print("✅ Users table created")

# ---- ADS TABLE ----
c.execute('''
    CREATE TABLE ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT DEFAULT '',
        description TEXT DEFAULT '',
        services TEXT DEFAULT '[]',
        rate TEXT DEFAULT '',
        contact TEXT DEFAULT '',
        photos TEXT DEFAULT '[]',
        status TEXT DEFAULT 'pending',
        is_premium INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')
print("✅ Ads table created")

# ---- CREATE ADMIN ACCOUNT ----
admin_hash = generate_password_hash('admin123')
c.execute('''
    INSERT INTO users (username, password_hash, age, account_type, role, verified)
    VALUES ('admin', ?, '25-34', 'vendor', 'admin', 1)
''', (admin_hash,))
print("✅ Admin created: admin / admin123")

# ---- CREATE TEST USER ----
test_hash = generate_password_hash('test123')
c.execute('''
    INSERT INTO users (username, password_hash, age, account_type, role, verified)
    VALUES ('test1', ?, '25-34', 'free', 'user', 1)
''', (test_hash,))
print("✅ Test user created: test1 / test123")

# ---- CREATE PREMIUM TEST USER ----
vendor_hash = generate_password_hash('vendor123')
c.execute('''
    INSERT INTO users (username, password_hash, age, account_type, role, verified)
    VALUES ('vendor1', ?, '25-34', 'vendor', 'user', 1)
''', (vendor_hash,))
print("✅ Vendor user created: vendor1 / vendor123")

db.commit()
db.close()

print()
print("=" * 55)
print("✅ DATABASE RESET COMPLETE!")
print("=" * 55)
print()
print("📋 YOUR ACCOUNTS:")
print("   🔑 Admin:  admin    / admin123  (role=admin, vendor)")
print("   👤 User:   test1    / test123   (role=user,  free)")
print("   💎 Vendor: vendor1  / vendor123 (role=user,  vendor)")
print()
print("📌 HOW EACH WORKS:")
print("   admin   → Posts go LIVE immediately, can manage all ads")
print("   vendor1 → Posts go LIVE immediately (premium ads)")
print("   test1   → Posts need approval (free ads, 3 day limit)")
print()
print("🚀 Now run: python3 app.py")
print("=" * 55)
