from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import json
from datetime import datetime, timedelta

# Photo upload configuration - BEFORE app creation
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Create uploads folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)

# File upload config
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max request
app.secret_key = 'hookupza_secret_2026_change_in_production'

# CRITICAL: Proper CORS configuration for sessions
CORS(app,
     supports_credentials=True,
     origins=['http://127.0.0.1:5500', 'http://localhost:5500', 'http://127.0.0.1:5501', 'http://localhost:5501'],
     allow_headers=['Content-Type'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Session configuration
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_NAME'] = 'hookupza_session'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Database setup
DB_FILE = 'hookupza.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            age TEXT,
            location TEXT,
            email TEXT,
            account_type TEXT DEFAULT 'free',
            vendor_data TEXT,
            vendor_paid INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute("PRAGMA table_info(users)")
        columns = {row['name'] for row in cursor.fetchall()}
        if 'role' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            print("✅ Added 'role' column to users table")
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT,
            description TEXT,
            services TEXT,
            rate TEXT,
            contact TEXT,
            photos TEXT,
            status TEXT DEFAULT 'pending',
            is_premium INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        conn.commit()
        print("✅ Database initialized/updated successfully!")

init_db()

def debug_session(f):
    def wrapper(*args, **kwargs):
        print(f"\n🔍 SESSION DEBUG for {f.__name__}:")
        print(f"   Session ID: {session.get('user_id', 'NONE')}")
        print(f"   Username: {session.get('username', 'NONE')}")
        print(f"   Role: {session.get('role', 'NONE')}")
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def is_admin():
    if 'user_id' not in session:
        return False
    with get_db() as conn:
        user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if user:
            return dict(user).get('role', 'user') == 'admin'
        return False

# ============================================
# SERVE UPLOADED FILES
# ============================================

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded photos"""
    return send_from_directory(UPLOAD_FOLDER, filename)

# ============================================
# AUTHENTICATION
# ============================================

@app.route('/api/signup', methods=['POST'])
@debug_session
def signup():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        age = data.get('age')
        location = data.get('location', '')
        email = data.get('email', '')
        account_type = data.get('account_type', 'free')
        vendor_data = data.get('vendor_data')
        
        if not username or not password or not age:
            return jsonify({'error': 'Missing required fields'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        password_hash = generate_password_hash(password)
        vendor_data_json = json.dumps(vendor_data) if vendor_data else None
        
        with get_db() as conn:
            try:
                cursor = conn.execute('''
                INSERT INTO users (username, password_hash, age, location, email, account_type, role, vendor_data, verified, vendor_paid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, password_hash, age, location, email, account_type, 'user', vendor_data_json, 1 if account_type == 'free' else 0, 0))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                session.permanent = True
                session['user_id'] = user_id
                session['username'] = username
                session['account_type'] = account_type
                session['role'] = 'user'
                session.modified = True
                
                print(f"✅ User created: {username} (ID: {user_id})")
                
                return jsonify({
                    'message': 'Account created successfully',
                    'username': username,
                    'account_type': account_type,
                    'role': 'user',
                    'user_id': user_id
                }), 201
                
            except sqlite3.IntegrityError:
                return jsonify({'error': 'Username already exists'}), 400
                
    except Exception as e:
        print(f"❌ Signup error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
@debug_session
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Missing username or password'}), 400
        
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                user_dict = dict(user)
                
                session.permanent = True
                session['user_id'] = user_dict['id']
                session['username'] = user_dict['username']
                session['account_type'] = user_dict.get('account_type', 'free')
                session['role'] = user_dict.get('role', 'user')
                session.modified = True
                
                print(f"✅ Login successful: {username}")
                
                return jsonify({
                    'message': 'Login successful',
                    'username': user_dict['username'],
                    'account_type': user_dict.get('account_type', 'free'),
                    'role': user_dict.get('role', 'user'),
                    'user_id': user_dict['id']
                })
            
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/check_auth', methods=['GET'])
@debug_session
def check_auth():
    if 'user_id' in session:
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            
            if user:
                user_dict = dict(user)
                return jsonify({
                    'logged_in': True,
                    'user_data': {
                        'user_id': user_dict['id'],
                        'username': user_dict['username'],
                        'account_type': user_dict.get('account_type', 'free'),
                        'age': user_dict.get('age'),
                        'location': user_dict.get('location'),
                        'email': user_dict.get('email'),
                        'verified': bool(user_dict.get('verified', 0)),
                        'vendor_paid': bool(user_dict.get('vendor_paid', 0)),
                        'created_at': user_dict.get('created_at'),
                        'role': user_dict.get('role', 'user')
                    }
                })
    
    return jsonify({'logged_in': False, 'error': 'Not logged in'}), 401

@app.route('/api/logout', methods=['POST'])
@debug_session
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    print(f"✅ Logout successful: {username}")
    return jsonify({'message': 'Logged out successfully'})

# ============================================
# AD MANAGEMENT
# ============================================

@app.route('/api/post_ad', methods=['POST', 'OPTIONS'])
@debug_session
def post_ad():
    if request.method == 'OPTIONS':
        return '', 204
    
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    try:
        data = request.json
        user_id = session['user_id']
        account_type = session.get('account_type', 'free')
        
        title = data.get('title')
        category = data.get('category')
        location = data.get('location')
        description = data.get('description')
        services = json.dumps(data.get('services', []))
        rate = data.get('rate', '')
        contact = data.get('contact')
        photos = json.dumps(data.get('photos', []))
        
        if not title or not category or not description or not contact:
            return jsonify({'error': 'Missing required fields'}), 400
        
        days = 30 if account_type == 'vendor' else 3
        is_premium = 1 if account_type == 'vendor' else 0
        status = 'active' if account_type == 'vendor' else 'pending'
        
        with get_db() as conn:
            cursor = conn.execute('''
            INSERT INTO ads (user_id, title, category, location, description, services, rate, contact, photos, status, is_premium, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+' || ? || ' days'))
            ''', (user_id, title, category, location, description, services, rate, contact, photos, status, is_premium, days))
            
            ad_id = cursor.lastrowid
            conn.commit()
        
        print(f"✅ Ad posted: ID {ad_id}")
        
        return jsonify({
            'message': 'Ad posted successfully',
            'ad_id': ad_id,
            'expires_in_days': days
        }), 201
        
    except Exception as e:
        print(f"❌ Post ad error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/my_ads', methods=['GET'])
@debug_session
def my_ads():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    try:
        with get_db() as conn:
            ads = conn.execute('''
            SELECT id, title, category, location, status, is_premium, created_at, expires_at
            FROM ads WHERE user_id = ? ORDER BY created_at DESC
            ''', (session['user_id'],)).fetchall()
            
            return jsonify({'ads': [dict(ad) for ad in ads]})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_ad/<int:ad_id>', methods=['GET'])
def get_ad_detail(ad_id):
    try:
        with get_db() as conn:
            ad = conn.execute('''
            SELECT a.*, u.username, u.account_type
            FROM ads a JOIN users u ON a.user_id = u.id
            WHERE a.id = ?
            ''', (ad_id,)).fetchone()
            
            if not ad:
                return jsonify({'error': 'Ad not found'}), 404
            
            ad_dict = dict(ad)
            
            if ad_dict.get('services'):
                try:
                    ad_dict['services'] = json.loads(ad_dict['services'])
                except:
                    pass
            
            if ad_dict.get('photos'):
                try:
                    ad_dict['photos'] = json.loads(ad_dict['photos'])
                except:
                    pass
            
            return jsonify({'ad': ad_dict})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/edit_ad/<int:ad_id>', methods=['PUT'])
@debug_session
def edit_ad(ad_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    try:
        with get_db() as conn:
            ad = conn.execute('SELECT * FROM ads WHERE id = ?', (ad_id,)).fetchone()
            
            if not ad:
                return jsonify({'error': 'Ad not found'}), 404
            
            ad_dict = dict(ad)
            
            if ad_dict['user_id'] != session['user_id'] and not is_admin():
                return jsonify({'error': 'Unauthorized'}), 403
            
            data = request.json
            
            title = data.get('title', ad_dict['title'])
            description = data.get('description', ad_dict['description'])
            category = data.get('category', ad_dict['category'])
            location = data.get('location', ad_dict['location'])
            services = data.get('services', ad_dict['services'])
            rate = data.get('rate', ad_dict['rate'])
            contact = data.get('contact', ad_dict['contact'])
            photos = data.get('photos', ad_dict['photos'])
            
            if isinstance(services, list):
                services = json.dumps(services)
            if isinstance(photos, list):
                photos = json.dumps(photos)
            
            conn.execute('''
            UPDATE ads 
            SET title = ?, description = ?, category = ?, location = ?, 
                services = ?, rate = ?, contact = ?, photos = ?
            WHERE id = ?
            ''', (title, description, category, location, services, rate, contact, photos, ad_id))
            
            conn.commit()
        
        print(f"✅ Ad updated: ID {ad_id}")
        return jsonify({'message': 'Ad updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_ad/<int:ad_id>', methods=['DELETE', 'OPTIONS'])
@debug_session
def delete_ad(ad_id):
    if request.method == 'OPTIONS':
        return '', 204
    
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    try:
        with get_db() as conn:
            ad = conn.execute('SELECT * FROM ads WHERE id = ? AND user_id = ?',
                            (ad_id, session['user_id'])).fetchone()
            
            if not ad:
                return jsonify({'error': 'Ad not found or unauthorized'}), 404
            
            conn.execute('DELETE FROM ads WHERE id = ?', (ad_id,))
            conn.commit()
        
        print(f"✅ Ad deleted: ID {ad_id}")
        return jsonify({'message': 'Ad deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_account', methods=['DELETE', 'OPTIONS'])
@debug_session
def delete_account():
    if request.method == 'OPTIONS':
        return '', 204
    
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    try:
        user_id = session['user_id']
        
        with get_db() as conn:
            conn.execute('DELETE FROM ads WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
        
        session.clear()
        print(f"✅ Account deleted: {user_id}")
        return jsonify({'message': 'Account deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# PHOTO UPLOAD
# ============================================

@app.route('/api/upload_photo', methods=['POST'])
@debug_session
def upload_photo():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo provided'}), 400
    
    file = request.files['photo']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Max 5MB'}), 400
    
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(filepath)
        
        print(f"✅ Photo uploaded: {unique_filename}")
        
        return jsonify({
            'message': 'Photo uploaded successfully',
            'filename': unique_filename,
            'url': f'/uploads/{unique_filename}'
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/delete_photo', methods=['DELETE'])
@debug_session
def delete_photo():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'message': 'Photo deleted successfully'})
        else:
            return jsonify({'error': 'Photo not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# ADMIN ENDPOINTS
# ============================================

@app.route('/api/admin/check_role', methods=['GET'])
@debug_session
def check_admin_role():
    if 'user_id' not in session:
        return jsonify({'is_admin': False}), 401
    
    try:
        with get_db() as conn:
            user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            
            if user and dict(user).get('role', 'user') == 'admin':
                return jsonify({'is_admin': True, 'username': session.get('username')})
            
            return jsonify({'is_admin': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/stats', methods=['GET'])
@debug_session
def admin_stats():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        with get_db() as conn:
            stats = {
                'total_users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
                'total_ads': conn.execute('SELECT COUNT(*) FROM ads').fetchone()[0],
                'pending_ads': conn.execute("SELECT COUNT(*) FROM ads WHERE status = 'pending'").fetchone()[0],
                'active_ads': conn.execute("SELECT COUNT(*) FROM ads WHERE status = 'active'").fetchone()[0],
                'expired_ads': conn.execute("SELECT COUNT(*) FROM ads WHERE status = 'expired'").fetchone()[0],
                'premium_users': conn.execute("SELECT COUNT(*) FROM users WHERE account_type = 'vendor'").fetchone()[0],
                'free_users': conn.execute("SELECT COUNT(*) FROM users WHERE account_type = 'free'").fetchone()[0],
            }
            return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/all_ads', methods=['GET'])
@debug_session
def admin_all_ads():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        with get_db() as conn:
            ads = conn.execute('''
            SELECT a.*, u.username, u.account_type
            FROM ads a JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            ''').fetchall()
            
            return jsonify({'ads': [dict(ad) for ad in ads]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/approve_ad/<int:ad_id>', methods=['POST'])
@debug_session
def approve_ad(ad_id):
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        with get_db() as conn:
            conn.execute('UPDATE ads SET status = ? WHERE id = ?', ('active', ad_id))
            conn.commit()
        return jsonify({'message': 'Ad approved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/reject_ad/<int:ad_id>', methods=['POST'])
@debug_session
def reject_ad(ad_id):
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        with get_db() as conn:
            conn.execute('UPDATE ads SET status = ? WHERE id = ?', ('rejected', ad_id))
            conn.commit()
        return jsonify({'message': 'Ad rejected'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/auto_approve', methods=['POST'])
@debug_session
def auto_approve_old_ads():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        with get_db() as conn:
            cursor = conn.execute('''
            UPDATE ads SET status = 'active'
            WHERE status = 'pending'
            AND created_at <= datetime('now', '-24 hours')
            ''')
            approved_count = cursor.rowcount
            conn.commit()
        
        return jsonify({'message': f'{approved_count} ads auto-approved', 'count': approved_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/expire_old_ads', methods=['POST'])
@debug_session
def expire_old_ads():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        with get_db() as conn:
            cursor = conn.execute('''
            UPDATE ads SET status = 'expired'
            WHERE status = 'active'
            AND expires_at <= datetime('now')
            ''')
            expired_count = cursor.rowcount
            conn.commit()
        
        return jsonify({'message': f'{expired_count} ads expired', 'count': expired_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
@debug_session
def get_all_users():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        with get_db() as conn:
            users = conn.execute('''
            SELECT id, username, email, age, location, account_type, role,
                   vendor_paid, verified, created_at
            FROM users ORDER BY created_at DESC
            ''').fetchall()
            
            return jsonify({'users': [dict(user) for user in users]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/create_admin', methods=['POST'])
@debug_session
def create_admin():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        password_hash = generate_password_hash(password)
        
        with get_db() as conn:
            cursor = conn.execute('''
            INSERT INTO users (username, password_hash, email, age, account_type, role, verified)
            VALUES (?, ?, ?, '35-44', 'free', 'admin', 1)
            ''', (username, password_hash, email))
            
            admin_id = cursor.lastrowid
            conn.commit()
        
        return jsonify({'message': 'Admin created successfully', 'admin_id': admin_id, 'username': username}), 201
        
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/update_role', methods=['POST'])
@debug_session
def update_user_role():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.json
        user_id = data.get('user_id')
        new_role = data.get('role')
        
        if new_role not in ['user', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
        
        with get_db() as conn:
            conn.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
            conn.commit()
        
        return jsonify({'message': f'Role updated to {new_role}'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/delete_user', methods=['DELETE'])
@debug_session
def admin_delete_user():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        user_id = request.json.get('user_id')
        
        with get_db() as conn:
            conn.execute('DELETE FROM ads WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/public_ads', methods=['GET'])
def get_public_ads():
    try:
        category = request.args.get('category', 'all')
        
        with get_db() as conn:
            if category == 'all':
                ads = conn.execute('''
                SELECT a.*, u.username FROM ads a
                JOIN users u ON a.user_id = u.id
                WHERE a.status = 'active' AND a.expires_at > datetime('now')
                ORDER BY a.is_premium DESC, a.created_at DESC LIMIT 100
                ''').fetchall()
            else:
                ads = conn.execute('''
                SELECT a.*, u.username FROM ads a
                JOIN users u ON a.user_id = u.id
                WHERE a.status = 'active' AND a.category = ? AND a.expires_at > datetime('now')
                ORDER BY a.is_premium DESC, a.created_at DESC LIMIT 100
                ''', (category,)).fetchall()
            
            return jsonify({'ads': [dict(ad) for ad in ads]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 HookUpZA Backend Server Starting...")
    print("=" * 50)
    print("📍 Server: http://127.0.0.1:5000")
    print("🔐 Database: hookupza.db")
    print("🔧 CORS enabled for: 127.0.0.1:5500, 5501")
    print("=" * 50)
    app.run(debug=True, port=5000)
