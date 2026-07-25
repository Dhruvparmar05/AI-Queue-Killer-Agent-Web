import os
import sqlite3
import asyncio
from flask import Flask, render_template, request, redirect, session, jsonify
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "queue_killer_db_secured_secret_2026")

DATABASE = "database.db"

# ----------------- DATABASE SETUP ----------------- #
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize Database on Startup
init_db()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------- FLASK ROUTES ----------------- #
@app.route('/')
def index():
    if "user_email" in session:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/login')
def login_page():
    if "user_email" in session:
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if "user_email" not in session:
        return redirect('/login')
    return render_template('dashboard.html', user_name=session.get('user_name'))

# ----------------- AUTHENTICATION WITH SQLITE DB ----------------- #
@app.route('/auth/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
                       (name, email, phone, password))
        conn.commit()
        session['user_email'] = email
        session['user_name'] = name
    except sqlite3.IntegrityError:
        conn.close()
        return "<script>alert('Email already registered! Please login.'); window.location.href='/login';</script>"
    
    conn.close()
    return redirect('/dashboard')

@app.route('/auth/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
    conn.close()
    
    if user:
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        return redirect('/dashboard')
    else:
        return "<script>alert('Invalid Email or Password!'); window.location.href='/login';</script>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ----------------- PLAYWRIGHT AUTOMATION ENGINE ----------------- #
async def run_playwright_pipeline(data):
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False, args=["--start-maximized", "--disable-notifications"])
    context = await browser.new_context(no_viewport=True)
    page = await context.new_page()

    portal = data.get('portal')
    is_registered = data.get('is_registered')
    user_id = data.get('portal_user_id')

    try:
        if portal == "passport":
            print("[*] Navigating to Passport India Portal...")
            await page.goto("https://www.passportindia.gov.in", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)
            
            # Dismiss popups
            try:
                close_btn = page.locator("text=Close").first
                if await close_btn.is_visible(timeout=2000):
                    await close_btn.click()
            except Exception:
                pass

            if is_registered:
                print("[*] Navigating to Existing User Login...")
                login_btn = page.locator("text=Existing User Login").first
                if await login_btn.is_visible(timeout=4000):
                    await login_btn.click()
                    await page.wait_for_timeout(2000)

                    user_input = page.locator("input[name='loginId'], input#loginId").first
                    if await user_input.is_visible(timeout=4000) and user_id:
                        await user_input.fill(user_id)
                        print(f"[+] User ID '{user_id}' Auto-filled!")
            else:
                print("[*] Navigating to New User Registration Page...")
                reg_btn = page.locator("text=New User Registration").first
                if await reg_btn.is_visible(timeout=4000):
                    await reg_btn.click()

        elif portal == "rto":
            print("[*] Navigating to Parivahan RTO Portal...")
            await page.goto("https://parivahan.gov.in", wait_until="domcontentloaded")
            
        elif portal == "hospital":
            print("[*] Navigating to ORS Govt Hospital Portal...")
            await page.goto("https://ors.gov.in", wait_until="domcontentloaded")

        # Keep browser active for Captcha / OTP entry
        await page.wait_for_timeout(20000)

    except Exception as e:
        print(f"[-] Execution Error: {e}")

@app.route('/submit_task', methods=['POST'])
def submit_task():
    data = request.get_json(force=True)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_playwright_pipeline(data))

    return jsonify({
        "status": "success",
        "message": f"Agent initialized for {data.get('portal').upper()}! Browser opened for auto-filling."
    }), 200

if __name__ == '__main__':
    print("🚀 QUEUE KILLER SERVER LIVE WITH SQLITE DB ON http://127.0.0.1:5000")
    app.run(debug=True, port=5000)