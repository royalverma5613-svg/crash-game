from flask import Flask, jsonify, render_template_string, request
import random, time, threading, sqlite3, smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ==========================================
# 📧 EMAIL OTP CONFIGURATION (Yahan apna Gmail aur App Password dalein)
# ==========================================
SENDER_EMAIL = "your_email@gmail.com"  
SENDER_PASSWORD = "mfoq cjkt eyub tuvu"  

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
        bets.append({"uid": f"{random.randint(10,99)}***{random.randint(10,99)}", "bet": random.choice([20,50,100,200,500]), "cashout_target": round(random.uniform(1.05, 5.50), 2), "cashed_out": False, "profit": 0, "stopped_at": 0})
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
                    b["cashed_out"], b["profit"], b["stopped_at"] = True, round(b["bet"] * b["cashout_target"], 2), b["cashout_target"]
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
    conn = sqlite3.connect('users.db')
    if conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone():
        conn.close(); return jsonify({"status":"error", "message":"Email registered!"})
    conn.close()
    otp = str(random.randint(1000, 9999)); otp_storage[email] = otp
    try:
        msg = MIMEText(f"Your Super100x OTP is: {otp}"); msg['Subject']='Super100x OTP'; msg['From']=SENDER_EMAIL; msg['To']=email
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(SENDER_EMAIL, SENDER_PASSWORD); server.send_message(msg); server.quit()
        return jsonify({"status":"success", "message":"OTP sent!"})
    except Exception as e: return jsonify({"status":"error", "message":"Failed to send OTP."})

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    e, o = request.json.get('email'), request.json.get('otp')
    return jsonify({"status":"success", "message":"Verified!"}) if otp_storage.get(e)==o else jsonify({"status":"error", "message":"Invalid OTP"})

@app.route('/api/register', methods=['POST'])
def register_user():
    e, p, r = request.json.get('email'), request.json.get('password'), request.json.get('ref', '')
    uid = str(random.randint(1000000, 9999999)); conn = sqlite3.connect('users.db')
    conn.execute("INSERT INTO users (email, password, uid, ref, balance) VALUES (?,?,?,?,?)", (e, p, uid, r, 50.0))
    conn.commit(); conn.close(); otp_storage.pop(e, None)
    return jsonify({"status":"success", "message":"Created!", "uid":uid, "balance":50.0})

@app.route('/api/login', methods=['POST'])
def login_user():
    u = sqlite3.connect('users.db').execute("SELECT uid, balance FROM users WHERE email=? AND password=?", (request.json.get('email'), request.json.get('password'))).fetchone()
    return jsonify({"status":"success", "message":"Login success!", "uid":u[0], "balance":u[1]}) if u else jsonify({"status":"error", "message":"Wrong details"})

@app.route('/api/game_state/<g>')
def get_state(g):
    if g in games:
        d = dict(games[g]); d["active_users"] = SETTINGS[f"{g}_active_users"]; return jsonify(d)
    return jsonify({"error":"Not found"})

@app.route('/')
def home():
    # Yeh file ab 'index.html' se design uthayegi
    with open('index.html', 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
