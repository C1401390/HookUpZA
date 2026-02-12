/**
 * HookUpZA - js/auth.js  (COMPLETE FIXED VERSION)
 * 
 * KEY FIXES:
 * - API_BASE declared ONCE here, exposed via window.API_BASE
 * - selectAccountType() defined here (called from index.html)
 * - Correct form field IDs matching index.html
 * - No duplicate declarations
 */

// ============================================
// API URL - AUTO DETECTS LOCAL vs RENDER
// ============================================
const API_BASE = (window.location.hostname === '127.0.0.1' || 
                  window.location.hostname === 'localhost')
    ? 'http://127.0.0.1:5000'
    : '';   // Empty string = relative URL (same server on Render)

// Expose globally so inline scripts in HTML can use it
window.API_BASE = API_BASE;

console.log(`🔧 API_BASE set to: "${API_BASE || '(relative - Render mode)'}"`);

// ============================================
// ACCOUNT TYPE SELECTOR (called from index.html onclick)
// ============================================

function selectAccountType(type) {
    const freeCard = document.getElementById('freeAccountCard');
    const vendorCard = document.getElementById('vendorAccountCard');
    const vendorFields = document.getElementById('vendorFields');
    const freeRadio = document.getElementById('freeAccount');
    const vendorRadio = document.getElementById('vendorAccount');

    if (type === 'vendor') {
        if (freeCard) freeCard.classList.remove('border-success');
        if (vendorCard) vendorCard.classList.add('border-warning');
        if (vendorFields) vendorFields.classList.remove('d-none');
        if (vendorRadio) vendorRadio.checked = true;
    } else {
        if (vendorCard) vendorCard.classList.remove('border-warning');
        if (freeCard) freeCard.classList.add('border-success');
        if (vendorFields) vendorFields.classList.add('d-none');
        if (freeRadio) freeRadio.checked = true;
    }
}
window.selectAccountType = selectAccountType;

// ============================================
// PASSWORD TOGGLE (called from index.html)
// ============================================

function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    field.type = field.type === 'password' ? 'text' : 'password';
}
window.togglePassword = togglePassword;

// ============================================
// AUTH CHECK ON PAGE LOAD
// ============================================

async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/check_auth`, { 
            credentials: 'include' 
        });
        if (response.ok) {
            const data = await response.json();
            if (data.logged_in) {
                updateUIForLoggedInUser(data);
                return data;
            }
        }
    } catch (err) {
        console.log('Auth check: not logged in');
    }
    updateUIForLoggedOutUser();
    return null;
}
window.checkAuthStatus = checkAuthStatus;

function updateUIForLoggedInUser(data) {
    const username = data.username || data.user_data?.username;
    const role = data.role || data.user_data?.role || 'user';

    const loginBtn   = document.getElementById('loginBtn');
    const signupBtn  = document.getElementById('signupBtn');
    const userMenu   = document.getElementById('userMenu');
    const userDisplay = document.getElementById('usernameDisplay');
    const adminLink  = document.getElementById('adminDashboardLink');

    if (loginBtn)   loginBtn.style.display   = 'none';
    if (signupBtn)  signupBtn.style.display   = 'none';
    if (userMenu)   userMenu.style.display    = 'block';
    if (userDisplay) userDisplay.textContent  = username;
    if (adminLink)  adminLink.style.display   = (role === 'admin') ? 'block' : 'none';

    localStorage.setItem('hookupza_user', JSON.stringify({ username, role }));
}

function updateUIForLoggedOutUser() {
    const loginBtn  = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    const userMenu  = document.getElementById('userMenu');
    const adminLink = document.getElementById('adminDashboardLink');

    if (loginBtn)  loginBtn.style.display  = 'block';
    if (signupBtn) signupBtn.style.display = 'block';
    if (userMenu)  userMenu.style.display  = 'none';
    if (adminLink) adminLink.style.display = 'none';

    localStorage.removeItem('hookupza_user');
}

// ============================================
// ADMIN CHECK
// ============================================

async function checkAdminStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/check_role`, { 
            credentials: 'include' 
        });
        if (response.ok) {
            const data = await response.json();
            const adminLink = document.getElementById('adminDashboardLink');
            if (adminLink) adminLink.style.display = data.is_admin ? 'block' : 'none';
            return data.is_admin;
        }
    } catch (err) { /* not admin */ }
    return false;
}
window.checkAdminStatus = checkAdminStatus;

// ============================================
// LOGIN
// ============================================

async function handleLogin(username, password) {
    try {
        const response = await fetch(`${API_BASE}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (response.ok) {
            showAuthMsg(`✅ Welcome back, ${data.username}!`, 'success');
            updateUIForLoggedInUser(data);
            setTimeout(closeAllModals, 500);
            return { success: true, data };
        } else {
            showAuthMsg(`❌ ${data.error || 'Invalid credentials'}`, 'danger');
            console.log('[AUTH ERROR]', data.error);
            return { success: false, error: data.error };
        }
    } catch (err) {
        showAuthMsg('❌ Network error. Check your connection.', 'danger');
        console.log('[AUTH ERROR]', err.message);
        return { success: false, error: err.message };
    }
}
window.handleLogin = handleLogin;

// ============================================
// SIGNUP
// ============================================

async function handleSignup(formData) {
    try {
        const response = await fetch(`${API_BASE}/api/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(formData)
        });
        const data = await response.json();
        if (response.ok) {
            showAuthMsg(`✅ Welcome, ${data.username}! Account created.`, 'success');
            updateUIForLoggedInUser(data);
            setTimeout(closeAllModals, 500);
            return { success: true, data };
        } else {
            showAuthMsg(`❌ ${data.error || 'Signup failed'}`, 'danger');
            console.log('[AUTH ERROR]', data.error);
            return { success: false, error: data.error };
        }
    } catch (err) {
        showAuthMsg('❌ Network error. Check your connection.', 'danger');
        console.log('[AUTH ERROR]', err.message);
        return { success: false, error: err.message };
    }
}
window.handleSignup = handleSignup;

