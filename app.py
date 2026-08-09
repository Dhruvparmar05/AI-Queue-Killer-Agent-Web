import sqlite3
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from playwright.sync_api import sync_playwright

app = Flask(__name__)
app.secret_key = "queue_killer_production_super_key_2026"
DB_NAME = "queue_killer.db"

# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# REAL GOVERNMENT PORTAL AUTOMATION AGENT
# ---------------------------------------------------------
class QueueKillerAgent:
    @staticmethod
    def execute_task(portal, service, input_data):
        try:
            with sync_playwright() as p:
                # Launching Chromium in non-headless mode for visibility
                browser = p.chromium.launch(
                    headless=False,
                    args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
                )
                context = browser.new_context(viewport=None)
                page = context.new_page()
                page.set_default_timeout(60000)

                # =========================================
                # 1. PASSPORT SEVA OFFICIAL SERVICES
                # =========================================
                if portal == "passport":
                    if service == "check_appointment":
                        page.goto("https://www.passportindia.gov.in/AppOnlineProject/statusTracker/checkAppointmentAvailabity", wait_until="domcontentloaded")
                    elif service == "track_status":
                        page.goto("https://www.passportindia.gov.in/AppOnlineProject/statusTracker/trackStatusInpNew", wait_until="domcontentloaded")
                        if input_data and page.is_visible("input[name='fileNo']"):
                            page.fill("input[name='fileNo']", input_data)
                    elif service == "fresh_passport":
                        page.goto("https://www.passportindia.gov.in/AppOnlineProject/user/registrationBaseAction?request_locale=en", wait_until="domcontentloaded")
                    elif service == "locate_psk":
                        page.goto("https://www.passportindia.gov.in/AppOnlineProject/online/locatePSKInp", wait_until="domcontentloaded")
                    elif service == "fee_calculator":
                        page.goto("https://www.passportindia.gov.in/AppOnlineProject/fee/feeCalInp", wait_until="domcontentloaded")
                    else:
                        page.goto("https://www.passportindia.gov.in/AppOnlineProject/welcomeLink", wait_until="domcontentloaded")

                # =========================================
                # 2. PARIVAHAN RTO SERVICES (SARATHI / VAHAN)
                # =========================================
                elif portal == "rto":
                    if service == "pay_echallan":
                        page.goto("https://echallan.parivahan.gov.in/", wait_until="domcontentloaded")
                        if input_data and page.is_visible("input[name='challanNo']"):
                            page.fill("input[name='challanNo']", input_data)
                    elif service in ["ll_slot", "dl_slot"]:
                        page.goto("https://sarathi.parivahan.gov.in/slots/slotBooking.do", wait_until="domcontentloaded")
                        if input_data and page.is_visible("input[name='applNum']"):
                            page.fill("input[name='applNum']", input_data)
                    elif service == "rc_status":
                        page.goto("https://vahan.parivahan.gov.in/nrservices/faces/user/citizen/citizenlogin.xhtml", wait_until="domcontentloaded")
                    elif service == "hser_plate":
                        page.goto("https://bookmyhsrp.com/", wait_until="domcontentloaded")
                    else:
                        page.goto("https://sarathi.parivahan.gov.in/sarathiservice/stateSelection.do", wait_until="domcontentloaded")

                # =========================================
                # 3. ORS MEDICAL & DIGITAL GUJARAT
                # =========================================
                elif portal == "ors":
                    if service == "lab_reports":
                        page.goto("https://ors.gov.in/orsportal/report.jsp", wait_until="domcontentloaded")
                    else:
                        page.goto("https://ors.gov.in/orsportal/", wait_until="domcontentloaded")

                elif portal == "digital_gujarat":
                    if service == "scholarship_status":
                        page.goto("https://www.digitalgujarat.gov.in/Scholarship.aspx", wait_until="domcontentloaded")
                    else:
                        page.goto("https://www.digitalgujarat.gov.in/", wait_until="domcontentloaded")

                # Keep browser open briefly so the operation is clearly visible
                page.wait_for_timeout(7000)
                browser.close()
                return True, f"Automation successfully completed for {service.upper()}."

        except Exception as e:
            return False, f"Process Note: {str(e)[:100]}"

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)", (fullname, email, password))
            conn.commit()
            conn.close()
            flash("Account registered successfully! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email is already registered!", "danger")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email address or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/run-agent", methods=["POST"])
def run_agent():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    portal = request.form.get("portal")
    service = request.form.get("service")
    input_data = request.form.get("input_data", "")

    success, msg = QueueKillerAgent.execute_task(portal, service, input_data)
    flash(msg, "success" if success else "warning")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True, port=8080)