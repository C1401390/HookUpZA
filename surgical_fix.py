#!/usr/bin/env python3
"""
HookUpZA - Surgical Fix Script v3
Fixes:
1. auth.js const API_BASE clash with hookupza.js var API_BASE  
2. admin-dashboard.html / admin-users.html missing hookupza.js
3. handleLogout not defined (needs to be in window scope)
4. All pages properly load hookupza.js BEFORE auth.js

Run from your HookUpZA directory: python3 surgical_fix.py
"""
import os
import re

print("=" * 60)
print("🔧 HookUpZA Surgical Fix v3")
print("=" * 60)

# ================================================================
# FIX 1: auth.js - remove const API_BASE, use var fallback
# ================================================================
print("\n📄 Fixing js/auth.js...")

if os.path.exists('js/auth.js'):
    with open('js/auth.js', 'r') as f:
        content = f.read()
    
    # Remove any const/let API_BASE declaration
    content = re.sub(
        r'const API_BASE = \(window\.location\.hostname[^;]+;\s*\n',
        '', content
    )
    content = re.sub(
        r'let API_BASE = \(window\.location\.hostname[^;]+;\s*\n',
        '', content
    )
    
    # Add safe fallback at the very top (after comments)
    fallback = '''
// API_BASE is set by hookupza.js. This is a safety fallback only.
if (typeof API_BASE === 'undefined') {
    var API_BASE = (window.location.hostname === '127.0.0.1' || 
                    window.location.hostname === 'localhost')
        ? 'http://127.0.0.1:5000' : '';
    window.API_BASE = API_BASE;
}

'''
    # Insert after the opening comment block
    if '/**' in content:
        # After closing */ of first comment block
        content = re.sub(r'(\*\/\s*\n)', r'\1' + fallback, content, count=1)
    else:
        content = fallback + content
    
    with open('js/auth.js', 'w') as f:
        f.write(content)
    print("   ✅ Removed const API_BASE, added var fallback")
else:
    print("   ❌ js/auth.js not found!")

# ================================================================
# FIX 2: hookupza.js - ensure handleLogout is exported
# ================================================================
print("\n📄 Checking js/hookupza.js...")

if os.path.exists('js/hookupza.js'):
    with open('js/hookupza.js', 'r') as f:
        content = f.read()
    
    # Add handleLogout export if missing
    if 'handleLogout' not in content:
        content += '''

// Expose handleLogout globally (some pages call it inline)
window.handleLogout = async function() {
    try {
        await fetch(API_BASE + '/api/logout', { method: 'POST', credentials: 'include' });
    } catch(e) {}
    
    localStorage.removeItem('hookupza_user');
    
    // Update UI
    const loginBtn  = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    const userMenu  = document.getElementById('userMenu');
    const adminLink = document.getElementById('adminDashboardLink');
    if (loginBtn)  loginBtn.style.display  = 'block';
    if (signupBtn) signupBtn.style.display = 'block';
    if (userMenu)  userMenu.style.display  = 'none';
    if (adminLink) adminLink.style.display = 'none';
    
    // Redirect from protected pages
    const protected_ = ['dashboard.html','post-ad.html','my-ads.html',
                         'admin-dashboard.html','edit-ad.html','admin-users.html'];
    const page = window.location.pathname.split('/').pop();
    if (protected_.includes(page)) {
        window.location.href = 'index.html';
    }
};
'''
        with open('js/hookupza.js', 'w') as f:
            f.write(content)
        print("   ✅ Added handleLogout to hookupza.js")
    else:
        print("   ✅ handleLogout already present")
else:
    print("   ❌ js/hookupza.js not found! Create it first.")

# ================================================================
# FIX 3: Add hookupza.js to ALL HTML files that don't have it
# ================================================================

HTML_FILES = [
    'index.html',
    'post-ad.html',
    'dashboard.html',
    'my-ads.html', 
    'edit-ad.html',
    'admin-dashboard.html',
    'admin-users.html',
    'auth-modals.html',
]

# The hookupza.js script tag to inject
HOOKUPZA_SCRIPT = '<script src="js/hookupza.js"></script>'

print("\n📄 Adding hookupza.js to HTML files...")

for filename in HTML_FILES:
    if not os.path.exists(filename):
        print(f"   ⏭️  {filename}: not found")
        continue
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Check if hookupza.js is already there
    if 'hookupza.js' in content:
        print(f"   ✅ {filename}: already has hookupza.js")
        continue
    
    # Strategy: insert before auth.js if present
    if 'js/auth.js' in content:
        content = content.replace(
            '<script src="js/auth.js"',
            f'{HOOKUPZA_SCRIPT}\n  <script src="js/auth.js"'
        )
        print(f"   ✅ {filename}: added hookupza.js before auth.js")
    
    # If no auth.js but has bootstrap JS, add after bootstrap
    elif 'bootstrap.bundle.min.js' in content:
        content = content.replace(
            'bootstrap.bundle.min.js"></script>',
            'bootstrap.bundle.min.js"></script>\n  ' + HOOKUPZA_SCRIPT
        )
        print(f"   ✅ {filename}: added hookupza.js after bootstrap")
    
    # Last resort: add before </body>
    elif '</body>' in content:
        content = content.replace(
            '</body>',
            f'  {HOOKUPZA_SCRIPT}\n</body>'
        )
        print(f"   ✅ {filename}: added hookupza.js before </body>")
    else:
        print(f"   ⚠️  {filename}: couldn't find injection point")
        continue
    
    if content != original:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

# ================================================================
# FIX 4: Fix inline API_BASE usage in HTML pages
# For pages like admin-dashboard.html that use API_BASE inline
# but master_fix.py may have missed
# ================================================================

print("\n📄 Fixing inline API_BASE in HTML script blocks...")

INLINE_PAGES = [
    'admin-dashboard.html',
    'admin-users.html', 
    'dashboard.html',
    'my-ads.html',
    'edit-ad.html',
]

for filename in INLINE_PAGES:
    if not os.path.exists(filename):
        continue
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Remove any inline const/var API_BASE declarations (hookupza.js handles it)
    content = re.sub(
        r'\s*(const|var|let)\s+API_BASE\s*=\s*\(window\.location[^;]+;\s*\n',
        '\n', content
    )
    content = re.sub(
        r"\s*(const|var|let)\s+API_BASE\s*=\s*['\"]http://127[^;]+;\s*\n",
        '\n', content  
    )
    content = re.sub(
        r"\s*(const|var|let)\s+API_BASE\s*=\s*['\"]['\"];\s*\n",
        '\n', content
    )
    
    # Fix fetch('http://127.0.0.1:5000/api/...') → fetch(`${API_BASE}/api/...`)
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
    
    # Fix single-quoted ${API_BASE} (not a template literal) → backtick
    content = re.sub(r"'(\$\{API_BASE\}/[^']*)'", r"`\1`", content)
    content = re.sub(r'"(\$\{API_BASE\}/[^"]*)"', r"`\1`", content)
    
    if content != original:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ {filename}: fixed inline API calls")
    else:
        print(f"   ✅ {filename}: no inline fixes needed")

# ================================================================
# DONE
# ================================================================
print()
print("=" * 60)
print("✅ All fixes applied!")
print()
print("Test locally first:")
print("   python3 app.py")
print("   # Open http://127.0.0.1:5000")
print()
print("Then deploy:")
print("   git add .")
print('   git commit -m "Fix: API_BASE scope, hookupza.js on all pages"')
print("   git push")
print("=" * 60)
