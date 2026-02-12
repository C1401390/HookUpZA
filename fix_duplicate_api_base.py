#!/usr/bin/env python3
"""
HookUpZA - Fix Duplicate API_BASE Script
Removes the injected API_BASE from HTML files since auth.js already declares it globally.
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
]

# The snippet that was wrongly injected by fix_urls.py
BAD_SNIPPET_PATTERNS = [
    # Pattern from fix_urls.py injection
    r"\n\s*// ✅ RENDER FIX: Auto-detects local vs production\s*\n\s*const API_BASE = \(window\.location\.hostname.*?\n.*?'http://127\.0\.0\.1:5000' : '';\s*\n",
    # Any standalone const API_BASE declaration in a script block  
    r"const API_BASE = \(window\.location\.hostname[^;]+;\s*\n",
    # Old style
    r"const API_BASE = 'http://127\.0\.0\.1:5000';\s*\n",
    r'const API_BASE = "http://127\.0\.0\.1:5000";\s*\n',
]

print("=" * 55)
print("🔧 Fix Duplicate API_BASE Declarations")
print("=" * 55)

total_fixed = 0

for filename in FILES_TO_FIX:
    if not os.path.exists(filename):
        print(f"⏭️  Skipping {filename} (not found)")
        continue

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # Remove bad injected snippets
    for pattern in BAD_SNIPPET_PATTERNS:
        content = re.sub(pattern, '\n', content, flags=re.DOTALL)
    
    if content != original_content:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        total_fixed += 1
        print(f"✅ {filename}: Removed duplicate API_BASE declaration")
    else:
        # Check if API_BASE is declared inline
        count = content.count('const API_BASE')
        if count > 0:
            print(f"⚠️  {filename}: Found {count} API_BASE declaration(s) — manual check needed")
        else:
            print(f"✅ {filename}: No duplicate found")

print()
print("=" * 55)
print(f"Fixed {total_fixed} files")
print()
print("API_BASE is declared ONCE in js/auth.js and exposed via:")
print("  window.API_BASE = API_BASE;")
print()
print("All HTML files should use: API_BASE (from auth.js global)")
print("NOT declare their own const API_BASE")
print("=" * 55)
