/**
 * HookUpZA - js/hookupza.js
 * LOAD THIS BEFORE auth.js ON ALL PAGES
 * 
 * Provides: API_BASE, isUserLoggedIn(), getApiUrl(), and common utilities
 */

// ============================================
// GLOBAL API BASE - declared with var to avoid
// "already declared" errors across pages
// ============================================

var API_BASE = (window.location.hostname === '127.0.0.1' || 
                window.location.hostname === 'localhost')
    ? 'http://127.0.0.1:5000'
    : '';

window.API_BASE = API_BASE;
console.log('🔧 API_BASE:', API_BASE || '(relative - production mode)');

// Helper to build full API URL
function getApiUrl(path) {
    return API_BASE + path;
}
window.getApiUrl = getApiUrl;

// ============================================
// SHARED AUTH STATE
// ============================================

var currentUser = null;

async function isUserLoggedIn() {
    try {
        const r = await fetch(API_BASE + '/api/check_auth', { credentials: 'include' });
        if (r.ok) {
            const d = await r.json();
            if (d.logged_in) { currentUser = d; return true; }
        }
    } catch(e) {}
    currentUser = null;
    return false;
}
window.isUserLoggedIn = isUserLoggedIn;
window.getCurrentUser = function() { return currentUser; };
