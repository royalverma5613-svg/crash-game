from flask import Flask, jsonify, render_template_string, request
import random
import time
import threading
import sqlite3
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ==========================================
# 📧 EMAIL SETTINGS (Apni Details Dalein)
# ==========================================
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"

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
# Bot settings for fake users
SETTINGS = {
    "crash_active_users": 10000,
    "aviator_active_users": 100
}

games = {
    "crash": {"status": "waiting", "multiplier": 1.0, "next_crash": 2.50, "time_left": 12.0, "history": [], "fake_bets": [], "total_amount": 0},
    "aviator": {"status": "waiting", "multiplier": 1.0, "next_crash": 3.00, "time_left": 8.0, "history": [], "fake_bets": [], "total_amount": 0}
}

def generate_fake_bets(num_users):
    bets = []
    # Server lag na ho isliye screen par dikhane ke liye sirf top 30-40 bets generate karenge
    display_users = min(num_users, 40) 
    total_amt = 0
    
    for _ in range(num_users):
        amt = random.choice([20, 50, 100, 200, 500, 1000, 5000])
        total_amt += amt
        
    for _ in range(display_users):
        bets.append({
            "uid": f"{random.randint(10,99)}***{random.randint(10,99)}",
            "bet": random.choice([20, 50, 100, 200, 500, 1000]),
            "cashout_target": round(random.uniform(1.05, 5.50), 2),
            "cashed_out": False,
            "profit": 0,
            "stopped_at": 0
        })
    return bets, total_amt

def game_thread(game_name, wait_time):
    global games
    while True:
        # WAITING PHASE
        games[game_name]["status"] = "waiting"
        games[game_name]["multiplier"] = 1.00
        games[game_name]["next_crash"] = round(random.uniform(1.05, 10.50), 2)
        
        # Generate Fake Bets based on bot settings
        users_count = SETTINGS[f"{game_name}_active_users"]
        games[game_name]["fake_bets"], games[game_name]["total_amount"] = generate_fake_bets(users_count)
        
        for i in range(int(wait_time * 10), -1, -1):
            games[game_name]["time_left"] = round(i / 10.0, 1)
            time.sleep(0.1)

        # FLYING PHASE
        games[game_name]["status"] = "flying"
        current_mult = 1.00
        while current_mult < games[game_name]["next_crash"]:
            current_mult += (0.01 * current_mult) + 0.01 
            games[game_name]["multiplier"] = round(current_mult, 2)
            
            # Fake users cashing out dynamically
            for b in games[game_name]["fake_bets"]:
                if not b["cashed_out"] and current_mult >= b["cashout_target"]:
                    b["cashed_out"] = True
                    b["stopped_at"] = b["cashout_target"]
                    b["profit"] = round(b["bet"] * b["cashout_target"], 2)
            time.sleep(0.05)

        # CRASHED PHASE
        games[game_name]["status"] = "crashed"
        games[game_name]["multiplier"] = games[game_name]["next_crash"]
        
        games[game_name]["history"].insert(0, games[game_name]["next_crash"])
        if len(games[game_name]["history"]) > 6:
            games[game_name]["history"].pop()
            
        time.sleep(4)

# Start both games independently
threading.Thread(target=game_thread, args=("crash", 12.0), daemon=True).start()
threading.Thread(target=game_thread, args=("aviator", 8.0), daemon=True).start()


# ==========================================
# 🌐 API ENDPOINTS (Auth, Settings, Game)
# ==========================================
@app.route('/api/bot_settings', methods=['POST'])
def bot_settings():
    data = request.json
    if "crash" in data: SETTINGS["crash_active_users"] = int(data["crash"])
    if "aviator" in data: SETTINGS["aviator_active_users"] = int(data["aviator"])
    return jsonify({"status": "success"})

