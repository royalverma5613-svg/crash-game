from flask import Flask, jsonify, render_template_string, request
import random, time, threading, sqlite3, smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ==========================================
# 📧 EMAIL OTP CONFIGURATION
# ==========================================
SENDER_EMAIL = "your_email@gmail.com"  # Yahan apna asal Gmail dalein
SENDER_PASSWORD = "mfoq cjkt eyub tuvu"  # Aapka App Password

def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, uid TEXT, ref TEXT, balance REAL)')
    conn.commit(); conn.close()

init_db()
otp_storage = {}

SETTINGS = {"crash_active_users": 10000, "aviator_active_users": 100}
games = {"crash": {"status":"waiting", "multiplier":1.0, "next_crash":2.5, "time_left":12.0, "history":[], "fake_bets":[], "total_amount":0},
         "aviator": {"status":"waiting", "multiplier":1.0, "next_crash":3.0, "time_left":8.0, "history":[], "fake_bets":[], "total_amount":0}}

def generate_fake_bets(num_users):
    bets = []; tot = sum(random.choice([20,50,100,200,500]) for _ in range(num_users))
    for _ in range(min(num_users, 40)):
        bets.append({"uid": f"{random.randint(10,99)}***{random.randint(10,99)}", "bet": random.choice([20,50,100,200,500]), "cashout_target": round(random.uniform(1.05, 5.50), 2), "cashed_out": False, "profit": 0})
    return bets, tot

def game_thread(g, wait_time):
    while True:
        games[g]["status"], games[g]["multiplier"], games[g]["next_crash"] = "waiting", 1.0, round(random.uniform(1.05, 10.50), 2)
        games[g]["fake_bets"], games[g]["total_amount"] = generate_fake_bets(SETTINGS[f"{g}_active_users"])
        for i in range(int(wait_time*10), -1, -1):
            games[g]["time_left"] = round(i/10.0, 1); time.sleep(0.1)
        games[g]["status"], m = "flying", 1.0
        while m < games[g]["next_crash"]:
            m += (0.01 * m) + 0.01; games[g]["multiplier"] = round(m, 2)
            for b in games[g]["fake_bets"]:
                if not b["cashed_out"] and m >= b["cashout_target"]:
                    b["cashed_out"], b["profit"] = True, round(b["bet"] * b["cashout_target"], 2)
            time.sleep(0.05)
        games[g]["status"], games[g]["multiplier"] = "crashed", games[g]["next_crash"]
        games[g]["history"].insert(0, games[g]["next_crash"])
        if len(games[g]["history"])>6: games[g]["history"].pop()
        time.sleep(4)

threading.Thread(target=game_thread, args=("crash", 12.0), daemon=True).start()
threading.Thread(target=game_thread, args=("aviator", 8.0), daemon=True).start()

@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    email = request.json.get('email')
    if not email or "@" not in email: return jsonify({"status":"error", "message":"Invalid email"})
    c = sqlite3.connect('users.db').cursor(); c.execute("SELECT * FROM users WHERE email=?", (email,))
    if c.fetchone(): return jsonify({"status":"error", "message":"Email registered!"})
    otp = str(random.randint(1000, 9999)); otp_storage[email] = otp
    try:
        msg = MIMEText(f"Your Super100x OTP is: {otp}"); msg['Subject']='Super100x OTP'; msg['From']=SENDER_EMAIL; msg['To']=email
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(SENDER_EMAIL, SENDER_PASSWORD); server.send_message(msg); server.quit()
        return jsonify({"status":"success", "message":"OTP sent!"})
    except: return jsonify({"status":"error", "message":"Failed to send OTP."})

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    e, o = request.json.get('email'), request.json.get('otp')
    return jsonify({"status":"success", "message":"Verified!"}) if otp_storage.get(e)==o else jsonify({"status":"error", "message":"Invalid OTP"})

@app.route('/api/register', methods=['POST'])
def register_user():
    e, p, r = request.json.get('email'), request.json.get('password'), request.json.get('ref', '')
    uid = str(random.randint(1000000, 9999999))
    conn = sqlite3.connect('users.db'); conn.execute("INSERT INTO users (email, password, uid, ref, balance) VALUES (?,?,?,?,?)", (e, p, uid, r, 50.0))
    conn.commit(); conn.close()
    if e in otp_storage: del otp_storage[e]
    return jsonify({"status":"success", "message":"Created!", "uid":uid, "balance":50.0})

