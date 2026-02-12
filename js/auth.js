/**
 * HookUpZA - auth.js
 * ✅ RENDER FIX: API_BASE auto-detects local vs production
 */

// Auto-detect: local dev uses http://127.0.0.1:5000, Render uses relative URLs
const API_BASE = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
    ? 'http://127.0.0.1:5000'
    : '';

// ============================================
// AUTH CHECK
// ============================================

async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/check_auth`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            if (data.logged_in) {
                updateUIForLoggedInUser(data);
                return data;
            }
        }
    } catch (err) { /* not logged in */ }
    updateUIForLoggedOutUser();
    return null;
}

function updateUIForLoggedInUser(data) {
    const username = data.username || data.user_data?.username;
    const role = data.role || data.user_data?.role || 'user';

    const loginBtn = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    const userMenu = document.getElementById('userMenu');
    const usernameDisplay = document.getElementById('usernameDisplay');
    const adminDashboardLink = document.getElementById('adminDashboardLink');

    if (loginBtn) loginBtn.style.display = 'none';
    if (signupBtn) signupBtn.style.display = 'none';
    if (userMenu) userMenu.style.display = 'block';
    if (usernameDisplay) usernameDisplay.textContent = username;
    if (adminDashboardLink) adminDashboardLink.style.display = (role === 'admin') ? 'block' : 'none';

    localStorage.setItem('hookupza_user', JSON.stringify({ username, role }));
}

function updateUIForLoggedOutUser() {
    const loginBtn = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    const userMenu = document.getElementById('userMenu');
    const adminDashboardLink = document.getElementById('adminDashboardLink');

    if (loginBtn) loginBtn.style.display = 'block';
    if (signupBtn) signupBtn.style.display = 'block';
    if (userMenu) userMenu.style.display = 'none';
    if (adminDashboardLink) adminDashboardLink.style.display = 'none';

    localStorage.removeItem('hookupza_user');
}

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
            showAuthMessage(`✅ Welcome, ${data.username}! Account created.`, 'success');
            updateUIForLoggedInUser(data);
            closeAllModals();
            return { success: true, data };
        } else {
            showAuthMessage(`❌ ${data.error || 'Signup failed'}`, 'error');
            return { success: false, error: data.error };
        }
    } catch (err) {
        showAuthMessage('❌ Network error. Check your connection.', 'error');
        return { success: false, error: err.message };
    }
}

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
            showAuthMessage(`✅ Welcome back, ${data.username}!`, 'success');
            updateUIForLoggedInUser(data);
            closeAllModals();
            return { success: true, data };
        } else {
            showAuthMessage(`❌ ${data.error || 'Login failed'}`, 'error');
            return { success: false, error: data.error };
        }
    } catch (err) {
        showAuthMessage('❌ Network error. Check your connection.', 'error');
        return { success: false, error: err.message };
    }
}

// ============================================
// LOGOUT
// ============================================

async function handleLogout() {
    try {
        await fetch(`${API_BASE}/api/logout`, { method: 'POST', credentials: 'include' });
    } catch (err) { /* ignore */ }

    updateUIForLoggedOutUser();
    showAuthMessage('✅ Logged out successfully', 'success');

    const protectedPages = ['dashboard.html', 'post-ad.html', 'my-ads.html', 'admin-dashboard.html', 'edit-ad.html'];
    const currentPage = window.location.pathname.split('/').pop();
    if (protectedPages.includes(currentPage)) {
        setTimeout(() => { window.location.href = 'index.html'; }, 1000);
    }
}

// ============================================
// ADMIN CHECK
// ============================================

async function checkAdminStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/check_role`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            const adminLink = document.getElementById('adminDashboardLink');
            if (adminLink) adminLink.style.display = data.is_admin ? 'block' : 'none';
            return data.is_admin;
        }
    } catch (err) { /* not admin */ }
    return false;
}

// ============================================
// FORM HANDLERS
// ============================================

document.addEventListener('DOMContentLoaded', function() {

    // LOGIN FORM - single event listener, no duplicates
    const loginForm = document.getElementById('loginForm');
    if (loginForm && !loginForm.dataset.bound) {
        loginForm.dataset.bound = 'true';
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('loginUsername')?.value?.trim();
            const password = document.getElementById('loginPassword')?.value;
            if (!username || !password) {
                showAuthMessage('Please enter username and password', 'error');
                return;
            }
            const btn = this.querySelector('[type="submit"]');
            if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Logging in...'; }
            await handleLogin(username, password);
            if (btn) { btn.disabled = false; btn.innerHTML = 'Login'; }
        });
    }

    // SIGNUP FORM - single event listener
    const signupForm = document.getElementById('signupForm');
    if (signupForm && !signupForm.dataset.bound) {
        signupForm.dataset.bound = 'true';
        signupForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('signupUsername')?.value?.trim();
            const password = document.getElementById('signupPassword')?.value;
            const age = document.getElementById('signupAge')?.value;
            const accountType = document.querySelector('input[name="accountType"]:checked')?.value || 'free';

            if (!username || !password || !age) {
                showAuthMessage('Please fill in all required fields', 'error');
                return;
            }
            if (password.length < 8) {
                showAuthMessage('Password must be at least 8 characters', 'error');
                return;
            }

            let vendorData = null;
            if (accountType === 'vendor') {
                vendorData = {
                    businessName: document.getElementById('businessName')?.value?.trim(),
                    whatsapp: document.getElementById('whatsapp')?.value?.trim(),
                    serviceDescription: document.getElementById('serviceDescription')?.value?.trim(),
                };
            }

            const btn = this.querySelector('[type="submit"]');
            if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating account...'; }

            await handleSignup({
                username, password, age,
                account_type: accountType,
                location: document.getElementById('signupLocation')?.value?.trim() || '',
                email: document.getElementById('signupEmail')?.value?.trim() || '',
                vendor_data: vendorData
            });

            if (btn) { btn.disabled = false; btn.innerHTML = 'Create Account'; }
        });
    }

    // LOGOUT BUTTON
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn && !logoutBtn.dataset.bound) {
        logoutBtn.dataset.bound = 'true';
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleLogout();
        });
    }

    // Run auth check
    checkAuthStatus();
});

// ============================================
// HELPERS
// ============================================

function closeAllModals() {
    document.querySelectorAll('.modal.show').forEach(modal => {
        const instance = bootstrap.Modal.getInstance(modal);
        if (instance) instance.hide();
    });
}

function showAuthMessage(message, type = 'info') {
    // Try inline message divs first
    const selectors = ['#authMessage', '#loginMessage', '#signupMessage', '#authToast .toast-body'];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el) {
            el.textContent = message;
            const parent = sel.includes('toast') ? el.closest('.toast') : el;
            if (parent) {
                parent.className = `alert ${type === 'success' ? 'alert-success' : 'alert-danger'} mt-2`;
                parent.style.display = 'block';
                setTimeout(() => { parent.style.display = 'none'; }, 4000);
            }
            return;
        }
    }
    console.log(`[AUTH ${type.toUpperCase()}] ${message}`);
}

// Expose globally
window.API_BASE = API_BASE;
window.checkAuthStatus = checkAuthStatus;
window.checkAdminStatus = checkAdminStatus;
window.handleLogin = handleLogin;
window.handleSignup = handleSignup;
window.handleLogout = handleLogout;
window.showAuthMessage = showAuthMessage;
