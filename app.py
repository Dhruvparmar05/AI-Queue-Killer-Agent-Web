import base64
import json
import asyncio
import threading
import os
from flask import Flask, request, jsonify, redirect, url_for, session
from google import genai
from supabase import create_client, Client
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Initialize Environment Variable Engine
load_dotenv()

base_dir = os.path.abspath(os.path.dirname(__file__))
static_path = os.path.join(base_dir, 'static')

app = Flask(__name__, static_folder=static_path)
app.secret_key = os.getenv("FLASK_SECRET", "queue_killer_isolated_session_2026")

# Core Credentials Mapping fetched from secure local .env config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("[CRITICAL] Supabase environmental variables are missing! Check your .env setup.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Global in-memory state for the active runtime session only (Zero DB exposure to user UI)
active_session_state = {
    "current_id": None,
    "status": "System Idle",
    "captcha_img": None
}

# --- PLAYWRIGHT ASYNC PIPELINE ---
async def async_passport_pipeline(record_id):
    global active_session_state
    print(f"[AGENT] Spawning independent execution node for ID: {record_id}")
    
    async with async_playwright() as p:
        # headless=False and slow_mo to handle navigation safely
        browser = await p.chromium.launch(headless=False, slow_mo=800)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        
        try:
            active_session_state["status"] = "LAUNCHING_BROWSER"
            supabase.table("queue_logs").update({"status": "LAUNCHING_BROWSER"}).eq("id", record_id).execute()
            
            await page.goto("https://www.passportindia.gov.in/", timeout=60000, wait_until="load")
            
            # Dismiss Popup Advisory Box if present
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
            
            # Capture dynamic captcha stream directly from site wrapper
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

# --- APP NAVIGATION ROUTING LOGIC ---
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