from flask import Flask, jsonify, render_template_string, request
import random
import time
import threading
import sqlite3
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ==========================================
# 📧 GMAIL SMTP CONFIGURATION
# ==========================================
SENDER_EMAIL = "your_email@gmail.com"  # Yahan apna Gmail dalein
SENDER_PASSWORD = "mfoq cjkt eyub tuvu"  # Aapka App Password set hai

# ==========================================
# 💾 DATABASE SETUP
# ==========================================
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, uid TEXT, ref TEXT, balance REAL)''')
    conn.commit()
    conn.close()

init_db()
otp_storage = {}

# ==========================================
# ⚙ DUAL GAME ENGINE (CRASH & AVIATOR)
# ==========================================
SETTINGS = {"crash_active_users": 10000, "aviator_active_users": 100}
games = {
    "crash": {"status": "waiting", "multiplier": 1.0, "next_crash": 2.50, "time_left": 12.0, "history": [], "fake_bets": [], "total_amount": 0},
    "aviator": {"status": "waiting", "multiplier": 1.0, "next_crash": 3.00, "time_left": 8.0, "history": [], "fake_bets": [], "total_amount": 0}
}

def generate_fake_bets(num_users):
    bets = []
    display_users = min(num_users, 40) 
    total_amt = 0
    for _ in range(num_users): total_amt += random.choice([20, 50, 100, 200, 500, 1000, 5000])
    for _ in range(display_users):
        bets.append({"uid": f"{random.randint(10,99)}***{random.randint(10,99)}", "bet": random.choice([20, 50, 100, 200, 500, 1000]), "cashout_target": round(random.uniform(1.05, 5.50), 2), "cashed_out": False, "profit": 0, "stopped_at": 0})
    return bets, total_amt

def game_thread(game_name, wait_time):
    global games
    while True:
        games[game_name]["status"] = "waiting"
        games[game_name]["multiplier"] = 1.00
        games[game_name]["next_crash"] = round(random.uniform(1.05, 10.50), 2)
        users_count = SETTINGS[f"{game_name}_active_users"]
        games[game_name]["fake_bets"], games[game_name]["total_amount"] = generate_fake_bets(users_count)
        
        for i in range(int(wait_time * 10), -1, -1):
            games[game_name]["time_left"] = round(i / 10.0, 1)
            time.sleep(0.1)

        games[game_name]["status"] = "flying"
        current_mult = 1.00
        while current_mult < games[game_name]["next_crash"]:
            current_mult += (0.01 * current_mult) + 0.01 
            games[game_name]["multiplier"] = round(current_mult, 2)
            for b in games[game_name]["fake_bets"]:
                if not b["cashed_out"] and current_mult >= b["cashout_target"]:
                    b["cashed_out"] = True; b["stopped_at"] = b["cashout_target"]; b["profit"] = round(b["bet"] * b["cashout_target"], 2)
            time.sleep(0.05)

        games[game_name]["status"] = "crashed"
        games[game_name]["multiplier"] = games[game_name]["next_crash"]
        games[game_name]["history"].insert(0, games[game_name]["next_crash"])
        if len(games[game_name]["history"]) > 6: games[game_name]["history"].pop()
        time.sleep(4)

threading.Thread(target=game_thread, args=("crash", 12.0), daemon=True).start()
threading.Thread(target=game_thread, args=("aviator", 8.0), daemon=True).start()

# ==========================================
# 🌐 API ENDPOINTS (REAL OTP & AUTH)
# ==========================================
@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get('email')
    
    if not email or "@" not in email:
        return jsonify({"status": "error", "message": "Invalid email address"})

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    if c.fetchone():
        conn.close()
        return jsonify({"status": "error", "message": "Email already registered. Please login!"})
    conn.close()

    otp = str(random.randint(1000, 9999))
    otp_storage[email] = otp

    try:
        msg = MIMEText(f"Welcome to Super100x!\n\nYour Verification Code is: {otp}\n\nDo not share this code.")
        msg['Subject'] = 'Super100x - Verification OTP'
        msg['From'] = SENDER_EMAIL
        msg['To'] = email

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return jsonify({"status": "success", "message": "OTP sent! Check your Gmail inbox."})
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to send email. Check SMTP settings."})

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    
    if email in otp_storage and otp_storage[email] == otp:
        return jsonify({"status": "success", "message": "Email verified successfully!"})
    return jsonify({"status": "error", "message": "Invalid or incorrect OTP!"})

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    ref = data.get('ref', '')

    uid = str(random.randint(1000000, 9999999))
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (email, password, uid, ref, balance) VALUES (?, ?, ?, ?, ?)", 
              (email, password, uid, ref, 50.00))
    conn.commit()
    conn.close()
    
    if email in otp_storage: del otp_storage[email]
    return jsonify({"status": "success", "message": "Account created! ₹50 Bonus added.", "uid": uid, "balance": 50.00})

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    c.execute("SELECT uid, balance FROM users WHERE email=? AND password=?", (email, password))
    user = c.fetchone(); conn.close()
    if user: return jsonify({"status": "success", "message": "Login successful!", "uid": user[0], "balance": user[1]})
    return jsonify({"status": "error", "message": "Incorrect Email or Password!"})

@app.route('/api/game_state/<game_name>')
def get_state(game_name):
    if game_name in games:
        data = dict(games[game_name])
        data["active_users"] = SETTINGS[f"{game_name}_active_users"]
        return jsonify(data)
    return jsonify({"error": "game not found"})
                    