// ============================================
// LOGOUT
// ============================================

async function handleLogout() {
    try {
        await fetch(`${API_BASE}/api/logout`, { method: 'POST', credentials: 'include' });
    } catch (err) { /* ignore */ }
    updateUIForLoggedOutUser();

    const protectedPages = ['dashboard.html','post-ad.html','my-ads.html',
                            'admin-dashboard.html','edit-ad.html','admin-users.html'];
    const page = window.location.pathname.split('/').pop();
    if (protectedPages.includes(page)) {
        window.location.href = 'index.html';
    }
}
window.handleLogout = handleLogout;

// ============================================
// FORM EVENT LISTENERS (DOMContentLoaded)
// ============================================

document.addEventListener('DOMContentLoaded', function() {

    // LOGIN FORM
    const loginForm = document.getElementById('loginForm');
    if (loginForm && !loginForm._bound) {
        loginForm._bound = true;
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('loginUsername')?.value?.trim();
            const password = document.getElementById('loginPassword')?.value;
            if (!username || !password) {
                showAuthMsg('Please enter username and password', 'danger');
                return;
            }
            const btn = this.querySelector('[type="submit"]');
            setBtn(btn, true, 'Logging in...');
            await handleLogin(username, password);
            setBtn(btn, false, 'Login');
        });
    }

    // SIGNUP FORM
    // Note: index.html uses id="username", id="password", id="age"
    const signupForm = document.getElementById('signupForm');
    if (signupForm && !signupForm._bound) {
        signupForm._bound = true;
        signupForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            // Support both naming conventions
            const username    = (document.getElementById('signupUsername') || document.getElementById('username'))?.value?.trim();
            const password    = (document.getElementById('signupPassword') || document.getElementById('password'))?.value;
            const age         = (document.getElementById('signupAge')      || document.getElementById('age'))?.value;
            const location    = (document.getElementById('signupLocation') || document.getElementById('location'))?.value?.trim() || '';
            const email       = (document.getElementById('signupEmail')    || document.getElementById('email'))?.value?.trim() || '';
            const accountType = document.querySelector('input[name="accountType"]:checked')?.value || 'free';

            if (!username || !password || !age) {
                showAuthMsg('Please fill in all required fields (username, password, age)', 'danger');
                return;
            }
            if (password.length < 8) {
                showAuthMsg('Password must be at least 8 characters', 'danger');
                return;
            }

            // Collect vendor data if vendor type
            let vendorData = null;
            if (accountType === 'vendor') {
                vendorData = {
                    businessName:       document.getElementById('businessName')?.value?.trim(),
                    whatsapp:           document.getElementById('whatsapp')?.value?.trim(),
                    serviceDescription: document.getElementById('serviceDescription')?.value?.trim(),
                };
            }

            const btn = this.querySelector('[type="submit"]');
            setBtn(btn, true, 'Creating account...');
            await handleSignup({ username, password, age, location, email, account_type: accountType, vendor_data: vendorData });
            setBtn(btn, false, 'Create Account');
        });
    }

    // LOGOUT BUTTON
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn && !logoutBtn._bound) {
        logoutBtn._bound = true;
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleLogout();
        });
    }

    // Initial auth check
    checkAuthStatus();
});

// ============================================
// HELPERS
// ============================================

function setBtn(btn, disabled, text) {
    if (!btn) return;
    btn.disabled = disabled;
    btn.innerHTML = disabled 
        ? `<span class="spinner-border spinner-border-sm me-2"></span>${text}`
        : text;
}

function closeAllModals() {
    document.querySelectorAll('.modal.show').forEach(modal => {
        try { bootstrap.Modal.getInstance(modal)?.hide(); } catch(e) {}
    });
}

function showAuthMsg(message, type = 'danger') {
    // Try multiple possible message containers
    const ids = ['authMessage', 'loginMessage', 'signupMessage', 'formMessage'];
    for (const id of ids) {
        const el = document.getElementById(id);
        if (el) {
            el.className = `alert alert-${type} mt-2 py-2`;
            el.textContent = message;
            el.style.display = 'block';
            setTimeout(() => { el.style.display = 'none'; }, 5000);
            return;
        }
    }
    // Bootstrap toast fallback
    const toastEl = document.getElementById('authToast');
    if (toastEl) {
        const body = toastEl.querySelector('.toast-body');
        if (body) body.textContent = message;
        toastEl.className = `toast align-items-center text-white border-0 bg-${type === 'success' ? 'success' : 'danger'}`;
        try { new bootstrap.Toast(toastEl).show(); } catch(e) {}
        return;
    }
    console.log(`[AUTH ${type.toUpperCase()}] ${message}`);
}
window.showAuthMsg = showAuthMsg;
