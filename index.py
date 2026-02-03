from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import timedelta

app = Flask(__name__)

# ✅ SECURITY FIX: Gunakan environment variable untuk SECRET_KEY
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# --- KONFIGURASI DATABASE ---
# ✅ SECURITY FIX: Gunakan environment variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'db_bioskop')
}

def get_db_connection():
    """Membuat koneksi ke database db_bioskop."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# ✅ IMPROVEMENT: Validasi password strength
def validate_password(password):
    """Check password strength"""
    if len(password) < 8:
        return False, "Password harus minimal 8 karakter"
    if not any(char.isdigit() for char in password):
        return False, "Password harus ada angka"
    if not any(char.isalpha() for char in password):
        return False, "Password harus ada huruf"
    return True, "OK"

# ✅ IMPROVEMENT: Decorator untuk route yang butuh login
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes Login dan Sign Up ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username_or_email or not password:
            flash('Isi username dan password dulu', 'error')
            return render_template('login.html')
        
        conn = None
        cursor = None
        
        try:
            conn = get_db_connection()
            if not conn:
                flash('Koneksi database error. Coba lagi nanti.', 'error')
                return render_template('login.html')
            
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE username = %s OR email = %s"
            cursor.execute(query, (username_or_email, username_or_email))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session.permanent = True
                
                flash(f'Halo {user["username"]}! Selamat datang kembali', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Username atau password salah', 'error')
        
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", 'error')
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not username or not email or not password:
            flash('Semua field harus diisi', 'error')
            return render_template('signup.html')
        
        if len(username) < 3:
            flash('Username minimal 3 karakter', 'error')
            return render_template('signup.html')
        
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('signup.html')
        
        hashed_password = generate_password_hash(password)

        conn = None
        cursor = None
        
        try:
            conn = get_db_connection()
            if not conn:
                flash('Koneksi database error. Coba lagi nanti.', 'error')
                return render_template('signup.html')
            
            cursor = conn.cursor()
            query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (username, email, hashed_password))
            conn.commit()
            
            flash('Akun berhasil dibuat! Silakan login', 'success')
            return redirect(url_for('login'))
        
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            
            if err.errno == 1062:
                flash("Username atau email sudah dipakai", 'error')
            else:
                flash(f"Database error: {err.msg}", 'error')
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('signup.html')

# ✅ IMPROVEMENT: Protected route dengan decorator
@app.route('/dashboard')
@login_required
def dashboard():
    username = session.get('username', 'User')
    return render_template('dashboard.html', username=username)

# ✅ IMPROVEMENT: Tambahkan logout functionality
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Berhasil logout. Sampai jumpa!', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

if __name__ == '__main__':
    # ✅ SECURITY FIX: Debug mode dari environment variable
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)