@app.route('/api/login', methods=['POST'])
def login_user():
    e, p = request.json.get('email'), request.json.get('password')
    u = sqlite3.connect('users.db').execute("SELECT uid, balance FROM users WHERE email=? AND password=?", (e, p)).fetchone()
    return jsonify({"status":"success", "message":"Login success!", "uid":u[0], "balance":u[1]}) if u else jsonify({"status":"error", "message":"Wrong details"})

@app.route('/api/game_state/<g>')
def get_state(g):
    if g in games:
        d = dict(games[g]); d["active_users"] = SETTINGS[f"{g}_active_users"]
        return jsonify(d)
    return jsonify({"error":"Not found"})

# YAHAN SE HTML FILE READ HOGI
@app.route('/')
def home():
    with open('index.html', 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
            <!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Super 100x</title>
<style>
body{margin:0;font-family:Arial,sans-serif;background-color:#f4f5f7;color:#333;overflow-x:hidden;}
.screen{display:none;min-height:100vh;padding-bottom:70px;}
.active-screen{display:block;}
.blue-header, .red-header{color:white;padding:15px;text-align:center;font-size:18px;font-weight:bold;position:sticky;top:0;z-index:50;display:flex;justify-content:space-between;}
.blue-header{background:#4a88ff;} .red-header{background:#e74c3c;}
.btn-blue, .btn-red{color:white;width:100%;padding:12px;border:none;border-radius:6px;font-size:16px;font-weight:bold;cursor:pointer;}
.btn-blue{background:#4a88ff;} .btn-red{background:#e74c3c;}
.btn-grey{background:#e0e0e0;color:#333;width:100%;padding:12px;border:none;border-radius:6px;font-weight:bold;}
.card{background:white;margin:15px;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.05);}
.input-group{margin-bottom:15px;}
.input-group input{width:90%;padding:12px;border:1px solid #ccc;border-radius:6px;font-size:15px;margin-top:5px;outline:none;}
.auth-tabs{display:flex;justify-content:space-around;margin-bottom:20px;border-bottom:2px solid #eee;}
.auth-tab{padding:10px 20px;font-weight:bold;color:#888;cursor:pointer;}
.auth-tab.active{color:#4a88ff;border-bottom:3px solid #4a88ff;}
.bottom-nav{position:fixed;bottom:0;width:100%;background:white;display:flex;justify-content:space-around;padding:10px 0;border-top:1px solid #ddd;z-index:100;}
.nav-item{text-align:center;font-size:12px;color:#888;cursor:pointer;width:25%;}
.nav-item.active{color:#4a88ff;font-weight:bold;}
.custom-popup{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:1000;justify-content:center;align-items:center;}
.popup-content{background:white;width:80%;max-width:300px;padding:20px;border-radius:12px;text-align:center;}
.history-bar{display:flex;gap:5px;padding:10px;overflow-x:auto;background:white;border-bottom:1px solid #eee;}
.pill{padding:5px 12px;border-radius:20px;font-size:12px;font-weight:bold;color:white;min-width:35px;text-align:center;}
.pill.blue{background:#4a88ff;} .pill.green{background:#2ecc71;} .pill.red{background:#e74c3c;}
.game-container{position:relative;width:100%;height:250px;background:#eef3f9;overflow:hidden;border-bottom:2px solid #ddd;}
canvas{display:block;width:100%;height:100%;}
.center-text{position:absolute;top:40%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none;}
.timer-text{font-size:50px;font-weight:bold;color:#333;margin:0;}
.live-bets{background:white;margin-top:10px;padding:15px;font-size:14px;}
.bet-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f4f5f7;}
.bet-row div{width:25%;text-align:center;} .bet-row div:first-child{text-align:left;} .bet-row div:last-child{text-align:right;}
.text-green{color:#2ecc71;font-weight:bold;} .text-red{color:#e74c3c;font-weight:bold;}
.hidden{display:none !important;}
</style>
</head>
<body>
    <div id="custom-popup" class="custom-popup"><div class="popup-content"><h3 id="popup-title">Title</h3><p id="popup-message">Msg</p><button class="btn-blue" onclick="document.getElementById('custom-popup').style.display='none'">OK</button></div></div>
    
    <div id="auth-screen" class="screen active-screen">
        <h2 style="text-align:center;color:#4a88ff;margin-top:50px;">Super100x</h2>
        <div class="card">
            <div class="auth-tabs"><div class="auth-tab active" id="tab-login" onclick="toggleAuth('login')">LOGIN</div><div class="auth-tab" id="tab-register" onclick="toggleAuth('register')">REGISTER</div></div>
            <div id="form-login">
                <div class="input-group"><label>Email</label><br><input type="email" id="login-email"></div>
                <div class="input-group"><label>Password</label><br><input type="password" id="login-pass"></div>
                <button class="btn-blue" onclick="verifyLogin()">LOGIN</button>
            </div>
            <div id="form-register" class="hidden">
                <div id="reg-step-1">
                    <div class="input-group"><label>Email Address</label><br><input type="email" id="reg-email"><button id="btn-send-otp" class="btn-grey" style="margin-top:10px;" onclick="sendEmailOTP()">Send OTP</button></div>
                    <div id="otp-section" class="hidden"><div class="input-group"><label>OTP</label><br><input type="number" id="reg-otp"></div><button class="btn-blue" onclick="verifyOTP()">Verify OTP</button></div>
                </div>
                <div id="reg-step-2" class="hidden">
                    <p style="color:#2ecc71;text-align:center;font-weight:bold;">✅ Email Verified!</p>
                    <div class="input-group"><label>Password</label><br><input type="password" id="reg-pass"></div>
                    <div class="input-group"><label>Referral Code</label><br><input type="text" id="reg-ref"></div>
                    <button class="btn-blue" onclick="finalRegister()">REGISTER</button>
                </div>
            </div>
        </div>
    </div>

    <div id="home-screen" class="screen">
        <div style="padding:15px;display:flex;justify-content:space-between;background:white;"><b>ID: <span class="user-uid"></span></b></div>
        <div class="card"><div style="color:#888;">Balance</div><h1 style="margin:5px 0;">₹ <span class="user-bal"></span></h1>
        <div style="display:flex;gap:10px;margin-top:15px;"><button class="btn-blue">Recharge</button><button class="btn-grey">Withdraw</button></div></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;padding:15px;">
            <div class="card" style="margin:0;text-align:center;padding:30px 10px;cursor:pointer;border:2px solid #4a88ff;" onclick="switchScreen('crash-screen')"><div style="font-size:40px;margin-bottom:10px;">🚀</div><b>Crash (12s)</b></div>
            <div class="card" style="margin:0;text-align:center;padding:30px 10px;cursor:pointer;border:2px solid #e74c3c;" onclick="switchScreen('aviator-screen')"><div style="font-size:40px;margin-bottom:10px;">✈️</div><b>Aviator (8s)</b></div>
        </div>
    </div>

    <div id="crash-screen" class="screen">
        <div class="blue-header"><span onclick="switchScreen('home-screen')">❮</span> Crash <span></span></div>
        <div class="history-bar" id="crash-history"></div>
        <div class="game-container"><canvas id="crashCanvas"></canvas><div class="center-text"><div style="font-weight:bold;color:#888;">Next round</div><div id="crash-display" class="timer-text">12.0s</div></div></div>
        <div class="live-bets"><div style="display:flex;justify-content:space-between;margin-bottom:10px;color:#888;"><span>Players: <b id="crash-players">0</b></span><span>Total: <b id="crash-totalamt">₹0</b></span></div><div class="bets-header"><div>User</div><div>Bet</div><div>Mult</div><div>Profit</div></div><div id="crash-orders"></div></div>
    </div>

    <div id="aviator-screen" class="screen">
        <div class="red-header"><span onclick="switchScreen('home-screen')">❮</span> Aviator <span></span></div>
        <div class="history-bar" id="aviator-history"></div>
        <div class="game-container" style="background:#1a1a24;"><canvas id="aviatorCanvas"></canvas><div class="center-text"><div style="font-weight:bold;color:#aaa;">Next round</div><div id="aviator-display" class="timer-text" style="color:white;">8.0s</div></div></div>
        <div class="live-bets"><div style="display:flex;justify-content:space-between;margin-bottom:10px;color:#888;"><span>Players: <b id="aviator-players">0</b></span><span>Total: <b id="aviator-totalamt">₹0</b></span></div><div class="bets-header"><div>User</div><div>Bet</div><div>Mult</div><div>Profit</div></div><div id="aviator-orders"></div></div>
    </div>

    <div class="bottom-nav" id="bottom-nav">
        <div class="nav-item active" onclick="switchScreen('home-screen')">🏠<br>Home</div>
        <div class="nav-item" onclick="location.reload()">👤<br>Logout</div>
    </div>

<script>
    let userEmail="", userUID="", otpTimerInterval;
    function showPopup(t, m){ document.getElementById('popup-title').innerText=t; document.getElementById('popup-message').innerText=m; document.getElementById('custom-popup').style.display='flex'; }
    function toggleAuth(type){
        document.getElementById('tab-login').classList.toggle('active', type==='login');
        document.getElementById('tab-register').classList.toggle('active', type==='register');
        document.getElementById('form-login').classList.toggle('hidden', type!=='login');
        document.getElementById('form-register').classList.toggle('hidden', type!=='register');
    }

    async function sendEmailOTP() {
        let email = document.getElementById('reg-email').value;
        if(!email.includes('@')) return showPopup("Error", "Enter valid email");
        let btn = document.getElementById('btn-send-otp'); btn.innerText = "Sending..."; btn.disabled = true;
        try {
            let res = await fetch('/api/send_otp', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:email})});
            let data = await res.json();
            showPopup("Status", data.message);
            if(data.status === 'success') { document.getElementById('otp-section').classList.remove('hidden'); document.getElementById('reg-email').readOnly=true; startTimer(); }
            else { btn.innerText = "Send OTP"; btn.disabled = false; }
        } catch(e) { btn.innerText = "Send OTP"; btn.disabled = false; }
    }
    function startTimer() {
        let btn = document.getElementById('btn-send-otp'), timeLeft = 50; clearInterval(otpTimerInterval);
        otpTimerInterval = setInterval(() => { btn.innerText = `Resend in ${timeLeft}s`; timeLeft--; if(timeLeft<0){ clearInterval(otpTimerInterval); btn.innerText="Resend OTP"; btn.disabled=false; } }, 1000);
    }
    async function verifyOTP() {
        let res = await fetch('/api/verify_otp', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:document.getElementById('reg-email').value, otp:document.getElementById('reg-otp').value})});
        let data = await res.json();
        if(data.status === 'success') { document.getElementById('reg-step-1').classList.add('hidden'); document.getElementById('reg-step-2').classList.remove('hidden'); }
        else showPopup("Error", data.message);
    }
    async function finalRegister() {
        let pass = document.getElementById('reg-pass').value; if(pass.length<6) return showPopup("Error", "Pass 6+ chars");
        let res = await fetch('/api/register', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:document.getElementById('reg-email').value, password:pass, ref:document.getElementById('reg-ref').value})});
        let data = await res.json();
        if(data.status === 'success') { showPopup("Success", data.message); setTimeout(()=>{ loginSuccess(data.uid, data.balance); }, 1500); } else showPopup("Error", data.message);
    }
    async function verifyLogin() {
        let res = await fetch('/api/login', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:document.getElementById('login-email').value, password:document.getElementById('login-pass').value})});
        let data = await res.json();
        if(data.status === 'success') loginSuccess(data.uid, data.balance); else showPopup("Error", data.message);
    }
    function loginSuccess(uid, bal) {
        document.querySelectorAll('.user-uid').forEach(e=>e.innerText=uid); document.querySelectorAll('.user-bal').forEach(e=>e.innerText=bal.toFixed(2));
        switchScreen('home-screen'); document.getElementById('bottom-nav').style.display="flex"; document.getElementById('custom-popup').style.display='none';
    }
    function switchScreen(id) { document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active-screen')); document.getElementById(id).classList.add('active-screen'); }

    function drawGraph(canvasId, multiplier, isCrashed, isAviator) {
        const canvas = document.getElementById(canvasId); if(!canvas) return;
        const ctx = canvas.getContext('2d'); canvas.width = canvas.parentElement.clientWidth; canvas.height = canvas.parentElement.clientHeight;
        ctx.clearRect(0,0,canvas.width,canvas.height);
        let progress = Math.min((multiplier-1)/4.0, 1.0); if(multiplier===1.0) progress=0;
        let sx=20, sy=canvas.height-20, ex=20+(canvas.width-60)*progress, ey=(canvas.height-20)-((canvas.height-60)*Math.pow(progress,1.2));
        if(progress>0){
            ctx.beginPath(); ctx.moveTo(sx,sy); ctx.quadraticCurveTo(ex*0.5,sy,ex,ey); ctx.lineTo(ex,canvas.height); ctx.lineTo(sx,canvas.height);
            ctx.fillStyle = isCrashed ? 'rgba(231,76,60,0.2)' : 'rgba(74,136,255,0.2)'; ctx.fill();
            ctx.beginPath(); ctx.moveTo(sx,sy); ctx.quadraticCurveTo(ex*0.5,sy,ex,ey); ctx.strokeStyle = isCrashed ? '#e74c3c' : '#4a88ff'; ctx.lineWidth=4; ctx.stroke();
            ctx.font="30px Arial"; ctx.fillText(isCrashed?"💥":(isAviator?"✈":"🚀"), ex-10, ey+10);
        }
    }
    async function syncGame(g) {
        if(!document.getElementById(g+'-screen').classList.contains('active-screen')) return;
        try {
            let res = await fetch('/api/game_state/'+g), data = await res.json();
            document.getElementById(g+'-history').innerHTML = data.history.map(v=>`<div class="pill ${v<2?'red':(v<5?'blue':'green')}">${v}x</div>`).join('');
            document.getElementById(g+'-display').innerText = data.status==='waiting' ? data.time_left.toFixed(1)+'s' : data.multiplier.toFixed(2)+'x';
            drawGraph(g+'Canvas', data.status==='waiting'?1.0:data.multiplier, data.status==='crashed', g==='aviator');
            document.getElementById(g+'-players').innerText = data.active_users; document.getElementById(g+'-totalamt').innerText = '₹'+data.total_amount;
            document.getElementById(g+'-orders').innerHTML = data.fake_bets.map(b=>`<div class="bet-row"><div>${b.uid}</div><div>₹${b.bet}</div><div>${b.cashed_out?`<span class="text-green">${b.stopped_at}x</span>`:(data.status=='crashed'?`<span class="text-red">Crash</span>`:`-`)}</div><div>${b.cashed_out?`<span class="text-green">+₹${b.profit}</span>`:(data.status=='crashed'?`<span class="text-red">-₹${b.bet}</span>`:`-`)}</div></div>`).join('');
        } catch(e){}
    }
    setInterval(()=>{ syncGame('crash'); syncGame('aviator'); }, 100);
</script>
</body>
</html>
import telebot
import requests

TOKEN = '8687319607:AAHmDLKX5hpU581-fOdFOn15SAf2eWvbhT0'
ADMIN_ID = 7959829014
# Yahan apne Telegram Group ka ID dalein, taaki wahan message jaye (jaise -100123456789)
GROUP_ID = None  

GAME_LINK = 'https://crashsuper100x.onrender.com'

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['signal'])
def send_signal(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        res = requests.get(f'{GAME_LINK}/api/game_state/crash')
        data = res.json()
        if data['status'] == 'waiting':
            text = f"🚀 **VIP CRASH SIGNAL** 🚀\n\n🎯 Next Crash: **{data['next_crash']}x**\n⏳ Time left: {data['time_left']}s\n\n[🎮 Play Now]({GAME_LINK})"
            
            # Agar GROUP_ID dali hui hai, toh seedha Group me message bhejega
            if GROUP_ID:
                bot.send_message(GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
                bot.reply_to(message, "✅ VIP Signal Group me bhej diya gaya hai!")
            else:
                bot.reply_to(message, text, parse_mode="Markdown")
        else:
            bot.reply_to(message, "⏳ Game abhi ud rahi hai. Agle round ka wait karein!")
    except Exception as e:
        bot.reply_to(message, "⚠ Server Error! (Website link check karein)")

print("Group VIP Bot is Running...")
bot.polling()
