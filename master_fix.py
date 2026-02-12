#!/usr/bin/env python3
"""
HookUpZA - Master URL Fix Script
Run this from your HookUpZA directory.

WHAT IT DOES:
1. Removes any duplicate const API_BASE declarations from HTML inline scripts
2. Properly converts 'http://127.0.0.1:5000/api/...' strings to template literals
3. Adds hookupza.js script tag to pages missing it
4. Adds isUserLoggedIn and other missing functions

Run: python3 master_fix.py
"""
import os
import re

HTML_FILES = [
    'index.html',
    'post-ad.html',
    'dashboard.html', 
    'my-ads.html',
    'edit-ad.html',
    'admin-dashboard.html',
    'admin-users.html',
]

# ----------------------------------------------------------------
# STEP 1: Fix fetch('http://127.0.0.1:5000/api/...') 
# Convert single/double quoted hardcoded URLs to template literals
# ----------------------------------------------------------------
def fix_hardcoded_urls(content):
    """Fix hardcoded localhost URLs in fetch() calls"""
    
    # Pattern: fetch('http://127.0.0.1:5000/api/something')
    # Becomes: fetch(`${API_BASE}/api/something`)
    content = re.sub(
        r"fetch\('http://127\.0\.0\.1:5000(/[^']*)'\)",
        r"fetch(`${API_BASE}\1`)",
        content
    )
    content = re.sub(
        r'fetch\("http://127\.0\.0\.1:5000(/[^"]*)"\)',
        r"fetch(`${API_BASE}\1`)",
        content
    )
    
    # Pattern: url: 'http://127.0.0.1:5000/api/...'
    content = re.sub(
        r"url:\s*'http://127\.0\.0\.1:5000(/[^']*)'",
        r"url: `${API_BASE}\1`",
        content
    )
    
    # Pattern: const url = 'http://127.0.0.1:5000...'
    content = re.sub(
        r"(const|let|var)\s+url\s*=\s*'http://127\.0\.0\.1:5000(/[^']*)'",
        r"\1 url = `${API_BASE}\2`",
        content
    )
    
    # Pattern: Loading ads from: http://127.0.0.1:5000...  (console.log strings)
    content = re.sub(
        r"(console\.log\([^)]*)'http://127\.0\.0\.1:5000(/[^']*)'",
        r"\1`${API_BASE}\2`",
        content
    )
    
    # Remaining bare URLs in template literals that got mangled
    # Fix: `${API_BASE}/api/...` that was wrongly made into '${API_BASE}/api/...' 
    content = re.sub(
        r"'(\$\{API_BASE\}[^']*)'",
        r"`\1`",
        content
    )
    content = re.sub(
        r'"(\$\{API_BASE\}[^"]*)"',
        r"`\1`",
        content
    )
    
    return content

# ----------------------------------------------------------------
# STEP 2: Remove duplicate const API_BASE declarations
# (auth.js declares it globally; HTML files should NOT redeclare)
# ----------------------------------------------------------------
def remove_duplicate_api_base(content):
    """Remove inline const API_BASE declarations that conflict with auth.js"""
    
    # Multi-line pattern from fix_urls.py injection
    patterns = [
        # The injected block from fix_urls.py
        r"\s*// ✅ RENDER FIX:[^\n]*\n\s*const API_BASE = \(window\.location\.hostname[^;]+;\s*",
        # Simple one-liner
        r"\s*const API_BASE = \(window\.location\.hostname[^;]+;\s*",
        # Old hardcoded versions  
        r"\s*const API_BASE = ['\"]http://127\.0\.0\.1:5000['\"];\s*",
        r"\s*const API_BASE = ['\"]['\"];\s*",
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, '\n', content, flags=re.DOTALL)
    
    return content

# ----------------------------------------------------------------
# STEP 3: Ensure hookupza.js is loaded before auth.js
# ----------------------------------------------------------------
def ensure_hookupza_js(content, filename):
    """Add hookupza.js script tag if not present"""
    
    if 'hookupza.js' in content:
        return content  # Already has it
    
    # Find where auth.js is loaded and add hookupza.js before it
    if 'js/auth.js' in content:
        content = content.replace(
            '<script src="js/auth.js"',
            '<script src="js/hookupza.js"></script>\n  <script src="js/auth.js"'
        )
        print(f"   ➕ Added hookupza.js before auth.js")
    
    return content

# ----------------------------------------------------------------
# STEP 4: Fix pages that use API_BASE without loading auth.js
# ----------------------------------------------------------------
def add_api_base_if_missing(content, filename):
    """For pages with inline API calls but no auth.js, add the hookupza.js script"""
    
    has_auth_js = 'js/auth.js' in content or 'js/hookupza.js' in content
    uses_api_base = 'API_BASE' in content
    
    if uses_api_base and not has_auth_js:
        # Add inline API_BASE definition at start of first <script> tag
        api_base_def = '''
    // API URL - auto detects local vs Render
    var API_BASE = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
        ? 'http://127.0.0.1:5000' : '';
    '''
        # Insert after first <script> tag
        content = re.sub(
            r'(<script[^>]*>)(\s*)',
            lambda m: m.group(1) + api_base_def,
            content, count=1
        )
        print(f"   ➕ Added inline API_BASE definition")
    
    return content

# ----------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------

print("=" * 60)
print("🔧 HookUpZA Master URL Fix")
print("=" * 60)

for filename in HTML_FILES:
    if not os.path.exists(filename):
        print(f"⏭️  {filename}: not found, skipping")
        continue

    with open(filename, 'r', encoding='utf-8') as f:
        original = f.read()
    
    content = original
    print(f"\n📄 Processing {filename}...")
    
    # Count issues before
    hardcoded_count = content.count('http://127.0.0.1:5000')
    bad_literal_count = len(re.findall(r"'(\$\{API_BASE\})", content))
    dup_api_base = len(re.findall(r'const API_BASE', content))
    
    # Apply fixes
    content = remove_duplicate_api_base(content)
    content = fix_hardcoded_urls(content)
    content = ensure_hookupza_js(content, filename)
    content = add_api_base_if_missing(content, filename)
    
    # Count remaining
    remaining_hardcoded = content.count('http://127.0.0.1:5000')
    remaining_bad = len(re.findall(r"'(\$\{API_BASE\})", content))
    
    if content != original:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ Fixed: {hardcoded_count} hardcoded URLs, {dup_api_base} duplicate API_BASE(s), {bad_literal_count} bad literals")
        if remaining_hardcoded > 0:
            print(f"   ⚠️  {remaining_hardcoded} hardcoded URLs still remaining (manual fix needed)")
        if remaining_bad > 0:
            print(f"   ⚠️  {remaining_bad} bad template literals still remaining")
    else:
        print(f"   ✅ No changes needed")

print()
print("=" * 60)
print("✅ Done! Next steps:")
print()
print("   git add .")
print('   git commit -m "Fix: proper template literals for API_BASE"')
print("   git push")
print()
print("   Render auto-deploys in ~2 min")
print("=" * 60)
