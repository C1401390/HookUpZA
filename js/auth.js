// ============================================
// SHARED AUTHENTICATION SYSTEM
// Works with Flask backend at http://127.0.0.1:5000
// ============================================

const API_BASE = 'http://127.0.0.1:5000/api';

// ============================================
// SESSION MANAGEMENT
// ============================================

function isUserLoggedIn() {
  return localStorage.getItem('hookupza_user') !== null;
}

function getCurrentUser() {
  const userData = localStorage.getItem('hookupza_user');
  return userData ? JSON.parse(userData) : null;
}

function saveUserSession(userData) {
  localStorage.setItem('hookupza_user', JSON.stringify(userData));
  updateNavbar();
}

function logoutUser() {
  // Call backend to clear session
  fetch(`${API_BASE}/logout`, {
    method: 'POST',
    credentials: 'include'
  })
  .then(() => {
    localStorage.removeItem('hookupza_user');
    updateNavbar();
    window.location.href = 'index.html';
  })
  .catch(err => {
    console.error('Logout error:', err);
    // Logout locally anyway
    localStorage.removeItem('hookupza_user');
    window.location.href = 'index.html';
  });
}

// ============================================
// NAVBAR UPDATES
// ============================================

function updateNavbar() {
  const navAuthButtons = document.querySelector('.navbar-nav.gap-3');
  
  if (!navAuthButtons) return;
  
  if (isUserLoggedIn()) {
    const user = getCurrentUser();
    navAuthButtons.innerHTML = `
      <li class="nav-item dropdown">
        <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false" id="userDropdown">
          <i class="bi bi-person-circle me-1"></i>${user.username}
          ${user.account_type === 'vendor' ? '<span class="badge bg-warning text-dark ms-1">PRO</span>' : ''}
        </a>
        <ul class="dropdown-menu dropdown-menu-end bg-dark border-danger">
          <li><a class="dropdown-item text-light" href="dashboard.html">
            <i class="bi bi-speedometer2 me-2"></i>Dashboard
          </a></li>
          <li><a class="dropdown-item text-light" href="my-ads.html">
            <i class="bi bi-megaphone me-2"></i>My Ads
          </a></li>
          <li><a class="dropdown-item text-light" href="messages.html">
            <i class="bi bi-chat-dots me-2"></i>Messages
          </a></li>
          <li><a class="dropdown-item text-light" href="profile.html">
            <i class="bi bi-gear me-2"></i>Settings
          </a></li>
          <li><hr class="dropdown-divider border-secondary"></li>
          <li><a class="dropdown-item text-danger" href="#" onclick="logoutUser(); return false;">
            <i class="bi bi-box-arrow-right me-2"></i>Logout
          </a></li>
        </ul>
      </li>
    `;
    
    // CRITICAL: Reinitialize Bootstrap dropdown after DOM update
    setTimeout(() => {
      const dropdownElementList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'));
      dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
      });
    }, 100);
    
  } else {
    navAuthButtons.innerHTML = `
      <li class="nav-item">
        <a class="nav-link" href="#" data-bs-toggle="modal" data-bs-target="#loginModal">
          <i class="bi bi-box-arrow-in-right me-1"></i>Login
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link btn btn-outline-danger px-4" href="#" data-bs-toggle="modal" data-bs-target="#signupModal">
          <i class="bi bi-person-plus me-1"></i>Sign Up
        </a>
      </li>
    `;
  }
}

// ============================================
// POST AD BUTTON LOGIC
// ============================================

function handlePostAdClick(e) {
  if (!isUserLoggedIn()) {
    e.preventDefault();
    const signupModal = new bootstrap.Modal(document.getElementById('signupModal'));
    signupModal.show();
    
    const modalBody = document.querySelector('#signupModal .modal-body');
    const existingAlert = modalBody.querySelector('.post-ad-alert');
    
    if (!existingAlert) {
      const alert = document.createElement('div');
      alert.className = 'alert alert-warning border-warning bg-transparent mb-3 post-ad-alert';
      alert.innerHTML = `
        <h6 class="fw-bold mb-2">
          <i class="bi bi-exclamation-triangle me-2"></i>Sign Up to Post Ads
        </h6>
        <p class="small mb-0">Create a free account to start posting ads instantly!</p>
      `;
      modalBody.insertBefore(alert, modalBody.firstChild);
    }
  }
}

// ============================================
// VENDOR PORTAL BUTTON LOGIC
// ============================================

function handleVendorPortalClick(e) {
  const user = getCurrentUser();
  
  if (!isUserLoggedIn()) {
    e.preventDefault();
    const signupModal = new bootstrap.Modal(document.getElementById('signupModal'));
    signupModal.show();
    
    setTimeout(() => {
      selectAccountType('vendor');
    }, 300);
    
  } else if (user.account_type !== 'vendor') {
    e.preventDefault();
    if (confirm('Upgrade to Vendor Premium for R299/month?\n\n✓ Featured ads\n✓ Priority listings\n✓ Photo galleries\n✓ Analytics dashboard')) {
      window.location.href = 'upgrade-to-vendor.html';
    }
  }
}

// ============================================
// ACCOUNT TYPE SELECTION
// ============================================