@app.route('/api/game_state/<game_name>')
def get_state(game_name):
    if game_name in games:
        # Also return active user count
        data = dict(games[game_name])
        data["active_users"] = SETTINGS[f"{game_name}_active_users"]
        return jsonify(data)
    return jsonify({"error": "game not found"})

@app.route('/api/change_password', methods=['POST'])
def change_pass():
    data = request.json
    email = data.get('email')
    old_p = data.get('old_pass')
    new_p = data.get('new_pass')
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE email=?", (email,))
    row = c.fetchone()
    
    if row and row[0] == old_p:
        c.execute("UPDATE users SET password=? WHERE email=?", (new_p, email))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Password changed successfully!"})
    conn.close()
    return jsonify({"status": "error", "message": "Incorrect old password."})

# (Keep /api/send_otp, /api/register, /api/login SAME AS BEFORE. Mapped briefly for space)
@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    data = request.json; email = data.get('email'); otp = str(random.randint(1000, 9999)); otp_storage[email] = otp
    try:
        msg = MIMEText(f"Your OTP is: {otp}"); msg['Subject'] = 'Super100x Registration OTP'; msg['From'] = SENDER_EMAIL; msg['To'] = email
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(SENDER_EMAIL, SENDER_PASSWORD); server.send_message(msg); server.quit()
        return jsonify({"status": "success", "message": "OTP sent!"})
    except: return jsonify({"status": "error", "message": "Failed to send email."})

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json; email = data.get('email'); otp = data.get('otp'); password = data.get('password')
    if email not in otp_storage or otp_storage[email] != otp: return jsonify({"status": "error", "message": "Invalid OTP!"})
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    if c.fetchone(): return jsonify({"status": "error", "message": "Email already registered!"})
    uid = str(random.randint(1000000, 9999999))
    c.execute("INSERT INTO users (email, password, uid, ref, balance) VALUES (?, ?, ?, ?, ?)", (email, password, uid, data.get('ref',''), 50.00))
    conn.commit(); conn.close(); del otp_storage[email]
    return jsonify({"status": "success", "message": "Account created! ₹50 Bonus.", "uid": uid, "balance": 50.00})

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json; email = data.get('email'); password = data.get('password')
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    c.execute("SELECT uid, balance FROM users WHERE email=? AND password=?", (email, password)); user = c.fetchone(); conn.close()
    if user: return jsonify({"status": "success", "message": "Login successful!", "uid": user[0], "balance": user[1]})
    return jsonify({"status": "error", "message": "Incorrect Email or Password!"})

