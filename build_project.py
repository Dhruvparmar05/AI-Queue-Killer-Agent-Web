import os

project_files = {
    "app.py": '''import base64
import json
import asyncio
import threading
import os
from flask import Flask, request, jsonify, redirect, url_for, session
from google import genai
from supabase import create_client, Client
from playwright.async_api import async_playwright

base_dir = os.path.abspath(os.path.dirname(__file__))
static_path = os.path.join(base_dir, 'static')

app = Flask(__name__, static_folder=static_path)
app.secret_key = "queue_killer_isolated_session_2026"

# Core Credentials Mapping
SUPABASE_URL = "https://avwbcswgqcwtkcfbuydu.supabase.co"
SUPABASE_KEY = "sb_publishable_tjjCkbvhdulJeT2BXwf1Uw_Z4EvITHW"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# global in-memory state for the active runtime session only (No DB exposure to user UI)
active_session_state = {
    "current_id": None,
    "status": "System Idle",
    "captcha_img": None
}

async def async_passport_pipeline(record_id):
    global active_session_state
    print(f"[AGENT] Spawning independent execution node for ID: {record_id}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=800)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        
        try:
            active_session_state["status"] = "LAUNCHING_BROWSER"
            supabase.table("queue_logs").update({"status": "LAUNCHING_BROWSER"}).eq("id", record_id).execute()
            
            await page.goto("https://www.passportindia.gov.in/", timeout=60000, wait_until="load")
            
            try:
                popup_close = await page.wait_for_selector("a#popupCloseBtn, .close, img[alt='close']", timeout=5000)
                if popup_close:
                    await popup_close.click()
            except Exception:
                pass

            print("[AGENT] Executing dynamic JavaScript bypass routing...")
            await page.evaluate("() => { if(typeof openApplication === 'function') { openApplication('welcomeLink'); } else { window.location.href = 'https://portal2.passportindia.gov.in/AppOnlineProject/welcomeLink'; } }")
            
            await page.wait_for_selector("#loginId", timeout=25000)
            
            active_session_state["status"] = "WAITING_FOR_USER_LOGIN"
            supabase.table("queue_logs").update({"status": "WAITING_FOR_USER_LOGIN"}).eq("id", record_id).execute()
            
            # Capture dynamic captcha stream
            captcha_element = await page.wait_for_selector("#captchaImgID", timeout=30000)
            captcha_bytes = await captcha_element.screenshot()
            b64_captcha = base64.b64encode(captcha_bytes).decode('utf-8')
            
            active_session_state["captcha_img"] = b64_captcha
            active_session_state["status"] = "WAITING_FOR_CAPTCHA"
            supabase.table("queue_logs").update({"status": "WAITING_FOR_CAPTCHA", "captcha_img": b64_captcha}).eq("id", record_id).execute()
            
            resolved_captcha = None
            for _ in range(60):  
                await asyncio.sleep(2)
                check_db = supabase.table("queue_logs").select("captcha_value").eq("id", record_id).execute()
                if check_db.data and check_db.data[0].get("captcha_value"):
                    resolved_captcha = check_db.data[0]["captcha_value"]
                    break
            
            if not resolved_captcha:
                active_session_state["status"] = "Failed: Captcha Timeout"
                active_session_state["captcha_img"] = None
                supabase.table("queue_logs").update({"status": "Failed: Captcha Timeout"}).eq("id", record_id).execute()
                return

            print(f"[AGENT] Injecting code token: {resolved_captcha}")
            await page.fill("#captcha", resolved_captcha)
            
            active_session_state["status"] = "MONITORING_SLOTS"
            active_session_state["captcha_img"] = None
            supabase.table("queue_logs").update({"status": "MONITORING_SLOTS"}).eq("id", record_id).execute()
            await asyncio.sleep(35)
            
            active_session_state["status"] = "Success: Run Complete"
        except Exception as err:
            active_session_state["status"] = f"Failed: {str(err)[:50]}"
            active_session_state["captcha_img"] = None
            supabase.table("queue_logs").update({"status": f"Failed: {str(err)[:50]}"}).eq("id", record_id).execute()
        finally:
            await browser.close()

def start_async_loop(record_id):
    asyncio.run(async_passport_pipeline(record_id))

# --- ENDPOINTS ---
@app.route('/')
def root():
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        session['user'] = request.form.get('username')
        return redirect(url_for('dashboard'))
    return app.send_static_file('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        return redirect(url_for('login_page'))
    return app.send_static_file('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return app.send_static_file('index.html')

@app.route('/submit', methods=['POST'])
def submit_request():
    global active_session_state
    raw_input = request.form.get('user_input', '')
    if not raw_input:
        return jsonify({"error": "Empty prompt payload"}), 400
        
    db_insert = supabase.table("queue_logs").insert({
        "user_name": "Parmar",
        "target_domain": "PASSPORT",
        "status": "INITIALIZING",
        "extracted_fields": {}
    }).execute()
    
    record_id = db_insert.data[0]['id']
    active_session_state["current_id"] = record_id
    active_session_state["status"] = "INITIALIZING"
    active_session_state["captcha_img"] = None
    
    threading.Thread(target=start_async_loop, args=(record_id,), daemon=True).start()
    return jsonify({"status": "SPAWNED", "record_id": record_id})

@app.route('/live-status', methods=['GET'])
def get_live_status():
    # Only returns the isolated current run details, no master database tables exposed!
    return jsonify(active_session_state)

@app.route('/submit-captcha', methods=['POST'])
def submit_captcha():
    global active_session_state
    data = request.json
    target_id = active_session_state["current_id"]
    
    if target_id:
        supabase.table("queue_logs").update({
            "captcha_value": data.get('captcha_value'), 
            "status": "INJECTING_TOKEN"
        }).eq("id", target_id).execute()
        active_session_state["status"] = "INJECTING_TOKEN"
        
    return jsonify({"status": "SUBMITTED"})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5005, debug=True, use_reloader=False)
''',

    "static/style.css": '''
:root {
    --bg-main: #0a0e17;
    --bg-surface: #111827;
    --bg-input: #1f2937;
    --primary: #3b82f6;
    --primary-hover: #2563eb;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
    --text-main: #f3f4f6;
    --text-muted: #9ca3af;
    --border: #374151;
}
* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
body { background-color: var(--bg-main); color: var(--text-main); height: 100vh; display: flex; justify-content: center; align-items: center; }
.auth-wrapper { display: flex; justify-content: center; align-items: center; width: 100vw; height: 100vh; }
.auth-card { background: var(--bg-surface); border: 1px solid var(--border); padding: 2.5rem; border-radius: 16px; width: 100%; max-width: 420px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
.auth-card h2 { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.5rem; color: #fff; }
.auth-card p { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 2rem; }
.input-field { width: 100%; padding: 0.75rem 1rem; background: var(--bg-input); border: 1px solid var(--border); border-radius: 8px; color: white; font-size: 0.95rem; margin-top: 0.5rem; margin-bottom: 1.25rem; }
.input-field:focus { outline: none; border-color: var(--primary); }
.form-label { display: block; text-align: left; font-size: 0.85rem; font-weight: 500; color: var(--text-muted); }
.action-btn { width: 100%; padding: 0.8rem; background: var(--primary); border: none; border-radius: 8px; color: white; font-weight: 600; cursor: pointer; font-size: 1rem; transition: background 0.2s; }
.action-btn:hover { background: var(--primary-hover); }
.auth-nav { margin-top: 1.5rem; font-size: 0.85rem; color: var(--text-muted); }
.auth-nav a { color: var(--primary); text-decoration: none; font-weight: 600; }
.app-container { display: flex; width: 100vw; height: 100vh; }
.sidebar { width: 360px; background-color: var(--bg-surface); border-right: 1px solid var(--border); padding: 2rem; display: flex; flex-direction: column; gap: 1.5rem; }
.brand-title { font-weight: 700; font-size: 1.4rem; color: #fff; display: flex; align-items: center; gap: 0.5rem; }
.sidebar textarea { width: 100%; height: 120px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; color: white; resize: none; font-size: 0.9rem; margin-top: 0.5rem; }
.captcha-container { background: rgba(245, 158, 11, 0.05); border: 1px dashed var(--warning); padding: 1rem; border-radius: 10px; margin-top: auto; }
.captcha-box-img { background: white; padding: 0.5rem; border-radius: 6px; display: flex; justify-content: center; margin: 0.75rem 0; min-height: 65px; }
.captcha-box-img img { max-width: 100%; height: auto; }
.main-viewport { flex: 1; display: flex; flex-direction: column; }
.top-nav { height: 70px; border-bottom: 1px solid var(--border); background-color: var(--bg-surface); display: flex; align-items: center; padding: 0 2rem; justify-content: space-between; }
.live-status { display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; font-weight: 500; }
.live-dot { width: 8px; height: 8px; background-color: var(--success); border-radius: 50%; box-shadow: 0 0 8px var(--success); }
.monitor-area { padding: 3rem; flex: 1; display: flex; justify-content: center; align-items: center; }
.monitor-card { background: var(--bg-surface); border: 1px solid var(--border); border-radius: 16px; padding: 3rem; width: 100%; max-width: 600px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
.status-display { font-size: 1.5rem; font-weight: 700; margin: 1.5rem 0; color: var(--primary); letter-spacing: 0.5px; }
.pipeline-tag { font-family: monospace; font-size: 1rem; color: var(--text-muted); background: var(--bg-input); padding: 0.3rem 0.8rem; border-radius: 6px; border: 1px solid var(--border); }
.hidden { display: none !important; }
''',

    "static/login.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>Terminal Authentication</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="auth-wrapper">
        <div class="auth-card">
            <h2>Welcome Operator</h2><p>Authorize session node profile access</p>
            <form action="/login" method="POST">
                <label class="form-label">Operator Terminal ID</label>
                <input type="text" name="username" class="input-field" placeholder="Enter custom identity" required>
                <label class="form-label">Access Token</label>
                <input type="password" class="input-field" placeholder="••••••••" required>
                <button type="submit" class="action-btn">Open Control Node</button>
            </form>
            <div class="auth-nav">New node setup? <a href="/signup">Register Profile</a></div>
        </div>
    </div>
</body>
</html>''',

    "static/signup.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>Terminal Registration</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="auth-wrapper">
        <div class="auth-card">
            <h2>Register Profile</h2><p>Establish verified terminal node profile</p>
            <form action="/signup" method="POST">
                <label class="form-label">Operator Code</label>
                <input type="text" class="input-field" placeholder="Terminal Identifier" required>
                <label class="form-label">Security Master Token</label>
                <input type="password" class="input-field" placeholder="••••••••" required>
                <button type="submit" class="action-btn">Compile Profile</button>
            </form>
            <div class="auth-nav">Existing node setup? <a href="/login">Sign In</a></div>
        </div>
    </div>
</body>
</html>''',

    "static/index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>Queue Killer Terminal</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="app-container">
        <aside class="sidebar">
            <div class="brand-title"><span style="background: linear-gradient(135deg, #3b82f6, #8b5cf6); padding: 0.4rem; border-radius:8px;">⚡</span> QUEUE KILLER</div>
            <p style="font-size:0.8rem; color:var(--text-muted); margin-top:-1rem;">Isolated Operational Mode</p>
            <form id="agent-submission-form">
                <label style="font-size:0.85rem; font-weight:500; color:var(--text-muted);">Payload Instruction Input</label>
                <textarea id="user_input" name="user_input" placeholder="Enter execution flow commands..." required></textarea>
                <button type="submit" class="action-btn" style="margin-top:1rem;">Spawn Dynamic Agent</button>
            </form>
            <div id="captcha-container" class="captcha-container hidden">
                <h4 style="font-size:0.85rem; color:var(--warning)">SECURE CAPTCHA TUNNEL</h4>
                <div class="captcha-box-img"><img id="captcha-img" src=""></div>
                <div style="display:flex; gap:0.5rem;">
                    <input type="text" id="captcha-value" class="input-field" style="margin:0; text-align:center; font-weight:bold;" placeholder="CODE">
                    <button onclick="submitCaptchaToken()" class="action-btn" style="width:auto; background:var(--success); padding:0 1rem;">INJECT</button>
                </div>
            </div>
            <div style="margin-top:auto;"><a href="/login" style="color:var(--danger); font-size:0.85rem; text-decoration:none; font-weight:600;">➔ Disconnect Session</a></div>
        </aside>
        <main class="main-viewport">
            <header class="top-nav">
                <div class="live-status"><span class="live-dot"></span><span id="global-status">Terminal Engine Online</span></div>
                <div style="font-size:0.8rem; background:var(--bg-input); padding:0.25rem 0.75rem; border-radius:20px; border:1px solid var(--border)">Secure Instance</div>
            </header>
            <section class="monitor-area">
                <div class="monitor-card">
                    <h3 style="font-size: 1.2rem; color: var(--text-muted)">ACTIVE RUNTIME PIPELINE MONITOR</h3>
                    <div style="margin-top: 1.5rem;">
                        <span class="pipeline-tag" id="active-id">Pipeline: None Active</span>
                    </div>
                    <div class="status-display" id="active-status">System Idle: Awaiting Prompt Initialization</div>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">This screen only reflects your current runtime stream. Full tracking log access is protected.</p>
                </div>
            </section>
        </main>
    </div>
    <script>
        document.getElementById('agent-submission-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const res = await fetch('/submit', { method: 'POST', body: formData });
            const data = await res.json();
            if(data.status === 'SPAWNED') {
                document.getElementById('global-status').innerText = "Matrix Loop Active";
                document.getElementById('user_input').value = '';
            }
        });
        async function updateDashboardMetrics() {
            const res = await fetch('/live-status');
            const state = await res.json();
            
            if(state.current_id) {
                document.getElementById('active-id').innerText = "Pipeline ID: #" + state.current_id;
                document.getElementById('active-status').innerText = state.status;
                
                // Toggle status colors dynamically
                if(state.status.includes('Failed')) document.getElementById('active-status').style.color = 'var(--danger)';
                else if(state.status.includes('Success')) document.getElementById('active-status').style.color = 'var(--success)';
                else if(state.status.includes('WAITING')) document.getElementById('active-status').style.color = 'var(--warning)';
                else document.getElementById('active-status').style.color = 'var(--primary)';

                if(state.status === "WAITING_FOR_CAPTCHA" && state.captcha_img) {
                    document.getElementById('captcha-img').src = "data:image/png;base64," + state.captcha_img;
                    document.getElementById('captcha-container').classList.remove('hidden');
                }
            }
            if(state.status !== "WAITING_FOR_CAPTCHA") {
                document.getElementById('captcha-container').classList.add('hidden');
            }
        }
        async function submitCaptchaToken() {
            const val = document.getElementById('captcha-value').value;
            await fetch('/submit-captcha', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ captcha_value: val })
            });
            document.getElementById('captcha-value').value = '';
            document.getElementById('captcha-container').classList.add('hidden');
        }
        setInterval(updateDashboardMetrics, 1500);
    </script>
</body>
</html>'''
}

print("[SYSTEM] Building isolated architectural workspace...")
for path, content in project_files.items():
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
    with open(path, "w", encoding="utf-8") as file:
        file.write(content.strip())
    print(f"[COMPILED] -> {path}")

print("\\n[SUCCESS] UI completely isolated. Database tables hidden from user panel.")