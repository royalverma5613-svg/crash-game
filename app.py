from flask import Flask, jsonify, render_template_string, request
import random
import time
import threading

app = Flask(__name__)

# ==========================================
# ⚙️ REAL SERVER GAME ENGINE (Runs 24/7)
# ==========================================
game_state = {
    "status": "waiting", 
    "multiplier": 1.00,
    "next_crash": 2.50,
    "time_left": 12.0,
    "history": [1.23, 5.27, 4.12, 1.03, 2.49]
}

def game_loop():
    global game_state
    while True:
        # WAITING PHASE (12 Seconds)
        game_state["status"] = "waiting"
        game_state["multiplier"] = 1.00
        game_state["next_crash"] = round(random.uniform(1.05, 10.50), 2)
        
        for i in range(120, 0, -1):
            game_state["time_left"] = i / 10.0
            time.sleep(0.1)

        # FLYING PHASE
        game_state["status"] = "flying"
        current_mult = 1.00
        while current_mult < game_state["next_crash"]:
            current_mult += (0.01 * current_mult) + 0.01 
            game_state["multiplier"] = round(current_mult, 2)
            time.sleep(0.05)

        # CRASHED PHASE
        game_state["status"] = "crashed"
        game_state["multiplier"] = game_state["next_crash"]
        
        game_state["history"].insert(0, game_state["next_crash"])
        if len(game_state["history"]) > 6:
            game_state["history"].pop()
            
        time.sleep(4)

threading.Thread(target=game_loop, daemon=True).start()


