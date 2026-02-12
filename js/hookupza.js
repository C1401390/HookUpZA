/**
 * HookUpZA - js/hookupza.js
 * 
 * LOAD THIS AS THE FIRST SCRIPT ON EVERY PAGE (before auth.js)
 * Provides globals: API_BASE, handleLogout, isUserLoggedIn, getApiUrl
 * 
 * Uses 'var' (not const/let) so it can be safely loaded multiple times
 * without "already declared" errors.
 */

// ============================================
// API_BASE - var so it can be re-read safely
// ============================================
var API_BASE = (window.location.hostname === '127.0.0.1' || 
                window.location.hostname === 'localhost')
    ? 'http://127.0.0.1:5000'
    : '';

window.API_BASE = API_BASE;
console.log('🔧 API_BASE:', API_BASE || '(relative - production mode)');

// Helper
function getApiUrl(path) { return API_BASE + path; }
window.getApiUrl = getApiUrl;

// ============================================
// LOGOUT - defined here so ALL pages have it
// (index.html calls onclick="handleLogout()")
// ============================================
window.handleLogout = async function() {
    try {
        await fetch(API_BASE + '/api/logout', { 
            method: 'POST', 
            credentials: 'include' 
        });
    } catch(e) {}

    localStorage.removeItem('hookupza_user');

    // Hide user menu, show login/signup buttons
    ['loginBtn','signupBtn'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'block';
    });
    ['userMenu','adminDashboardLink'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });

    // Redirect away from protected pages
    const protected_ = ['dashboard.html','post-ad.html','my-ads.html',
                         'admin-dashboard.html','edit-ad.html','admin-users.html'];
    const page = window.location.pathname.split('/').pop();
    if (protected_.includes(page)) {
        window.location.href = 'index.html';
    }
};

// ============================================
// isUserLoggedIn - used by dashboard, my-ads etc
// ============================================
var currentUser = null;

window.isUserLoggedIn = async function() {
    try {
        const r = await fetch(API_BASE + '/api/check_auth', { credentials: 'include' });
        if (r.ok) {
            const d = await r.json();
            if (d.logged_in) { 
                currentUser = d;
                return true; 
            }
        }
    } catch(e) {}
    currentUser = null;
    return false;
};

window.getCurrentUser = function() { return currentUser; };

// ============================================
// selectAccountType - called from index.html signup form
// ============================================
window.selectAccountType = function(type) {
    const freeCard   = document.getElementById('freeAccountCard');
    const vendorCard = document.getElementById('vendorAccountCard');
    const vendorFields = document.getElementById('vendorFields');
    const freeRadio  = document.getElementById('freeAccount');
    const vendorRadio = document.getElementById('vendorAccount');

    if (type === 'vendor') {
        if (freeCard)    freeCard.classList.remove('border-success');
        if (vendorCard)  vendorCard.classList.add('border-warning');
        if (vendorFields) vendorFields.classList.remove('d-none');
        if (vendorRadio) vendorRadio.checked = true;
    } else {
        if (vendorCard)  vendorCard.classList.remove('border-warning');
        if (freeCard)    freeCard.classList.add('border-success');
        if (vendorFields) vendorFields.classList.add('d-none');
        if (freeRadio)   freeRadio.checked = true;
    }
};

// ============================================
// togglePassword - called from login/signup forms
// ============================================
window.togglePassword = function(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) field.type = field.type === 'password' ? 'text' : 'password';
};
