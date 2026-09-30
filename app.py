from flask import Flask, jsonify, render_template_string, request
import random
import time
import threading

app = Flask(__name__)

# ==========================================
# ⚙ REAL SERVER GAME ENGINE (Runs 24/7)
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
        game_state["status"] = "waiting"
        game_state["multiplier"] = 1.00
        game_state["next_crash"] = round(random.uniform(1.05, 10.50), 2)
        
        for i in range(120, -1, -1):
            game_state["time_left"] = round(i / 10.0, 1)
            time.sleep(0.1)

        game_state["status"] = "flying"
        current_mult = 1.00
        while current_mult < game_state["next_crash"]:
            current_mult += (0.01 * current_mult) + 0.01 
            game_state["multiplier"] = round(current_mult, 2)
            time.sleep(0.05)

        game_state["status"] = "crashed"
        game_state["multiplier"] = game_state["next_crash"]
        
        game_state["history"].insert(0, game_state["next_crash"])
        if len(game_state["history"]) > 6:
            game_state["history"].pop()
            
        time.sleep(4)

threading.Thread(target=game_loop, daemon=True).start()


# ==========================================
# 🌐 FRONTEND UI (Email Auth + Referral)
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
        
        /* Headers & Buttons */
        .blue-header { background: #4a88ff; color: white; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; position: sticky; top: 0; z-index: 50; display: flex; justify-content: space-between; align-items: center;}
        .btn-blue { background: #4a88ff; color: white; width: 100%; padding: 12px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        
        /* Cards & Inputs */
        .card { background: white; margin: 15px; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .input-group { margin-bottom: 15px; }
        .input-group input { width: 90%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; }
        
        /* Auth Tabs (Login / Register) */
        .auth-tabs { display: flex; justify-content: space-around; margin-bottom: 20px; border-bottom: 2px solid #eee; }
        .auth-tab { padding: 10px 20px; font-weight: bold; color: #888; cursor: pointer; }
        .auth-tab.active { color: #4a88ff; border-bottom: 3px solid #4a88ff; }
        
        /* Bottom Nav */
        .bottom-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #ddd; z-index: 100; }
        .nav-item { text-align: center; font-size: 12px; color: #888; cursor: pointer; width: 25%; }
        .nav-item.active { color: #4a88ff; font-weight: bold; }

        /* Custom Premium Popup (Replaces alert) */
        .custom-popup { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center; }
        .popup-content { background: white; width: 80%; max-width: 300px; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); animation: pop 0.3s; }
        @keyframes pop { from {transform: scale(0.8); opacity: 0;} to {transform: scale(1); opacity: 1;} }
        .popup-btn { background: #4a88ff; color: white; padding: 8px 20px; border: none; border-radius: 6px; margin-top: 15px; font-weight: bold; cursor: pointer; }

        /* Crash Game specific */
        .history-bar { display: flex; gap: 5px; padding: 10px; overflow-x: auto; background: white; border-bottom: 1px solid #eee;}
        .pill { padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; }
        .pill.blue { background: #4a88ff; } .pill.green { background: #2ecc71; } .pill.red { background: #e74c3c; }
        
        .game-container { position: relative; width: 100%; height: 300px; background: #eef3f9; overflow: hidden; border-bottom: 2px solid #ddd;}
        canvas { display: block; width: 100%; height: 100%; }
        .center-text { position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); text-align: center; pointer-events: none;}
        .timer-text { font-size: 50px; font-weight: bold; color: #333; margin: 0; line-height: 1;}
        .status-text { font-size: 16px; font-weight: bold; color: #888; margin-bottom: 5px;}
        
        .grid-options { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 15px; }
        .grid-options div { background: #f4f5f7; padding: 10px 0; text-align: center; border-radius: 5px; border: 1px solid #ddd; font-weight: bold; color: #555; cursor: pointer;}
    </style>
</head>
<body>

    <!-- CUSTOM PREMIUM POPUP -->
    <div id="custom-popup" class="custom-popup">
        <div class="popup-content">
            <h3 id="popup-title" style="margin-top:0; color:#333;">Title</h3>
            <p id="popup-message" style="color:#666; font-size:14px;">Message goes here.</p>
            <button class="popup-btn" onclick="closePopup()">OK</button>
        </div>
    </div>

    <!-- 1. AUTH SCREEN (LOGIN / REGISTER) -->
    <div id="auth-screen" class="screen active-screen">
        <h2 style="text-align: center; color: #4a88ff; margin-top: 50px;">Super100x</h2>
        <div class="card" style="padding: 10px 20px 30px 20px;">
            <div class="auth-tabs">
                <div class="auth-tab active" id="tab-login" onclick="toggleAuth('login')">LOGIN</div>
                <div class="auth-tab" id="tab-register" onclick="toggleAuth('register')">REGISTER</div>
            </div>
            
            <!-- Login Form -->
            <div id="form-login">
                <div class="input-group">
                    <label>Email Address</label><br>
                    <input type="email" id="login-email" placeholder="Enter your email">
                </div>
                <div class="input-group">
                    <label>Password</label><br>
                    <input type="password" id="login-pass" placeholder="Enter password">
                </div>
                <button class="btn-blue" onclick="verifyLogin()">LOGIN</button>
            </div>

            <!-- Register Form -->
            <div id="form-register" style="display:none;">
                <div class="input-group">
                    <label>Email Address</label><br>
                    <input type="email" id="reg-email" placeholder="Enter your email">
                    <button style="background: #e0e0e0; padding: 10px; border: none; border-radius: 6px; margin-top: 10px; width:100%; cursor:pointer;" onclick="sendEmailOTP()">Send OTP to Email</button>
                </div>
                <div class="input-group">
                    <label>Email OTP</label><br>
                    <input type="number" id="reg-otp" placeholder="Enter 4-digit OTP">
                </div>
                <div class="input-group">
                    <label>Create Password</label><br>
                    <input type="password" id="reg-pass" placeholder="Minimum 6 characters">
                </div>
                <div class="input-group">
                    <label>Referral Code (Optional)</label><br>
                    <input type="text" id="reg-ref" placeholder="Enter Invite Code">
                </div>
                <button class="btn-blue" onclick="verifyRegister()">REGISTER & PLAY</button>
            </div>
        </div>
    </div>

    <!-- 2. HOME SCREEN -->
    <div id="home-screen" class="screen">
        <div style="padding: 15px; display: flex; justify-content: space-between; align-items: center; background: white;">
            <b>ID: <span id="home-uid">Loading...</span></b>
            <span style="background: #eef3f9; padding: 5px 10px; border-radius: 20px;">🪙 App</span>
        </div>
        <div class="card">
            <div style="color: #888;">Balance</div>
            <h1 style="margin: 5px 0;">₹ <span id="main-bal">180.50</span> <span style="font-size: 14px; color: #888;">rupee</span></h1>
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button class="btn-blue" style="border-radius: 20px;" onclick="switchScreen('recharge-screen')">Recharge</button>
                <button class="btn-blue" style="background: white; color: #333; border: 1px solid #ccc; border-radius: 20px;" onclick="switchScreen('withdraw-screen')">Withdraw</button>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px;">
            <div class="card" style="margin:0; text-align:center; padding: 30px 10px; cursor:pointer;" onclick="switchScreen('crash-screen')">
                <div style="font-size: 40px; margin-bottom:10px;">🚀</div>
                <b>Crash Game</b>
            </div>
            <div class="card" style="margin:0; text-align:center; padding: 30px 10px; cursor:pointer;" onclick="showPopup('Coming Soon', 'Dice game is currently under maintenance. Please play Crash Game.')">
                <div style="font-size: 40px; margin-bottom:10px;">🎲</div>
                <b>Dice</b>
            </div>
        </div>
    </div>

    <!-- 3. CRASH GAME SCREEN (REAL CANVAS) -->
    <div id="crash-screen" class="screen">
        <div class="blue-header">
            <span onclick="switchScreen('home-screen')" style="cursor:pointer; font-size:22px;">❮</span>
            Crash
            <span style="font-size:14px; cursor:pointer;" onclick="showPopup('Crash Rule', 'Place a bet and cash out before the rocket crashes to win! If it crashes before you cash out, you lose the bet.')">Rule ❓</span>
        </div>
        
        <div class="history-bar" id="history-bar"></div>
        
        <div class="game-container">
            <canvas id="crashCanvas"></canvas>
            <div class="center-text">
                <div id="status-title" class="status-text">Next round in</div>
                <div id="main-display" class="timer-text">12.0s</div>
            </div>
        </div>
        
        <div style="background: white; padding: 15px; border-top: 1px solid #eee;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <div style="color:#888;">Balance: ₹180.50</div>
            </div>
            <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                <input type="number" id="bet-amt" value="100" style="width: 60%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-size:16px;">
                <button class="btn-blue" style="width: 40%;" onclick="showPopup('Success', 'Bet Placed Successfully for ₹' + document.getElementById('bet-amt').value)">START</button>
            </div>
            <div class="grid-options">
                <div onclick="document.getElementById('bet-amt').value=20">20</div>
                <div onclick="document.getElementById('bet-amt').value=50">50</div>
                <div onclick="document.getElementById('bet-amt').value=100">100</div>
                <div onclick="document.getElementById('bet-amt').value=1000">1000</div>
            </div>
        </div>
    </div>

    <!-- 4. RECHARGE SCREEN -->
    <div id="recharge-screen" class="screen">
        <div class="blue-header">
            <span onclick="switchScreen('home-screen')" style="cursor:pointer; font-size:22px;">❮</span>
            Recharge
            <span></span>
        </div>
        <div class="card">
            <h3>Select Amount</h3>
            <div class="grid-options" style="margin-top:20px;">
                <div onclick="document.getElementById('rech-amt').value=500">₹500</div>
                <div onclick="document.getElementById('rech-amt').value=1000">₹1000</div>
                <div onclick="document.getElementById('rech-amt').value=2000">₹2000</div>
                <div onclick="document.getElementById('rech-amt').value=5000">₹5000</div>
            </div>
            <input type="number" id="rech-amt" placeholder="Enter Amount" style="width: 90%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; margin-bottom:20px;">
            <button class="btn-blue" onclick="showPopup('Redirecting...', 'Connecting to UPI Payment Gateway. Please wait...')">Pay Now</button>
        </div>
    </div>

    <!-- 5. WITHDRAW SCREEN -->
    <div id="withdraw-screen" class="screen">
        <div class="blue-header">
            <span onclick="switchScreen('home-screen')" style="cursor:pointer; font-size:22px;">❮</span>
            Withdraw
            <span></span>
        </div>
        <div class="card">
            <div style="color: #888;">Available Balance</div>
            <h2>₹ 180.50</h2>
            <br>
            <label>Add Bank / UPI</label><br>
            <input type="text" placeholder="Enter UPI ID or Account No" style="width: 90%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; margin: 10px 0 20px 0;">
            
            <label>Withdrawal Amount</label><br>
            <input type="number" placeholder="Min ₹500" style="width: 90%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; margin: 10px 0 20px 0;">
            <button class="btn-blue" onclick="showPopup('Error', 'Insufficient Balance. Minimum withdrawal is ₹500')">Withdraw</button>
        </div>
    </div>

    <!-- 6. INVITE SCREEN -->
    <div id="invite-screen" class="screen">
        <div class="blue-header" style="justify-content: center;">Invite & Earn</div>
        <div class="card" style="text-align: center;">
            <h3>Your Personal Invite Link</h3>
            <p id="invite-link-text" style="background: #eef3f9; padding: 10px; border-radius: 5px; word-break: break-all; font-weight:bold; color:#4a88ff;">
                Loading...
            </p>
            <button class="btn-blue" onclick="showPopup('Copied', 'Your referral link has been copied successfully!')">Copy Link</button>
            <p style="color: #888; font-size: 14px; margin-top: 20px;">Share this link with your friends. When they register using your code, you earn commission on their trades!</p>
        </div>
    </div>

    <!-- 7. PROFILE / MY SCREEN -->
    <div id="profile-screen" class="screen">
        <div style="background: #4a88ff; padding: 40px 20px 20px 20px; color: white; display: flex; align-items: center; gap: 15px; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;">
            <div style="width: 60px; height: 60px; background: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 30px;">👤</div>
            <div>
                <h3 id="profile-email" style="margin:0 0 5px 0;">ami***@gmail.com</h3>
                <div style="font-size:14px; background:rgba(0,0,0,0.2); padding:2px 10px; border-radius:10px; display:inline-block;">ID: <span id="profile-uid">Loading...</span></div>
            </div>
        </div>
        <div class="card" style="margin-top: -20px; position:relative; z-index:10; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:#888; font-size:14px;">Total Balance</div>
                <h2 style="margin:5px 0;">₹ 180.50</h2>
            </div>
            <button class="btn-blue" style="width:auto; padding:8px 20px; border-radius:20px;" onclick="switchScreen('recharge-screen')">Recharge</button>
        </div>
        <div class="card" style="padding:0; overflow:hidden;">
            <div style="padding: 15px 20px; border-bottom: 1px solid #eee; font-weight: bold; display: flex; justify-content: space-between; cursor:pointer;" onclick="showPopup('Order Record', 'You have no recent bets placed.')">📄 Order Record <span>></span></div>
            <div style="padding: 15px 20px; border-bottom: 1px solid #eee; font-weight: bold; display: flex; justify-content: space-between; cursor:pointer;" onclick="showPopup('Financial Details', 'No recent transactions found.')">💰 Financial Details <span>></span></div>
            <div style="padding: 15px 20px; border-bottom: 1px solid #eee; font-weight: bold; display: flex; justify-content: space-between; cursor:pointer;" onclick="showPopup('Support', 'Connecting to Live Support Chat... (Demo)')">🎧 Support <span>></span></div>
            <div style="padding: 15px 20px; font-weight: bold; color: #e74c3c; text-align: center; cursor:pointer;" onclick="logout()">Log Out</div>
        </div>
    </div>

    <!-- BOTTOM NAVIGATION -->
    <div class="bottom-nav" id="bottom-nav" style="display: none;">
        <div class="nav-item active" onclick="switchScreen('home-screen', this)">🏠<br>Home</div>
        <div class="nav-item" onclick="switchScreen('invite-screen', this)">👥<br>Invite</div>
        <div class="nav-item" onclick="switchScreen('recharge-screen', this)">💳<br>Recharge</div>
        <div class="nav-item" onclick="switchScreen('profile-screen', this)">👤<br>My</div>
    </div>

    <script>
        // =====================================
        // 💬 CUSTOM POPUP LOGIC (NO MORE UGLY ALERTS)
        // =====================================
        function showPopup(title, message) {
            document.getElementById('popup-title').innerText = title;
            document.getElementById('popup-message').innerText = message;
            document.getElementById('custom-popup').style.display = 'flex';
        }
        function closePopup() {
            document.getElementById('custom-popup').style.display = 'none';
        }

        // =====================================
        // 🔐 EMAIL LOGIN & REGISTER LOGIC
        // =====================================
        function toggleAuth(type) {
            document.getElementById('tab-login').classList.remove('active');
            document.getElementById('tab-register').classList.remove('active');
            document.getElementById('form-login').style.display = 'none';
            document.getElementById('form-register').style.display = 'none';
            
            if(type === 'login') {
                document.getElementById('tab-login').classList.add('active');
                document.getElementById('form-login').style.display = 'block';
            } else {
                document.getElementById('tab-register').classList.add('active');
                document.getElementById('form-register').style.display = 'block';
            }
        }

        function maskEmail(email) {
            let parts = email.split("@");
            if(parts.length !== 2) return email;
            let name = parts[0];
            let domain = parts[1];
            if(name.length > 3) {
                name = name.substring(0, 3) + "***";
            }
            return name + "@" + domain;
        }

        function sendEmailOTP() { 
            let email = document.getElementById('reg-email').value;
            if(!email.includes('@')) { showPopup("Error", "Please enter a valid email address."); return; }
            showPopup("OTP Sent", "An OTP has been sent to " + email + ". (Hint: enter 1234)"); 
        }
        
        function verifyLogin() {
            initAudio(); // Unlock audio
            let email = document.getElementById('login-email').value;
            let pass = document.getElementById('login-pass').value;
            
            if(email.includes('@') && pass.length >= 6) {
                loginSuccess(email);
            } else {
                showPopup("Login Failed", "Invalid Email or Password. Password must be at least 6 characters.");
            }
        }

        function verifyRegister() {
            initAudio(); // Unlock audio
            let email = document.getElementById('reg-email').value;
            let otp = document.getElementById('reg-otp').value;
            let pass = document.getElementById('reg-pass').value;
            let ref = document.getElementById('reg-ref').value;
            
            if(!email.includes('@')) { showPopup("Error", "Invalid Email"); return; }
            if(otp !== "1234") { showPopup("Error", "Incorrect OTP"); return; }
            if(pass.length < 6) { showPopup("Error", "Password must be at least 6 characters"); return; }
            
            showPopup("Success", "Account created successfully!" + (ref ? " Referral applied." : ""));
            setTimeout(() => { closePopup(); loginSuccess(email); }, 1500);
        }

        function loginSuccess(email) {
            let newUID = Math.floor(1000000 + Math.random() * 9000000);
            
            // Set UID & Email Everywhere
            document.getElementById('home-uid').innerText = newUID;
            document.getElementById('profile-uid').innerText = newUID;
            document.getElementById('profile-email').innerText = maskEmail(email);
            document.getElementById('invite-link-text').innerText = "https://crashsuper100x.onrender.com/invite?ref=" + newUID;
            
            switchScreen('home-screen', document.querySelectorAll('.nav-item')[0]);
            document.getElementById('bottom-nav').style.display = "flex";
        }
        
        function logout() {
            document.getElementById('bottom-nav').style.display = "none";
            document.getElementById('login-email').value = "";
            document.getElementById('login-pass').value = "";
            switchScreen('auth-screen');
        }

        // =====================================
        // 🔊 AUDIO & SOUND SYSTEM
        // =====================================
        let audioCtx;
        function initAudio() {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
        }
        function playSound(type) {
            if (!audioCtx) return;
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain); gain.connect(audioCtx.destination);
            
            if (type === 'tick') {
                osc.type = 'sine'; osc.frequency.setValueAtTime(800, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
                osc.start(); osc.stop(audioCtx.currentTime + 0.1);
            } else if (type === 'fly') {
                osc.type = 'triangle'; osc.frequency.setValueAtTime(150, audioCtx.currentTime);
                osc.frequency.linearRampToValueAtTime(300, audioCtx.currentTime + 0.5);
                gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
                gain.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 0.5);
                osc.start(); osc.stop(audioCtx.currentTime + 0.5);
            } else if (type === 'crash') {
                osc.type = 'sawtooth'; osc.frequency.setValueAtTime(100, audioCtx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(10, audioCtx.currentTime + 0.5);
                gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
                osc.start(); osc.stop(audioCtx.currentTime + 0.5);
            }
        }

        // =====================================
        // 📱 NAVIGATION & CANVAS
        // =====================================
        function switchScreen(screenId, navElement = null) {
            initAudio(); 
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active-screen'));
            document.getElementById(screenId).classList.add('active-screen');
            
            if(navElement) {
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                navElement.classList.add('active');
            }
            if(screenId === 'crash-screen') resizeCanvas();
        }

        const canvas = document.getElementById('crashCanvas');
        const ctx = canvas.getContext('2d');
        function resizeCanvas() { canvas.width = canvas.parentElement.clientWidth; canvas.height = canvas.parentElement.clientHeight; }
        window.addEventListener('resize', resizeCanvas);

        function drawGraph(multiplier, isCrashed) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            let w = canvas.width, h = canvas.height;

            ctx.strokeStyle = '#e0e0e0'; ctx.lineWidth = 1; ctx.beginPath();
            for(let i=0; i<w; i+=40) { ctx.moveTo(i,0); ctx.lineTo(i,h); }
            for(let i=0; i<h; i+=40) { ctx.moveTo(0,i); ctx.lineTo(w,i); }
            ctx.stroke();

            let progress = Math.min((multiplier - 1) / 4.0, 1.0); 
            if (multiplier === 1.00) progress = 0;

            let startX = 20, startY = h - 20;
            let endX = 20 + (w - 60) * progress;
            let endY = (h - 20) - ((h - 60) * Math.pow(progress, 1.2)); 

            if (progress > 0) {
                ctx.beginPath(); ctx.moveTo(startX, startY); ctx.quadraticCurveTo(endX * 0.5, startY, endX, endY);
                ctx.lineTo(endX, h); ctx.lineTo(startX, h);
                ctx.fillStyle = isCrashed ? 'rgba(231, 76, 60, 0.2)' : 'rgba(74, 136, 255, 0.2)'; ctx.fill();

                ctx.beginPath(); ctx.moveTo(startX, startY); ctx.quadraticCurveTo(endX * 0.5, startY, endX, endY);
                ctx.strokeStyle = isCrashed ? '#e74c3c' : '#4a88ff'; ctx.lineWidth = 4; ctx.stroke();

                ctx.beginPath(); ctx.arc(endX, endY, 6, 0, Math.PI * 2);
                ctx.fillStyle = isCrashed ? '#e74c3c' : '#4a88ff'; ctx.fill();
                ctx.strokeStyle = "white"; ctx.lineWidth = 2; ctx.stroke();
                
                ctx.font = "24px Arial"; ctx.fillText(isCrashed ? "💥" : "🚀", endX + 10, endY + 10);
            }
        }

        const display = document.getElementById('main-display');
        const title = document.getElementById('status-title');
        const historyBar = document.getElementById('history-bar');
        let lastStatus = "", lastTimeLeft = 0;

        setInterval(async () => {
            if(!document.getElementById('crash-screen').classList.contains('active-screen')) return;
            try {
                let res = await fetch('/api/game_state');
                let data = await res.json();
                
                historyBar.innerHTML = '';
                data.history.forEach(val => {
                    let color = val < 2.0 ? 'red' : (val < 5.0 ? 'blue' : 'green');
                    historyBar.innerHTML += `<div class="pill ${color}">${val}x</div>`;
                });

                if(data.status === 'waiting') {
                    title.innerText = "Next round in"; display.innerText = data.time_left.toFixed(1) + "s"; display.style.color = "#333";
                    drawGraph(1.00, false);
                    if (data.time_left !== lastTimeLeft && data.time_left <= 5.0) { playSound('tick'); lastTimeLeft = data.time_left; }
                } 
                else if(data.status === 'flying') {
                    title.innerText = ""; display.innerText = data.multiplier.toFixed(2) + "x"; display.style.color = "#4a88ff";
                    drawGraph(data.multiplier, false);
                    if (Math.random() > 0.7) playSound('fly');
                }
                else if(data.status === 'crashed') {
                    title.innerText = "Crashed"; display.innerText = data.multiplier.toFixed(2) + "x"; display.style.color = "#e74c3c";
                    drawGraph(data.multiplier, true);
                    if (lastStatus !== 'crashed') { playSound('crash'); }
                }
                lastStatus = data.status;
            } catch(e) {}
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
