#!/usr/bin/env python3
"""
HookUpZA - Fix Hardcoded URLs Script
Replaces all http://127.0.0.1:5000 with the API_BASE pattern
Run this from your HookUpZA directory.
"""
import os
import re

FILES_TO_FIX = [
    'index.html',
    'post-ad.html',
    'dashboard.html',
    'my-ads.html',
    'edit-ad.html',
    'admin-dashboard.html',
    'admin-users.html',
    'auth-modals.html',
]

# The API_BASE JS snippet to inject at the top of each <script> block
API_BASE_SNIPPET = """
    // ✅ RENDER FIX: Auto-detects local vs production
    const API_BASE = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
        ? 'http://127.0.0.1:5000' : '';
"""

print("=" * 55)
print("🔧 HookUpZA URL Fix Script")
print("=" * 55)

total_replacements = 0

for filename in FILES_TO_FIX:
    if not os.path.exists(filename):
        print(f"⏭️  Skipping {filename} (not found)")
        continue

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    count = content.count("http://127.0.0.1:5000")
    
    if count == 0:
        print(f"✅ {filename}: No hardcoded URLs found")
        continue

    # Replace hardcoded URLs with template literal using API_BASE
    # fetch('http://127.0.0.1:5000/api/...') -> fetch(`${API_BASE}/api/...`)
    
    # Pattern 1: 'http://127.0.0.1:5000/api/...' -> `${API_BASE}/api/...`
    content = re.sub(
        r"'http://127\.0\.0\.1:5000(/[^']*)'",
        r'`${API_BASE}\1`',
        content
    )
    
    # Pattern 2: "http://127.0.0.1:5000/api/..." -> `${API_BASE}/api/...`
    content = re.sub(
        r'"http://127\.0\.0\.1:5000(/[^"]*)"',
        r'`${API_BASE}\1`',
        content
    )
    
    # Pattern 3: const API_URL = 'http://...' -> const API_URL = API_BASE
    content = re.sub(
        r"(const|let|var)\s+API_URL\s*=\s*['\"]http://127\.0\.0\.1:5000['\"]",
        r'\1 API_URL = API_BASE',
        content
    )

    # Remaining hardcoded http://127.0.0.1:5000 (bare, not in quotes)
    content = content.replace('http://127.0.0.1:5000', '${API_BASE}')

    new_count = content.count("http://127.0.0.1:5000")
    fixed = count - new_count

    if content != original:
        # Check if API_BASE is already defined in the file
        if 'API_BASE' not in original and '<script>' in content:
            # Inject API_BASE definition after first <script> tag
            content = content.replace('<script>', f'<script>{API_BASE_SNIPPET}', 1)
            print(f"   ➕ Injected API_BASE definition")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        total_replacements += fixed
        print(f"✅ {filename}: Fixed {fixed} hardcoded URLs")
    else:
        print(f"⚠️  {filename}: Found {count} URLs but pattern didn't match — manual fix needed")

print()
print("=" * 55)
if total_replacements > 0:
    print(f"✅ Fixed {total_replacements} hardcoded URLs total!")
    print()
    print("📋 NEXT STEPS:")
    print("   1. Commit and push:")
    print("      git add .")
    print('      git commit -m "Fix: use relative API URLs for Render deployment"')
    print("      git push")
    print("   2. Wait for Render to auto-deploy (~2 min)")
    print("   3. Test at https://hookupza.onrender.com")
else:
    print("ℹ️  No changes made.")
print("=" * 55)