# ==========================================
# 🌐 FRONTEND UI (FIEWIN/ACEWIN CLONE)
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Acewin Clone</title>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; background-color: #f4f5f7; color: #333; overflow-x: hidden; }
        .screen { display: none; min-height: 100vh; padding-bottom: 70px;}
        .active-screen { display: block; }
        
        /* --- LOGIN SCREEN --- */
        .login-box { background: white; margin: 50px 20px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .input-group { margin-bottom: 20px; }
        .input-group input { width: 90%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; }
        .btn-blue { background: #4a88ff; color: white; width: 100%; padding: 12px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .otp-btn { background: #e0e0e0; color: #333; padding: 10px; border: none; border-radius: 6px; margin-top: 10px; cursor: pointer; }

        /* --- DASHBOARD / HOME --- */
        .top-bar { padding: 15px; display: flex; justify-content: space-between; align-items: center; background: white; }
        .balance-card { margin: 15px; padding: 20px; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .game-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; }
        .game-tile { background: white; border-radius: 12px; padding: 20px; text-align: center; font-weight: bold; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }

        /* --- CRASH GAME SCREEN --- */
        .crash-header { background: #4a88ff; color: white; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; display: flex; justify-content: space-between;}
        .history-bar { display: flex; gap: 5px; padding: 10px; overflow-x: auto; background: white; }
        .pill { padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; }
        .pill.blue { background: #4a88ff; } .pill.green { background: #2ecc71; } .pill.red { background: #e74c3c; }
        
        .game-area { background: #eef3f9; height: 300px; position: relative; margin: 10px; border: 2px solid #333; border-radius: 8px; overflow: hidden; }
        .rocket { position: absolute; bottom: 10px; left: 10px; font-size: 40px; transition: 0.1s; z-index: 10; }
        .center-text { position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
        .timer-text { font-size: 40px; font-weight: bold; color: #333; }
        .bet-controls { background: white; padding: 15px; margin: 10px; border-radius: 8px; }
        
        /* --- NEW PROFILE SCREEN --- */
        .profile-header { background: #4a88ff; padding: 30px 20px; color: white; display: flex; align-items: center; gap: 15px; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;}
        .avatar { width: 60px; height: 60px; background: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 30px; }
        .profile-menu { background: white; margin: 15px; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .menu-item { padding: 15px 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; font-weight: bold; cursor: pointer; }
        .menu-item:last-child { border-bottom: none; }
        .menu-item.logout { color: #e74c3c; text-align: center; justify-content: center; }

        /* --- BOTTOM NAV BAR --- */
        .bottom-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #ddd; z-index: 100; }
        .nav-item { text-align: center; font-size: 12px; color: #888; cursor: pointer; width: 25%; }
        .nav-item.active { color: #4a88ff; font-weight: bold; }
    </style>
</head>
<body>

    <!-- 1. LOGIN SCREEN -->
    <div id="login-screen" class="screen active-screen">
        <h2 style="text-align: center; color: #4a88ff; margin-top: 50px;">Welcome to Super100x</h2>
        <div class="login-box">
            <div class="input-group">
                <label>Mobile Number</label><br>
                <input type="number" id="mobile" placeholder="Enter mobile number">
                <button class="otp-btn" onclick="sendOTP()">Get Verification Code</button>
            </div>
            <div class="input-group">
                <label>Verification Code</label><br>
                <input type="number" id="otp" placeholder="Enter OTP (Hint: 1234)">
            </div>
            <button class="btn-blue" onclick="verifyLogin()">LOGIN</button>
        </div>
    </div>

    <!-- 2. HOME SCREEN -->
    <div id="home-screen" class="screen">
        <div class="top-bar">
            <b>User ID: <span id="home-uid">Loading...</span></b>
            <span style="background: #eef3f9; padding: 5px 10px; border-radius: 20px;">🪙 App</span>
        </div>
        <div class="balance-card">
            <div style="color: #888;">Balance</div>
            <h1 style="margin: 5px 0;">₹ 180.50 <span style="font-size: 14px; color: #888;">rupee</span></h1>
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button class="btn-blue" style="border-radius: 20px;" onclick="alert('Redirecting to Payment Gateway...')">Recharge</button>
                <button class="btn-blue" style="background: white; color: #333; border: 1px solid #ccc; border-radius: 20px;" onclick="alert('Minimum withdrawal ₹500')">Withdraw</button>
            </div>
        </div>
        
        <marquee style="background: white; padding: 10px; font-size: 14px;">🏆 **9824 Wins ₹450.00 in Crash game</marquee>

        <div class="game-grid">
            <div class="game-tile" onclick="switchScreen('crash-screen')">
                <div style="font-size: 40px;">🚀</div>
                Crash
            </div>
            <div class="game-tile" onclick="alert('Dice game coming soon!')">
                <div style="font-size: 40px;">🎲</div>
                Dice
            </div>
        </div>
    </div>

    <!-- 3. CRASH GAME SCREEN -->
    <div id="crash-screen" class="screen">
        <div class="crash-header">
            <span onclick="switchScreen('home-screen')" style="cursor:pointer;">❮ Back</span>
            Crash
            <span onclick="alert('Crash Rule: Cash out before the rocket crashes!')" style="cursor:pointer;">Rule ❓</span>
        </div>
        <div class="history-bar" id="history-bar"></div>
        <div class="game-area">
            <div class="rocket" id="rocket">🚀</div>
            <div class="center-text">
                <div id="status-title" style="font-size: 18px; font-weight: bold;">Next round in</div>
                <div id="main-display" class="timer-text">12.0s</div>
            </div>
        </div>
        <div class="bet-controls">
            <div style="color:#888; margin-bottom:10px;">Balance: ₹180.50</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <input type="number" value="100" style="width: 50%; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
                <button class="btn-blue" style="width: 40%;" onclick="alert('Bet Placed Successfully!')">START</button>
            </div>
        </div>
    </div>
    
    <!-- 4. INVITE SCREEN -->
    <div id="invite-screen" class="screen">
        <div class="crash-header" style="justify-content: center;">Invite & Earn</div>
        <div class="balance-card" style="text-align: center;">
            <h3>Your Personal Invite Link</h3>
            <p id="invite-link-text" style="background: #eef3f9; padding: 10px; border-radius: 5px; word-break: break-all; font-weight:bold;">
                Link loading...
            </p>
            <button class="btn-blue" onclick="alert('Link Copied Successfully!')">Copy Link</button>
            <p style="color: #888; font-size: 14px; margin-top: 20px;">Share this link with your friends and earn commission on their trades!</p>
        </div>
    </div>

    <!-- 5. PROFILE SCREEN (NEW) -->
    <div id="profile-screen" class="screen">
        <div class="profile-header">
            <div class="avatar">👤</div>
            <div>
                <h3 id="profile-phone" style="margin:0 0 5px 0;">+91 987****321</h3>
                <div style="font-size:14px; background:rgba(0,0,0,0.2); padding:2px 10px; border-radius:10px; display:inline-block;">
                    ID: <span id="profile-uid">Loading...</span>
                </div>
            </div>
        </div>
        <div class="balance-card" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:#888; font-size:14px;">Total Balance</div>
                <h2>₹ 180.50</h2>
            </div>
            <button class="btn-blue" style="width:auto; padding:8px 20px; border-radius:20px;" onclick="switchScreen('home-screen')">Play</button>
        </div>
        <div class="profile-menu">
            <div class="menu-item" onclick="alert('Order Records')">📄 Order Record <span>></span></div>
            <div class="menu-item" onclick="alert('Financial Details')">💰 Financial Details <span>></span></div>
            <div class="menu-item" onclick="alert('App Downloading...')">⬇️ Download App <span>></span></div>
            <div class="menu-item" onclick="alert('Support Chat Opened')">🎧 Support <span>></span></div>
            <div class="menu-item logout" onclick="logout()">Log Out</div>
        </div>
    </div>

    <!-- BOTTOM NAVIGATION -->
    <div class="bottom-nav" id="bottom-nav" style="display: none;">
        <div class="nav-item active" onclick="switchScreen('home-screen', this)">🏠<br>Home</div>
        <div class="nav-item" onclick="switchScreen('invite-screen', this)">👥<br>Invite</div>
        <div class="nav-item" onclick="switchScreen('home-screen', this); alert('Recharge Page')">💳<br>Recharge</div>
        <div class="nav-item" onclick="switchScreen('profile-screen', this)">👤<br>My</div>
    </div>

    <script>
        // --- REAL LOGIN & DYNAMIC UID LOGIC ---
        function sendOTP() {
            let mob = document.getElementById('mobile').value;
            if(mob.length < 10) { alert("Enter valid 10-digit mobile number"); return; }
            alert("OTP sent to " + mob + "! (Demo Hint: enter 1234)");
        }
        
        function verifyLogin() {
            let mobile = document.getElementById('mobile').value;
            let otp = document.getElementById('otp').value;
            
            if(otp === "1234" && mobile.length >= 10) {
                // 1. Generate Unique UID (e.g. 7349102)
                let newUID = Math.floor(1000000 + Math.random() * 9000000);
                
                // 2. Set UID in Home and Profile
                document.getElementById('home-uid').innerText = newUID;
                document.getElementById('profile-uid').innerText = newUID;
                
                // 3. Mask Phone Number (+91 987****321)
                let maskedPhone = mobile.substring(0,3) + "****" + mobile.substring(mobile.length-3);
                document.getElementById('profile-phone').innerText = "+91 " + maskedPhone;
                
                // 4. Update Personal Invite Link
                document.getElementById('invite-link-text').innerText = "https://crashsuper100x.onrender.com/invite?ref=" + newUID;

                // Move to Home
                switchScreen('home-screen', document.querySelectorAll('.nav-item')[0]);
                document.getElementById('bottom-nav').style.display = "flex";
            } else {
                alert("Incorrect OTP or Mobile Number!");
            }
        }
        
        function logout() {
            if(confirm("Are you sure you want to log out?")) {
                document.getElementById('bottom-nav').style.display = "none";
                document.getElementById('mobile').value = "";
                document.getElementById('otp').value = "";
                switchScreen('login-screen');
            }
        }

        // --- NAVIGATION LOGIC ---
        function switchScreen(screenId, navElement = null) {
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active-screen'));
            document.getElementById(screenId).classList.add('active-screen');
            
            if(navElement) {
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                navElement.classList.add('active');
            }
        }

        // --- GAME ENGINE SYNC ---
        const display = document.getElementById('main-display');
        const title = document.getElementById('status-title');
        const rocket = document.getElementById('rocket');
        const historyBar = document.getElementById('history-bar');

        setInterval(async () => {
            if(document.getElementById('crash-screen').classList.contains('active-screen')) {
                try {
                    let res = await fetch('/api/game_state');
                    let data = await res.json();
                    
                    historyBar.innerHTML = '';
                    data.history.forEach(val => {
                        let color = val < 2.0 ? 'red' : (val < 5.0 ? 'blue' : 'green');
                        historyBar.innerHTML += `<div class="pill ${color}">${val}x</div>`;
                    });

                    if(data.status === 'waiting') {
                        title.innerText = "Next round in";
                        display.innerText = data.time_left + "s";
                        display.style.color = "#333";
                        rocket.style.bottom = "10px";
                        rocket.style.left = "10px";
                    } 
                    else if(data.status === 'flying') {
                        title.innerText = "";
                        display.innerText = data.multiplier.toFixed(2) + "x";
                        display.style.color = "#4a88ff";
                        
                        let progress = Math.min(data.multiplier / 5.0, 1.0); 
                        rocket.style.bottom = (10 + (progress * 220)) + "px";
                        rocket.style.left = (10 + (progress * 200)) + "px";
                    }
                    else if(data.status === 'crashed') {
                        title.innerText = "Crashed";
                        display.innerText = data.multiplier.toFixed(2) + "x";
                        display.style.color = "#e74c3c";
                    }
                } catch(e) {}
            }
        }, 100); 
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/game_state')
def get_state():
    return jsonify(game_state)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