function selectAccountType(type) {
  const freeCard = document.getElementById('freeAccountCard');
  const vendorCard = document.getElementById('vendorAccountCard');
  const vendorFields = document.getElementById('vendorFields');
  const signupBtn = document.getElementById('signupBtn');
  
  if (!freeCard || !vendorCard) return;
  
  if (type === 'free') {
    freeCard.classList.add('border-success', 'bg-dark');
    freeCard.classList.remove('border-secondary');
    vendorCard.classList.remove('border-warning', 'bg-dark');
    vendorCard.classList.add('border-secondary');
    if (vendorFields) vendorFields.classList.add('d-none');
    document.getElementById('freeAccount').checked = true;
    if (signupBtn) signupBtn.innerHTML = '<i class="bi bi-check-circle me-2"></i>Create Free Account';
  } else {
    vendorCard.classList.add('border-warning', 'bg-dark');
    vendorCard.classList.remove('border-secondary');
    freeCard.classList.remove('border-success', 'bg-dark');
    freeCard.classList.add('border-secondary');
    if (vendorFields) vendorFields.classList.remove('d-none');
    document.getElementById('vendorAccount').checked = true;
    if (signupBtn) signupBtn.innerHTML = '<i class="bi bi-star-fill me-2"></i>Create Vendor Account (R299/month)';
  }
}

// ============================================
// PASSWORD VISIBILITY TOGGLE
// ============================================

function togglePassword(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  
  const btn = field.nextElementSibling;
  
  if (field.type === 'password') {
    field.type = 'text';
    if (btn) btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
  } else {
    field.type = 'password';
    if (btn) btn.innerHTML = '<i class="bi bi-eye"></i>';
  }
}

// ============================================
// SIGNUP FORM SUBMISSION
// ============================================

function setupSignupForm() {
  const signupForm = document.getElementById('signupForm');
  if (!signupForm) return;
  
  signupForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const accountType = document.querySelector('input[name="accountType"]:checked').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const age = document.getElementById('age').value;
    const location = document.getElementById('location').value;
    const email = document.getElementById('email').value;
    
    // Vendor-specific fields
    let vendorData = null;
    if (accountType === 'vendor') {
      vendorData = {
        businessName: document.getElementById('businessName')?.value || '',
        whatsapp: document.getElementById('whatsapp')?.value || '',
        serviceDesc: document.getElementById('serviceDesc')?.value || ''
      };
    }
    
    const signupData = {
      username: username,
      password: password,
      age: age,
      location: location || '',
      email: email || '',
      account_type: accountType,
      vendor_data: vendorData
    };
    
    try {
      const response = await fetch(`${API_BASE}/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(signupData)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Save user session
        const userData = {
          username: username,
          account_type: accountType,
          age: age,
          location: location,
          email: email,
          verified: accountType === 'free',
          created_at: new Date().toISOString()
        };
        
        saveUserSession(userData);
        
        alert(`✅ Welcome, ${username}!\n\nYour ${accountType} account is ready!`);
        
        bootstrap.Modal.getInstance(document.getElementById('signupModal')).hide();
        
        // Redirect based on account type
        if (accountType === 'vendor') {
          window.location.href = 'vendor-payment.html';
        } else {
          window.location.href = 'post-ad.html';
        }
      } else {
        alert(`❌ Signup failed: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Signup error:', error);
      alert('❌ Network error. Make sure the Flask server is running at http://127.0.0.1:5000');
    }
  });
}

// ============================================
// LOGIN FORM SUBMISSION
// ============================================

function setupLoginForm() {
  const loginForm = document.getElementById('loginForm');
  if (!loginForm) return;
  
  loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Get full user data from check_auth endpoint
        const authResponse = await fetch(`${API_BASE}/check_auth`, {
          credentials: 'include'
        });
        
        const authData = await authResponse.json();
        
        if (authResponse.ok && authData.logged_in) {
          saveUserSession(authData.user_data);
          
          alert(`✅ Welcome back, ${username}!`);
          
          bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
          
          // Always redirect to dashboard after login
          window.location.href = 'dashboard.html';
        }
      } else {
        alert(`❌ Login failed: ${data.error || 'Invalid credentials'}`);
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('❌ Network error. Make sure the Flask server is running at http://127.0.0.1:5000');
    }
  });
}

// ============================================
// POST AD FORM LOGIC (for post-ad.html)
// ============================================

function setupPostAdPage() {
  // Check login status on page load
  const gate = document.getElementById('loginGate');
  const form = document.getElementById('postFormContainer');
  
  if (!gate || !form) return;
  
  if (isUserLoggedIn()) {
    gate.classList.add('d-none');
    form.classList.remove('d-none');
  } else {
    gate.classList.remove('d-none');
    form.classList.add('d-none');
  }
}

function setupPostAdForm() {
  const postAdForm = document.getElementById('postAdForm');
  if (!postAdForm) return;
  
  postAdForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!isUserLoggedIn()) {
      alert('Please login first');
      return;
    }
    
    // Collect form data
    const formData = {
      title: postAdForm.querySelector('input[type="text"]').value,
      category: postAdForm.querySelector('select').value,
      // Add more fields as needed
    };
    
    try {
      const response = await fetch(`${API_BASE}/post_ad`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        alert('✅ Ad posted successfully! It will be reviewed within 24 hours.');
        window.location.href = 'my-ads.html';
      } else {
        alert(`❌ Post failed: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Post ad error:', error);
      alert('❌ Network error. Please try again.');
    }
  });
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
  // Update navbar
  updateNavbar();
  
  // Setup forms
  setupSignupForm();
  setupLoginForm();
  
  // Post ad page specific
  setupPostAdPage();
  setupPostAdForm();
  
  // Attach post ad button handlers
  const postAdButtons = document.querySelectorAll('[data-action="post-ad"]');
  postAdButtons.forEach(button => {
    button.addEventListener('click', handlePostAdClick);
  });
  
  // Attach vendor portal button handlers
  const vendorButtons = document.querySelectorAll('[data-action="vendor-portal"]');
  vendorButtons.forEach(button => {
    button.addEventListener('click', handleVendorPortalClick);
  });
  
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
