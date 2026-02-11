from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import json
from datetime import datetime, timedelta

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.secret_key = 'hookupza_secret_2026_change_in_production'

CORS(app,
     supports_credentials=True,
     origins=[
         'http://127.0.0.1:5500', 'http://localhost:5500',
         'http://127.0.0.1:5501', 'http://localhost:5501',
         'https://hookupza.onrender.com'
     ],
     allow_headers=['Content-Type'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_NAME'] = 'hookupza_session'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

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
            print("Added role column")
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
        print("Database ready!")

init_db()

def debug_session(f):
    def wrapper(*args, **kwargs):
        print(f"\nSESSION for {f.__name__}: user_id={session.get('user_id','NONE')} username={session.get('username','NONE')} role={session.get('role','NONE')}")
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def is_admin():
    if 'user_id' not in session:
        return False
    with get_db() as conn:
        user = conn.execute('SELECT role FROM users WHERE id=?', (session['user_id'],)).fetchone()
        return dict(user).get('role') == 'admin' if user else False

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/signup', methods=['POST', 'OPTIONS'])
@debug_session
def signup():
    if request.method == 'OPTIONS': return '', 204
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        age = data.get('age')
        if not username or not password or not age:
            return jsonify({'error': 'Missing required fields'}), 400
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        password_hash = generate_password_hash(password)
        account_type = data.get('account_type', 'free')
        vendor_data_json = json.dumps(data.get('vendor_data')) if data.get('vendor_data') else None
        with get_db() as conn:
            try:
                cursor = conn.execute('''
                INSERT INTO users (username, password_hash, age, location, email, account_type, role, vendor_data, verified, vendor_paid)
                VALUES (?, ?, ?, ?, ?, ?, 'user', ?, ?, 0)
                ''', (username, password_hash, age, data.get('location',''), data.get('email',''),
                      account_type, vendor_data_json, 1 if account_type == 'free' else 0))
                user_id = cursor.lastrowid
                conn.commit()
                session.permanent = True
                session['user_id'] = user_id
                session['username'] = username
                session['account_type'] = account_type
                session['role'] = 'user'
                session.modified = True
                print(f"User registered: {username} ID={user_id}")
                return jsonify({'message': 'Account created successfully', 'username': username,
                                'account_type': account_type, 'role': 'user', 'user_id': user_id}), 201
            except sqlite3.IntegrityError:
                return jsonify({'error': 'Username already exists'}), 400
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST', 'OPTIONS'])
@debug_session
def login():
    if request.method == 'OPTIONS': return '', 204
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        if not username or not password:
            return jsonify({'error': 'Missing username or password'}), 400
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
            if not user:
                return jsonify({'error': 'Invalid credentials'}), 401
            user_dict = dict(user)
            if not check_password_hash(user_dict['password_hash'], password):
                return jsonify({'error': 'Invalid credentials'}), 401
            session.permanent = True
            session['user_id'] = user_dict['id']
            session['username'] = user_dict['username']
            session['account_type'] = user_dict.get('account_type', 'free')
            session['role'] = user_dict.get('role', 'user')
            session.modified = True
            print(f"Login OK: {username} role={session['role']}")
            return jsonify({'message': 'Login successful', 'username': user_dict['username'],
                            'account_type': user_dict.get('account_type','free'),
                            'role': user_dict.get('role','user'), 'user_id': user_dict['id']})
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_auth', methods=['GET', 'OPTIONS'])
@debug_session
def check_auth():
    if request.method == 'OPTIONS': return '', 204
    if 'user_id' not in session:
        return jsonify({'logged_in': False, 'error': 'Not logged in'}), 401
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
        if not user:
            session.clear()
            return jsonify({'logged_in': False}), 401
        u = dict(user)
        return jsonify({'logged_in': True, 'authenticated': True, 'username': u['username'],
                        'role': u.get('role','user'), 'account_type': u.get('account_type','free'),
                        'user_id': u['id'],
                        'user_data': {'user_id': u['id'], 'username': u['username'],
                                      'account_type': u.get('account_type','free'),
                                      'age': u.get('age'), 'location': u.get('location'),
                                      'email': u.get('email'), 'verified': bool(u.get('verified',0)),
                                      'vendor_paid': bool(u.get('vendor_paid',0)),
                                      'created_at': u.get('created_at'), 'role': u.get('role','user')}})

@app.route('/api/logout', methods=['POST', 'OPTIONS'])
@debug_session
def logout():
    if request.method == 'OPTIONS': return '', 204
    username = session.get('username', 'Unknown')
    session.clear()
    print(f"Logout: {username}")
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/post_ad', methods=['POST', 'OPTIONS'])
@debug_session
def post_ad():
    if request.method == 'OPTIONS': return '', 204
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    try:
        data = request.json
        title = data.get('title','').strip()
        category = data.get('category','').strip()
        description = data.get('description','').strip()
        contact = data.get('contact','').strip()
        if not title or not category or not description or not contact:
            return jsonify({'error': 'Missing required fields'}), 400
        account_type = session.get('account_type', 'free')
        role = session.get('role', 'user')
        # Admin OR vendor = live immediately, 30 days
        # Free user = pending, 3 days
        if role == 'admin' or account_type == 'vendor':
            days, is_premium, status = 30, 1, 'active'
        else:
            days, is_premium, status = 3, 0, 'pending'
        with get_db() as conn:
            cursor = conn.execute('''
            INSERT INTO ads (user_id, title, category, location, description, services, rate, contact, photos, status, is_premium, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+' || ? || ' days'))
            ''', (session['user_id'], title, category, data.get('location',''), description,
                  json.dumps(data.get('services',[])), data.get('rate',''), contact,
                  json.dumps(data.get('photos',[])), status, is_premium, str(days)))
            ad_id = cursor.lastrowid
            conn.commit()
        print(f"Ad posted: ID={ad_id} status={status} premium={is_premium}")
        return jsonify({'message': 'Ad posted successfully', 'ad_id': ad_id, 'status': status, 'expires_in_days': days}), 201
    except Exception as e:
        print(f"Post ad error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/public_ads', methods=['GET', 'OPTIONS'])
def get_public_ads():
    if request.method == 'OPTIONS': return '', 204
    try:
        category = request.args.get('category', 'all')
        with get_db() as conn:
            if category == 'all':
                ads = conn.execute('''SELECT a.*, u.username FROM ads a JOIN users u ON a.user_id=u.id
                WHERE a.status='active' AND a.expires_at > datetime('now')
                ORDER BY a.is_premium DESC, a.created_at DESC LIMIT 100''').fetchall()
            else:
                ads = conn.execute('''SELECT a.*, u.username FROM ads a JOIN users u ON a.user_id=u.id
                WHERE a.status='active' AND a.category=? AND a.expires_at > datetime('now')
                ORDER BY a.is_premium DESC, a.created_at DESC LIMIT 100''', (category,)).fetchall()
            return jsonify({'ads': [dict(ad) for ad in ads]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/my_ads', methods=['GET', 'OPTIONS'])
@debug_session
def my_ads():
    if request.method == 'OPTIONS': return '', 204
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    try:
        with get_db() as conn:
            ads = conn.execute('''SELECT id, title, category, location, status, is_premium, created_at, expires_at
            FROM ads WHERE user_id=? ORDER BY created_at DESC''', (session['user_id'],)).fetchall()
            return jsonify({'ads': [dict(ad) for ad in ads]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_ad/<int:ad_id>', methods=['GET'])
def get_ad_detail(ad_id):
    try:
        with get_db() as conn:
            ad = conn.execute('''SELECT a.*, u.username, u.account_type FROM ads a
            JOIN users u ON a.user_id=u.id WHERE a.id=?''', (ad_id,)).fetchone()
            if not ad: return jsonify({'error': 'Ad not found'}), 404
            ad_dict = dict(ad)
            for field in ['services', 'photos']:
                if ad_dict.get(field):
                    try: ad_dict[field] = json.loads(ad_dict[field])
                    except: pass
            return jsonify({'ad': ad_dict})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/edit_ad/<int:ad_id>', methods=['PUT', 'OPTIONS'])
@debug_session
def edit_ad(ad_id):
    if request.method == 'OPTIONS': return '', 204
    if 'user_id' not in session: return jsonify({'error': 'Login required'}), 401
    try:
        with get_db() as conn:
            ad = conn.execute('SELECT * FROM ads WHERE id=?', (ad_id,)).fetchone()
            if not ad: return jsonify({'error': 'Ad not found'}), 404
            ad_dict = dict(ad)
            if ad_dict['user_id'] != session['user_id'] and not is_admin():
                return jsonify({'error': 'Unauthorized'}), 403
            data = request.json
            services = data.get('services', ad_dict['services'])
            photos = data.get('photos', ad_dict['photos'])
            if isinstance(services, list): services = json.dumps(services)
            if isinstance(photos, list): photos = json.dumps(photos)
            conn.execute('''UPDATE ads SET title=?,description=?,category=?,location=?,
            services=?,rate=?,contact=?,photos=? WHERE id=?''',
            (data.get('title',ad_dict['title']), data.get('description',ad_dict['description']),
             data.get('category',ad_dict['category']), data.get('location',ad_dict['location']),
             services, data.get('rate',ad_dict['rate']), data.get('contact',ad_dict['contact']),
             photos, ad_id))
            conn.commit()
        return jsonify({'message': 'Ad updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_ad/<int:ad_id>', methods=['DELETE', 'OPTIONS'])
@debug_session
def delete_ad(ad_id):
    if request.method == 'OPTIONS': return '', 204
    if 'user_id' not in session: return jsonify({'error': 'Login required'}), 401
    try:
        with get_db() as conn:
            ad = conn.execute('SELECT * FROM ads WHERE id=? AND user_id=?', (ad_id, session['user_id'])).fetchone()
            if not ad: return jsonify({'error': 'Ad not found or unauthorized'}), 404
            conn.execute('DELETE FROM ads WHERE id=?', (ad_id,))
            conn.commit()
        return jsonify({'message': 'Ad deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_account', methods=['DELETE', 'OPTIONS'])
@debug_session
def delete_account():
    if request.method == 'OPTIONS': return '', 204
    if 'user_id' not in session: return jsonify({'error': 'Login required'}), 401
    try:
        user_id = session['user_id']
        with get_db() as conn:
            conn.execute('DELETE FROM ads WHERE user_id=?', (user_id,))
            conn.execute('DELETE FROM users WHERE id=?', (user_id,))
            conn.commit()
        session.clear()
        return jsonify({'message': 'Account deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload_photo', methods=['POST', 'OPTIONS'])
@debug_session
def upload_photo():
    if request.method == 'OPTIONS': return '', 204
    if 'user_id' not in session: return jsonify({'error': 'Login required'}), 401
    if 'photo' not in request.files: return jsonify({'error': 'No photo provided'}), 400
    file = request.files['photo']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    file.seek(0, os.SEEK_END)
    if file.tell() > MAX_FILE_SIZE: return jsonify({'error': 'File too large (max 5MB)'}), 400
    file.seek(0)
    try:
        unique_filename = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
        file.save(os.path.join(UPLOAD_FOLDER, unique_filename))
        print(f"Photo uploaded: {unique_filename}")
        return jsonify({'message': 'Photo uploaded successfully', 'filename': unique_filename, 'url': f'/uploads/{unique_filename}'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_photo', methods=['DELETE', 'OPTIONS'])
@debug_session
def delete_photo():
    if request.method == 'OPTIONS': return '', 204
    if 'user_id' not in session: return jsonify({'error': 'Login required'}), 401
    try:
        filename = request.json.get('filename')
        if not filename: return jsonify({'error': 'No filename provided'}), 400
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'message': 'Photo deleted successfully'})
        return jsonify({'error': 'Photo not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/check_role', methods=['GET', 'OPTIONS'])
@debug_session
def check_admin_role():
    if request.method == 'OPTIONS': return '', 204
    if 'user_id' not in session: return jsonify({'is_admin': False}), 200
    try:
        with get_db() as conn:
            user = conn.execute('SELECT role FROM users WHERE id=?', (session['user_id'],)).fetchone()
            if user and dict(user).get('role') == 'admin':
                return jsonify({'is_admin': True, 'username': session.get('username')})
            return jsonify({'is_admin': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/stats', methods=['GET'])
@debug_session
def admin_stats():
    if not is_admin(): return jsonify({'error': 'Admin access required'}), 403
    try:
        with get_db() as conn:
            return jsonify({
                'total_users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
                'total_ads': conn.execute('SELECT COUNT(*) FROM ads').fetchone()[0],
                'pending_ads': conn.execute("SELECT COUNT(*) FROM ads WHERE status='pending'").fetchone()[0],
                'active_ads': conn.execute("SELECT COUNT(*) FROM ads WHERE status='active'").fetchone()[0],
                'expired_ads': conn.execute("SELECT COUNT(*) FROM ads WHERE status='expired'").fetchone()[0],
                'premium_users': conn.execute("SELECT COUNT(*) FROM users WHERE account_type='vendor'").fetchone()[0],
                'free_users': conn.execute("SELECT COUNT(*) FROM users WHERE account_type='free'").fetchone()[0],
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/all_ads', methods=['GET', 'OPTIONS'])
@debug_session
def admin_all_ads():
    if request.method == 'OPTIONS': return '', 204
    if not is_admin(): return jsonify({'error': 'Admin access required'}), 403
    try:
        with get_db() as conn:
            ads = conn.execute('''SELECT a.*, u.username, u.account_type FROM ads a
            JOIN users u ON a.user_id=u.id ORDER BY a.created_at DESC''').fetchall()
            return jsonify({'ads': [dict(ad) for ad in ads]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/approve_ad/<int:ad_id>', methods=['POST', 'OPTIONS'])
@debug_session
def approve_ad(ad_id):
    if request.method == 'OPTIONS': return '', 204
    if not is_admin(): return jsonify({'error': 'Admin access required'}), 403
    try:
        with get_db() as conn:
            conn.execute("UPDATE ads SET status='active' WHERE id=?", (ad_id,))
            conn.commit()
        return jsonify({'message': 'Ad approved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/reject_ad/<int:ad_id>', methods=['POST', 'OPTIONS'])
@debug_session
def reject_ad(ad_id):
    if request.method == 'OPTIONS': return '', 204
    if not is_admin(): return jsonify({'error': 'Admin access required'}), 403
    try:
        with get_db() as conn:
            conn.execute("UPDATE ads SET status='rejected' WHERE id=?", (ad_id,))
            conn.commit()
        return jsonify({'message': 'Ad rejected'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/auto_approve', methods=['POST', 'OPTIONS'])
@debug_session
def auto_approve_old_ads():
    if request.method == 'OPTIONS': return '', 204
    if not is_admin(): return jsonify({'error': 'Admin access required'}), 403
    try:
        with get_db() as conn:
            cursor = conn.execute("""UPDATE ads SET status='active'
            WHERE status='pending' AND created_at <= datetime('now', '-24 hours')""")
            conn.commit()
        return jsonify({'message': f'{cursor.rowcount} ads auto-approved', 'count': cursor.rowcount})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/expire_old_ads', methods=['POST', 'OPTIONS'])
@debug_session
def expire_old_ads():
    if request.method == 'OPTIONS': return '', 204
    if not is_admin(): return jsonify({'error': 'Admin access required'}), 403
    try:
        with get_db() as conn:
            cursor = conn.execute("""UPDATE ads SET status='expired'
            WHERE status='active' AND expires_at <= datetime('now')""")
            conn.commit()
        return jsonify({'message': f'{cursor.rowcount} ads expired', 'count': cursor.rowcount})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET', 'OPTIONS'])
@debug_session
def get_all_users():
    if request.method == 'OPTIONS': return '', 204
    if not is_admin(): return jsonify({'error': 'Admin access required'}), 403
    try:
        with get_db() as conn:
            users = conn.execute('''SELECT id, username, email, age, location, account_type, role,
            vendor_paid, verified, created_at FROM users ORDER BY created_at DESC''').fetchall()
            return jsonify({'users': [dict(u) for u in users]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/create_admin', methods=['POST', 'OPTIONS'])
@debug_session
def create_admin():
    if request.method == 'OPTIONS': return '', 204
    if not is_admin(): return jsonify({'error': 'Admin access required'}), 403
    try:
        data = request.json
        username, password = data.get('username'), data.get('password')
        if not username or not password: return jsonify({'error': 'Username and password required'}), 400
        password_hash = generate_password_hash(password)
        with get_db() as conn:
            cursor = conn.execute('''INSERT INTO users (username, password_hash, email, age, account_type, role, verified)
            VALUES (?, ?, ?, '35-44', 'vendor', 'admin', 1)''', (username, password_hash, data.get('email','')))
            admin_id = cursor.lastrowid
            conn.commit()
        return jsonify({'message': 'Admin created', 'admin_id': admin_id, 'username': username}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/update_role', methods=['POST', 'OPTIONS'])
@debug_session
def update_user_role():
    if request.method == 'OPTIONS': return '', 204
    if not is_admin(): return jsonify({'error': 'Admin access required'}), 403
    try:
        data = request.json
        if data.get('role') not in ['user', 'admin']: return jsonify({'error': 'Invalid role'}), 400
        with get_db() as conn:
            conn.execute('UPDATE users SET role=? WHERE id=?', (data['role'], data['user_id']))
            conn.commit()
        return jsonify({'message': f"Role updated to {data['role']}"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/delete_user', methods=['DELETE', 'OPTIONS'])
@debug_session
def admin_delete_user():
    if request.method == 'OPTIONS': return '', 204
    if not is_admin(): return jsonify({'error': 'Admin access required'}), 403
    try:
        user_id = request.json.get('user_id')
        with get_db() as conn:
            conn.execute('DELETE FROM ads WHERE user_id=?', (user_id,))
            conn.execute('DELETE FROM users WHERE id=?', (user_id,))
            conn.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("HookUpZA Backend Starting...")
    print("Server: http://127.0.0.1:5000")
    print("=" * 50)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