# ==========================================
# 🌐 FRONTEND UI HTML/JS
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
        .btn-red { background: #e74c3c; color: white; width: 100%; padding: 12px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        
        .card { background: white; margin: 15px; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .input-group { margin-bottom: 15px; }
        .input-group input { width: 90%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; }
        
        .auth-tabs { display: flex; justify-content: space-around; margin-bottom: 20px; border-bottom: 2px solid #eee; }
        .auth-tab { padding: 10px 20px; font-weight: bold; color: #888; cursor: pointer; }
        .auth-tab.active { color: #4a88ff; border-bottom: 3px solid #4a88ff; }
        .bottom-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #ddd; z-index: 100; }
        .nav-item { text-align: center; font-size: 12px; color: #888; cursor: pointer; width: 25%; }
        .nav-item.active { color: #4a88ff; font-weight: bold; }

        .custom-popup { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center; }
        .popup-content { background: white; width: 80%; max-width: 300px; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); animation: pop 0.3s; }
        @keyframes pop { from {transform: scale(0.8); opacity: 0;} to {transform: scale(1); opacity: 1;} }
        .popup-btn { background: #4a88ff; color: white; padding: 8px 20px; border: none; border-radius: 6px; margin-top: 15px; font-weight: bold; cursor: pointer; }

        /* Game Elements */
        .history-bar { display: flex; gap: 5px; padding: 10px; overflow-x: auto; background: white; border-bottom: 1px solid #eee;}
        .pill { padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; }
        .pill.blue { background: #4a88ff; } .pill.green { background: #2ecc71; } .pill.red { background: #e74c3c; }
        .game-container { position: relative; width: 100%; height: 250px; background: #eef3f9; overflow: hidden; border-bottom: 2px solid #ddd;}
        .aviator-bg { background: #1a1a24; }
        canvas { display: block; width: 100%; height: 100%; }
        .center-text { position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); text-align: center; pointer-events: none;}
        .timer-text { font-size: 50px; font-weight: bold; color: #333; margin: 0; line-height: 1;}
        .aviator-text { color: white; }
        
        /* Live Bets Table */
        .live-bets { background: white; margin-top: 10px; padding: 15px; font-size: 14px; }
        .bets-header { display: flex; justify-content: space-between; font-weight: bold; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 10px; }
        .bet-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f4f5f7; }
        .bet-row div { width: 25%; text-align: center; }
        .bet-row div:first-child { text-align: left; }
        .bet-row div:last-child { text-align: right; }
        .text-green { color: #2ecc71; font-weight: bold; }
        .text-red { color: #e74c3c; font-weight: bold; }
        
    </style>
</head>
<body>

    <!-- POPUP -->
    <div id="custom-popup" class="custom-popup">
        <div class="popup-content">
            <h3 id="popup-title" style="margin-top:0; color:#333;">Title</h3>
            <p id="popup-message" style="color:#666; font-size:14px;">Message goes here.</p>
            <div id="popup-inputs" style="display:none; margin: 15px 0;"></div>
            <button class="popup-btn" id="popup-ok" onclick="closePopup()">OK</button>
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
                <button class="btn-blue" id="btn-login" onclick="verifyLogin()">LOGIN</button>
            </div>
            <div id="form-register" style="display:none;">
                <div class="input-group"><label>Email</label><br><input type="email" id="reg-email">
                    <button style="background: #e0e0e0; padding: 10px; border: none; border-radius: 6px; margin-top: 10px; width:100%; cursor:pointer;" onclick="sendEmailOTP()">Send OTP to Email</button>
                </div>
                <div class="input-group"><label>Email OTP</label><br><input type="number" id="reg-otp"></div>
                <div class="input-group"><label>Password</label><br><input type="password" id="reg-pass"></div>
                <div class="input-group"><label>Referral Code</label><br><input type="text" id="reg-ref"></div>
                <button class="btn-blue" id="btn-register" onclick="verifyRegister()">REGISTER</button>
            </div>
        </div>
    </div>

    <!-- 2. HOME SCREEN -->
    <div id="home-screen" class="screen">
        <div style="padding: 15px; display: flex; justify-content: space-between; align-items: center; background: white;">
            <b>ID: <span class="user-uid">Loading...</span></b>
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

    <!-- 3. CRASH GAME SCREEN (BLUE) -->
    <div id="crash-screen" class="screen">
        <div class="blue-header"><span onclick="switchScreen('home-screen')" style="cursor:pointer; font-size:22px;">❮</span> Crash <span style="font-size:14px; cursor:pointer;">Rule ❓</span></div>
        <div class="history-bar" id="crash-history"></div>
        <div class="game-container">
            <canvas id="crashCanvas"></canvas>
            <div class="center-text">
                <div id="crash-title" style="font-weight:bold; color:#888;">Next round in</div>
                <div id="crash-display" class="timer-text">12.0s</div>
            </div>
        </div>
        <div style="background: white; padding: 15px; border-bottom: 2px solid #eee;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;"><div style="color:#888;">Balance: ₹<span class="user-bal">0.00</span></div></div>
            <div style="display: flex; gap: 10px;"><input type="number" id="crash-bet" value="10" style="width: 60%; padding: 10px; border: 1px solid #ccc; border-radius: 5px;"><button class="btn-blue" style="width: 40%;" onclick="showPopup('Success', 'Bet Placed!')">START</button></div>
        </div>
        <!-- LIVE BETS TABLE -->
        <div class="live-bets">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px; color:#888;">
                <span>Players: <b id="crash-players">0</b></span>
                <span>Total Bet: <b id="crash-totalamt">₹0</b></span>
            </div>
            <div class="bets-header"><div>User</div><div>Bet</div><div>Mult</div><div>Profit</div></div>
            <div id="crash-orders"></div>
        </div>
    </div>

    <!-- 3. AVIATOR GAME SCREEN (RED) -->
    <div id="aviator-screen" class="screen">
        <div class="red-header"><span onclick="switchScreen('home-screen')" style="cursor:pointer; font-size:22px;">❮</span> Aviator <span style="font-size:14px; cursor:pointer;">Rule ❓</span></div>
        <div class="history-bar" id="aviator-history"></div>
        <div class="game-container aviator-bg">
            <canvas id="aviatorCanvas"></canvas>
            <div class="center-text">
                <div id="aviator-title" style="font-weight:bold; color:#aaa;">Next round in</div>
                <div id="aviator-display" class="timer-text aviator-text">8.0s</div>
            </div>
        </div>
        <div style="background: white; padding: 15px; border-bottom: 2px solid #eee;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;"><div style="color:#888;">Balance: ₹<span class="user-bal">0.00</span></div></div>
            <div style="display: flex; gap: 10px;"><input type="number" id="aviator-bet" value="10" style="width: 60%; padding: 10px; border: 1px solid #ccc; border-radius: 5px;"><button class="btn-red" style="width: 40%;" onclick="showPopup('Success', 'Bet Placed!')">START</button></div>
        </div>
        <!-- LIVE BETS TABLE -->
        <div class="live-bets">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px; color:#888;">
                <span>Players: <b id="aviator-players">0</b></span>
                <span>Total Bet: <b id="aviator-totalamt">₹0</b></span>
            </div>
            <div class="bets-header"><div>User</div><div>Bet</div><div>Mult</div><div>Profit</div></div>
            <div id="aviator-orders"></div>
        </div>
    </div>

    <!-- OTHER SCREENS (Recharge, Withdraw, Invite, Profile) -->
    <div id="recharge-screen" class="screen">
        <div class="blue-header"><span onclick="switchScreen('home-screen')">❮</span> Recharge <span></span></div>
        <div class="card">
            <h3>Select Amount</h3><input type="number" placeholder="Enter Amount" style="width: 90%; padding: 12px; border: 1px solid #ccc; margin-bottom:20px;">
            <button class="btn-blue" onclick="showPopup('Redirecting...', 'Connecting to Payment Gateway...')">Pay Now</button>
        </div>
    </div>
    
    <div id="withdraw-screen" class="screen">
        <div class="blue-header"><span onclick="switchScreen('home-screen')">❮</span> Withdraw <span></span></div>
        <div class="card">
            <h2>₹ <span class="user-bal">0.00</span></h2>
            <input type="text" placeholder="Enter UPI ID" style="width: 90%; padding: 12px; margin: 10px 0 20px 0;">
            <button class="btn-blue" onclick="showPopup('Error', 'Min withdrawal is ₹500')">Withdraw</button>
        </div>
    </div>

    <div id="invite-screen" class="screen">
        <div class="blue-header" style="justify-content: center;">Invite & Earn</div>
        <div class="card" style="text-align: center;">
            <p id="invite-link-text" style="background: #eef3f9; padding: 10px; font-weight:bold; color:#4a88ff;">Loading...</p>
            <button class="btn-blue" onclick="showPopup('Copied', 'Referral link copied!')">Copy Link</button>
        </div>
    </div>

    <!-- PROFILE WITH CHANGE PASSWORD -->
    <div id="profile-screen" class="screen">
        <div style="background: #4a88ff; padding: 40px 20px 20px 20px; color: white; display: flex; align-items: center; gap: 15px; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;">
            <div style="width: 60px; height: 60px; background: white; border-radius: 50%; display:flex; justify-content:center; align-items:center; font-size: 30px;">👤</div>
            <div>
                <h3 id="profile-email" style="margin:0 0 5px 0;"></h3>
                <div style="font-size:14px; background:rgba(0,0,0,0.2); padding:2px 10px; border-radius:10px;">ID: <span class="user-uid"></span></div>
            </div>
        </div>
        <div class="card" style="margin-top: -20px; position:relative; z-index:10; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:#888; font-size:14px;">Total Balance</div><h2 style="margin:5px 0;">₹ <span class="user-bal">0.00</span></h2></div>
        </div>
        <div class="card" style="padding:0; overflow:hidden;">
            <div style="padding: 15px 20px; border-bottom: 1px solid #eee; font-weight: bold; cursor:pointer;" onclick="showPopup('Order Record', 'No recent bets.')">📄 Order Record </div>
            <div style="padding: 15px 20px; border-bottom: 1px solid #eee; font-weight: bold; cursor:pointer;" onclick="openChangePassword()">🔒 Change Password</div>
            <div style="padding: 15px 20px; border-bottom: 1px solid #eee; font-weight: bold; cursor:pointer;" onclick="showPopup('Support', 'Connecting to Chat...')">🎧 Support</div>
            <div style="padding: 15px 20px; font-weight: bold; color: #e74c3c; text-align: center; cursor:pointer;" onclick="logout()">Log Out</div>
        </div>
    </div>

    <div class="bottom-nav" id="bottom-nav" style="display: none;">
        <div class="nav-item active" onclick="switchScreen('home-screen', this)">🏠<br>Home</div>
        <div class="nav-item" onclick="switchScreen('invite-screen', this)">👥<br>Invite</div>
        <div class="nav-item" onclick="switchScreen('recharge-screen', this)">💳<br>Recharge</div>
        <div class="nav-item" onclick="switchScreen('profile-screen', this)">👤<br>My</div>
    </div>

    <script>
        let userEmail = ""; let userUID = ""; let userBalance = 0.00;
        
        function showPopup(title, message) {
            document.getElementById('popup-title').innerText = title;
            document.getElementById('popup-message').innerText = message;
            document.getElementById('popup-inputs').style.display = 'none';
            document.getElementById('popup-ok').onclick = closePopup;
            document.getElementById('custom-popup').style.display = 'flex';
        }
        function closePopup() { document.getElementById('custom-popup').style.display = 'none'; }
        
        // --- CHANGE PASSWORD LOGIC ---
        function openChangePassword() {
            document.getElementById('popup-title').innerText = "Change Password";
            document.getElementById('popup-message').innerText = "";
            let inputs = document.getElementById('popup-inputs');
            inputs.innerHTML = `<input type='password' id='old_p' placeholder='Old Password' style='width:90%; padding:10px; margin-bottom:10px;'>
                                <input type='password' id='new_p' placeholder='New Password' style='width:90%; padding:10px;'>`;
            inputs.style.display = 'block';
            
            document.getElementById('popup-ok').onclick = async function() {
                let old_p = document.getElementById('old_p').value;
                let new_p = document.getElementById('new_p').value;
                if(new_p.length < 6) { alert("New password must be 6+ chars"); return; }
                
                let res = await fetch('/api/change_password', {
                    method: 'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({email: userEmail, old_pass: old_p, new_pass: new_p})
                });
                let data = await res.json();
                closePopup();
                setTimeout(() => showPopup(data.status==='success'?"Success":"Error", data.message), 300);
            };
            document.getElementById('custom-popup').style.display = 'flex';
        }

        // --- AUTH ---
        function toggleAuth(type) {
            document.getElementById('tab-login').classList.remove('active'); document.getElementById('tab-register').classList.remove('active');
            document.getElementById('form-login').style.display = 'none'; document.getElementById('form-register').style.display = 'none';
            if(type === 'login') { document.getElementById('tab-login').classList.add('active'); document.getElementById('form-login').style.display = 'block'; }
            else { document.getElementById('tab-register').classList.add('active'); document.getElementById('form-register').style.display = 'block'; }
        }

        async function sendEmailOTP() {
            let email = document.getElementById('reg-email').value;
            if(!email.includes('@')) return showPopup("Error", "Invalid email");
            document.getElementById('btn-send-otp').innerText = "Sending...";
            let res = await fetch('/api/send_otp', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ email: email }) });
            let data = await res.json();
            showPopup("Status", data.message);
            document.getElementById('btn-send-otp').innerText = "Send OTP";
        }

        async function verifyRegister() {
            let email = document.getElementById('reg-email').value; let otp = document.getElementById('reg-otp').value;
            let pass = document.getElementById('reg-pass').value; let ref = document.getElementById('reg-ref').value;
            let res = await fetch('/api/register', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ email: email, otp: otp, password: pass, ref: ref }) });
            let data = await res.json();
            if(data.status === 'success') { showPopup("Success", data.message); setTimeout(() => { closePopup(); loginSuccess(email, data.uid, data.balance); }, 2000); }
            else showPopup("Error", data.message);
        }

        async function verifyLogin() {
            let email = document.getElementById('login-email').value; let pass = document.getElementById('login-pass').value;
            let res = await fetch('/api/login', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ email: email, password: pass }) });
            let data = await res.json();
            if(data.status === 'success') loginSuccess(email, data.uid, data.balance);
            else showPopup("Error", data.message);
        }

        function loginSuccess(email, uid, balance) {
            userEmail = email; userUID = uid; userBalance = balance.toFixed(2);
            document.querySelectorAll('.user-uid').forEach(el => el.innerText = userUID);
            document.querySelectorAll('.user-bal').forEach(el => el.innerText = userBalance);
            let parts = email.split("@");
            document.getElementById('profile-email').innerText = (parts[0].length>3?parts[0].substring(0,3)+"***":parts[0]) + "@" + parts[1];
            document.getElementById('invite-link-text').innerText = window.location.origin + "/invite?ref=" + userUID;
            switchScreen('home-screen', document.querySelectorAll('.nav-item')[0]);
            document.getElementById('bottom-nav').style.display = "flex";
        }

        function logout() { document.getElementById('bottom-nav').style.display = "none"; switchScreen('auth-screen'); }
        function switchScreen(screenId, navElement = null) {
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active-screen'));
            document.getElementById(screenId).classList.add('active-screen');
            if(navElement) { document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active')); navElement.classList.add('active'); }
        }

        // =====================================
        // 🚀 GRAPH DRAWING FUNCTION
        // =====================================
        function drawGraph(canvasId, multiplier, isCrashed, isAviator) {
            const canvas = document.getElementById(canvasId);
            const ctx = canvas.getContext('2d');
            canvas.width = canvas.parentElement.clientWidth; canvas.height = canvas.parentElement.clientHeight;
            let w = canvas.width, h = canvas.height;
            ctx.clearRect(0,0,w,h);

            ctx.strokeStyle = isAviator ? '#333' : '#e0e0e0'; ctx.lineWidth = 1; ctx.beginPath();
            for(let i=0; i<w; i+=40) { ctx.moveTo(i,0); ctx.lineTo(i,h); }
            for(let i=0; i<h; i+=40) { ctx.moveTo(0,i); ctx.lineTo(w,i); }
            ctx.stroke();

            let progress = Math.min((multiplier - 1) / 4.0, 1.0); 
            if (multiplier === 1.00) progress = 0;
            let startX = 20, startY = h - 20, endX = 20 + (w - 60) * progress, endY = (h - 20) - ((h - 60) * Math.pow(progress, 1.2)); 

            if (progress > 0) {
                let mainColor = isAviator ? '#e74c3c' : '#4a88ff';
                let crashColor = isAviator ? '#c0392b' : '#e74c3c';
                let finalColor = isCrashed ? crashColor : mainColor;

                ctx.beginPath(); ctx.moveTo(startX, startY); ctx.quadraticCurveTo(endX * 0.5, startY, endX, endY);
                ctx.lineTo(endX, h); ctx.lineTo(startX, h);
                ctx.fillStyle = isCrashed ? (isAviator?'rgba(192, 57, 43, 0.2)':'rgba(231, 76, 60, 0.2)') : (isAviator?'rgba(231, 76, 60, 0.2)':'rgba(74, 136, 255, 0.2)'); ctx.fill();
                ctx.beginPath(); ctx.moveTo(startX, startY); ctx.quadraticCurveTo(endX * 0.5, startY, endX, endY);
                ctx.strokeStyle = finalColor; ctx.lineWidth = 4; ctx.stroke();
                
                ctx.font = "30px Arial"; 
                if (isAviator) ctx.fillText(isCrashed ? "💥" : "✈️", endX - 10, endY + 10);
                else ctx.fillText(isCrashed ? "💥" : "🚀", endX - 10, endY + 10);
            }
        }

        // =====================================
        // 🔄 SYNC GAMES & LIVE BETS
        // =====================================
        async function syncGame(gameName) {
            if(!document.getElementById(gameName+'-screen').classList.contains('active-screen')) return;
            try {
                let res = await fetch('/api/game_state/' + gameName);
                let data = await res.json();
                
                // History
                let hBar = document.getElementById(gameName+'-history');
                hBar.innerHTML = '';
                data.history.forEach(val => { hBar.innerHTML += `<div class="pill ${val<2?'red':(val<5?'blue':'green')}">${val}x</div>`; });

                let title = document.getElementById(gameName+'-title');
                let display = document.getElementById(gameName+'-display');
                let isAviator = gameName === 'aviator';

                // Display Game Status
                if(data.status === 'waiting') {
                    title.innerText = "Next round in"; display.innerText = data.time_left.toFixed(1) + "s"; 
                    display.style.color = isAviator ? "#aaa" : "#333";
                    drawGraph(gameName+'Canvas', 1.00, false, isAviator);
                } 
                else if(data.status === 'flying') {
                    title.innerText = ""; display.innerText = data.multiplier.toFixed(2) + "x"; 
                    display.style.color = isAviator ? "#e74c3c" : "#4a88ff";
                    drawGraph(gameName+'Canvas', data.multiplier, false, isAviator);
                }
                else if(data.status === 'crashed') {
                    title.innerText = "Crashed"; display.innerText = data.multiplier.toFixed(2) + "x"; 
                    display.style.color = isAviator ? "#c0392b" : "#e74c3c";
                    drawGraph(gameName+'Canvas', data.multiplier, true, isAviator);
                }

                // Render Live Fake Bets (Order Book)
                document.getElementById(gameName+'-players').innerText = data.active_users;
                document.getElementById(gameName+'-totalamt').innerText = '₹' + data.total_amount;
                
                let ordersDiv = document.getElementById(gameName+'-orders');
                let html = "";
                data.fake_bets.forEach(b => {
                    let st = b.cashed_out ? `<span class="text-green">${b.stopped_at}x</span>` : (data.status=='crashed'?`<span class="text-red">Crash</span>`:`-`);
                    let pr = b.cashed_out ? `<span class="text-green">+₹${b.profit}</span>` : (data.status=='crashed'?`<span class="text-red">-₹${b.bet}</span>`:`-`);
                    html += `<div class="bet-row"><div>${b.uid}</div><div>₹${b.bet}</div><div>${st}</div><div>${pr}</div></div>`;
                });
                ordersDiv.innerHTML = html;

            } catch(e) {}
        }

        setInterval(() => { syncGame('crash'); syncGame('aviator'); }, 100); 

    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
