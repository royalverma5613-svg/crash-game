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
SENDER_EMAIL = "your_email@gmail.com"  # Apna Gmail yahan dalein
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

# ==========================================
# 🌐 FRONTEND HTML/JS
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Super 100x</title>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; background-color: #f4f5f7; color: #333; overflow-x: hidden; }
        .screen { display: none; min-height: 100vh; padding-bottom: 70px; background: #f4f5f7;}
        .active-screen { display: block; }
        
        .blue-header { background: #4a88ff; color: white; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; position: sticky; top: 0; z-index: 50; display: flex; justify-content: space-between; align-items: center;}
        .red-header { background: #e74c3c; color: white; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; position: sticky; top: 0; z-index: 50; display: flex; justify-content: space-between; align-items: center;}
        
        .btn-blue { background: #4a88ff; color: white; width: 100%; padding: 12px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .btn-blue:disabled { background: #a0c1ff; cursor: not-allowed; }
        .btn-grey { background: #e0e0e0; color: #333; width: 100%; padding: 12px; border: none; border-radius: 6px; font-size: 14px; font-weight: bold; cursor: pointer; }
        .btn-grey:disabled { background: #f0f0f0; color: #aaa; cursor: not-allowed; }

        .card { background: white; margin: 15px; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .input-group { margin-bottom: 15px; }
        .input-group label { font-size: 14px; font-weight: bold; color: #555; }
        .input-group input { width: 90%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; margin-top: 5px; outline: none;}
        
        .auth-tabs { display: flex; justify-content: space-around; margin-bottom: 20px; border-bottom: 2px solid #eee; }
        .auth-tab { padding: 10px 20px; font-weight: bold; color: #888; cursor: pointer; }
        .auth-tab.active { color: #4a88ff; border-bottom: 3px solid #4a88ff; }
        
        .bottom-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #ddd; z-index: 100; }
        .nav-item { text-align: center; font-size: 12px; color: #888; cursor: pointer; width: 25%; }
        .nav-item.active { color: #4a88ff; font-weight: bold; }

        .custom-popup { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center; }
        .popup-content { background: white; width: 80%; max-width: 300px; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .popup-btn { background: #4a88ff; color: white; padding: 8px 20px; border: none; border-radius: 6px; margin-top: 15px; font-weight: bold; cursor: pointer; }

        .history-bar { display: flex; gap: 5px; padding: 10px; overflow-x: auto; background: white; border-bottom: 1px solid #eee;}
        .pill { padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; min-width:35px; text-align:center;}
        .pill.blue { background: #4a88ff; } .pill.green { background: #2ecc71; } .pill.red { background: #e74c3c; }
        .game-container { position: relative; width: 100%; height: 250px; background: #eef3f9; overflow: hidden; border-bottom: 2px solid #ddd;}
        .aviator-bg { background: #1a1a24; }
        canvas { display: block; width: 100%; height: 100%; }
        .center-text { position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); text-align: center; pointer-events: none;}
        .timer-text { font-size: 50px; font-weight: bold; color: #333; margin: 0; line-height: 1;}
        .aviator-text { color: white; }
        
        .live-bets { background: white; margin-top: 10px; padding: 15px; font-size: 14px; }
        .bets-header { display: flex; justify-content: space-between; font-weight: bold; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 10px; }
        .bet-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f4f5f7; }
        .bet-row div { width: 25%; text-align: center; }
        .bet-row div:first-child { text-align: left; }
        .bet-row div:last-child { text-align: right; }
        .text-green { color: #2ecc71; font-weight: bold; }
        .text-red { color: #e74c3c; font-weight: bold; }
        .hidden { display: none !important; }
    </style>
</head>
<body>

    <div id="custom-popup" class="custom-popup">
        <div class="popup-content">
            <h3 id="popup-title" style="margin-top:0; color:#333;">Title</h3>
            <p id="popup-message" style="color:#666; font-size:14px;">Message</p>
            <button class="popup-btn" onclick="closePopup()">OK</button>
        </div>
    </div>

    <!-- 1. AUTH SCREEN -->
    <div id="auth-screen" class="screen active-screen">
        <h2 style="text-align: center; color: #4a88ff; margin-top: 50px;">Super100x</h2>
        <div class="card" style="padding: 10px 20px 30px 20px;">
            <div class="auth-tabs">
                <div class="auth-tab active" id="tab-login" onclick="toggleAuth('login')">LOGIN</div>
                <div class="auth-tab" id="tab-register" onclick="toggleAuth('register')">REGISTER</div>
            </div>
            
            <div id="form-login">
                <div class="input-group"><label>Email</label><br><input type="email" id="login-email"></div>
                <div class="input-group"><label>Password</label><br><input type="password" id="login-pass"></div>
                <button class="btn-blue" onclick="verifyLogin()">LOGIN</button>
            </div>

            <div id="form-register" class="hidden">
                <div id="reg-step-1">
                    <div class="input-group">
                        <label>Email Address</label><br>
                        <input type="email" id="reg-email" placeholder="Enter valid email">
                        <button id="btn-send-otp" class="btn-grey" style="margin-top:10px;" onclick="sendEmailOTP()">Send OTP to Email</button>
                    </div>
                    
                    <div id="otp-section" class="hidden">
                        <div class="input-group">
                            <label>Email OTP</label><br>
                            <input type="number" id="reg-otp" placeholder="Enter 4-digit code">
                        </div>
                        <button class="btn-blue" onclick="verifyOTP()">Verify OTP</button>
                    </div>
                </div>

                <div id="reg-step-2" class="hidden">
                    <div style="background: #eef3f9; padding: 10px; border-radius:6px; margin-bottom:15px; color:#2ecc71; font-weight:bold; text-align:center;">
                        ✅ Email Verified Successfully!
                    </div>
                    <div class="input-group"><label>Create Password</label><br><input type="password" id="reg-pass" placeholder="Min 6 characters"></div>
                    <div class="input-group"><label>Referral Code (Optional)</label><br><input type="text" id="reg-ref" placeholder="Optional"></div>
                    <button class="btn-blue" onclick="finalRegister()">COMPLETE REGISTRATION</button>
                </div>
            </div>
        </div>
    </div>

    <!-- 2. HOME SCREEN -->
    <div id="home-screen" class="screen">
        <div style="padding: 15px; display: flex; justify-content: space-between; align-items: center; background: white;">
            <b>ID: <span class="user-uid">Loading...</span></b>
            <span style="background: #eef3f9; padding: 5px 10px; border-radius: 20px;">🪙 App</span>
        </div>
        <div class="card">
            <div style="color: #888;">Balance</div><h1 style="margin: 5px 0;">₹ <span class="user-bal">0.00</span></h1>
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button class="btn-blue" style="border-radius: 20px;" onclick="switchScreen('recharge-screen')">Recharge</button>
                <button class="btn-blue" style="background: white; color: #333; border: 1px solid #ccc; border-radius: 20px;" onclick="switchScreen('withdraw-screen')">Withdraw</button>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px;">
            <div class="card" style="margin:0; text-align:center; padding: 30px 10px; cursor:pointer; border: 2px solid #4a88ff;" onclick="switchScreen('crash-screen')">
                <div style="font-size: 40px; margin-bottom:10px;">🚀</div><b>Crash (12s)</b>
            </div>
            <div class="card" style="margin:0; text-align:center; padding: 30px 10px; cursor:pointer; border: 2px solid #e74c3c;" onclick="switchScreen('aviator-screen')">
                <div style="font-size: 40px; margin-bottom:10px;">✈️</div><b>Aviator (8s)</b>
            </div>
        </div>
    </div>

    <!-- 3. GAMES -->
    <div id="crash-screen" class="screen">
        <div class="blue-header"><span onclick="switchScreen('home-screen')" style="cursor:pointer; font-size:22px;">❮</span> Crash <span></span></div>
        <div class="history-bar" id="crash-history"></div>
        <div class="game-container">
            <canvas id="crashCanvas"></canvas>
            <div class="center-text">
                <div id="crash-title" style="font-weight:bold; color:#888;">Next round in</div>
                <div id="crash-display" class="timer-text">12.0s</div>
            </div>
        </div>
        <div class="live-bets">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px; color:#888;"><span>Players: <b id="crash-players">0</b></span><span>Total Bet: <b id="crash-totalamt">₹0</b></span></div>
            <div class="bets-header"><div>User</div><div>Bet</div><div>Mult</div><div>Profit</div></div>
            <div id="crash-orders"></div>
        </div>
    </div>

    <div id="aviator-screen" class="screen">
        <div class="red-header"><span onclick="switchScreen('home-screen')" style="cursor:pointer; font-size:22px;">❮</span> Aviator <span></span></div>
        <div class="history-bar" id="aviator-history"></div>
        <div class="game-container aviator-bg">
            <canvas id="aviatorCanvas"></canvas>
            <div class="center-text">
                <div id="aviator-title" style="font-weight:bold; color:#aaa;">Next round in</div>
                <div id="aviator-display" class="timer-text aviator-text">8.0s</div>
            </div>
        </div>
        <div class="live-bets">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px; color:#888;"><span>Players: <b id="aviator-players">0</b></span><span>Total Bet: <b id="aviator-totalamt">₹0</b></span></div>
            <div class="bets-header"><div>User</div><div>Bet</div><div>Mult</div><div>Profit</div></div>
            <div id="aviator-orders"></div>
        </div>
    </div>

    <!-- OTHER SCREENS -->
    <div id="recharge-screen" class="screen">
        <div class="blue-header"><span onclick="switchScreen('home-screen')">❮</span> Recharge <span></span></div>
        <div class="card"><h3>Recharge Gateway Offline</h3></div>
    </div>
    
    <div id="withdraw-screen" class="screen">
        <div class="blue-header"><span onclick="switchScreen('home-screen')">❮</span> Withdraw <span></span></div>
        <div class="card"><h2>₹ <span class="user-bal">0.00</span></h2></div>
    </div>

    <div id="invite-screen" class="screen">
        <div class="blue-header" style="justify-content: center;">Invite & Earn</div>
        <div class="card" style="text-align: center;"><p id="invite-link-text" style="background: #eef3f9; padding: 10px; font-weight:bold; color:#4a88ff;">Loading...</p></div>
    </div>

    <div id="profile-screen" class="screen">
        <div style="background: #4a88ff; padding: 40px 20px 20px 20px; color: white; display: flex; align-items: center; gap: 15px; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;">
            <div style="width: 60px; height: 60px; background: white; border-radius: 50%; display:flex; justify-content:center; align-items:center; font-size: 30px;">👤</div>
            <div><h3 id="profile-email" style="margin:0 0 5px 0;"></h3><div style="font-size:14px; background:rgba(0,0,0,0.2); padding:2px 10px; border-radius:10px;">ID: <span class="user-uid"></span></div></div>
        </div>
        <div class="card" style="padding:0; overflow:hidden; margin-top:20px;">
            <div style="padding: 15px 20px; font-weight: bold; color: #e74c3c; text-align: center; cursor:pointer;" onclick="logout()">Log Out</div>
        </div>
    </div>

    <div class="bottom-nav" id="bottom-nav" style="display: none;">
        <div class="nav-item active" onclick="switchScreen
