from flask import Flask, jsonify, render_template_string, request
import random

app = Flask(__name__)

SETTINGS = {
    "mode": "auto",  
    "current_crash": 1.00,
    "maintenance_mode": "ON", 
    "deposit_msg": "⚠ Deposit system is currently under maintenance. Please try again later.",
    "withdraw_msg": "⚠ Withdrawal gateway is temporarily unavailable due to a system upgrade."
}

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Crash Super 100x</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background-color: #121212; color: white; font-family: Arial; margin: 0; text-align: center; }
        .navbar { background-color: #1e1e1e; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; }
        .logo { font-size: 22px; font-weight: bold; color: #00ff66; }
        .btn { padding: 10px 18px; font-weight: bold; border-radius: 6px; cursor: pointer; border: none; font-size: 14px; }
        .btn-deposit { background-color: #00ff66; color: black; margin-right: 10px; }
        .btn-withdraw { background-color: transparent; color: white; border: 1px solid #fff; }
        .game-area { margin-top: 100px; }
        .multiplier { font-size: 120px; color: #00ff66; margin: 10px 0; text-shadow: 0px 0px 20px rgba(0, 255, 102, 0.5); }
        #toast { visibility: hidden; min-width: 300px; background-color: #333; color: #fff; text-align: center; border-radius: 8px; padding: 16px; position: fixed; left: 50%; bottom: 30px; transform: translateX(-50%); font-size: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5); }
        #toast.show { visibility: visible; animation: fadein 0.5s, fadeout 0.5s 2.5s; }
        @keyframes fadein { from {bottom: 0; opacity: 0;} to {bottom: 30px; opacity: 1;} }
        @keyframes fadeout { from {bottom: 30px; opacity: 1;} to {bottom: 0; opacity: 0;} }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">🚀 Crash Super 100x</div>
        <div>
            <button class="btn btn-deposit" onclick="showMsg('deposit')">📥 Deposit</button>
            <button class="btn btn-withdraw" onclick="showMsg('withdraw')">📤 Withdraw</button>
        </div>
    </div>
    <div class="game-area">
        <h3 style="color: #aaa; font-weight: normal;">Live Crash Result</h3>
        <div class="multiplier">{{ crash }}x</div>
        <p style="color: #666; font-size: 14px;">(Refresh page for next round)</p>
    </div>
    <div id="toast"></div>

    <script>
        function showMsg(action) {
            var toast = document.getElementById("toast");
            var isMaintenance = "{{ maintenance }}";
            
            if (isMaintenance === "ON") {
                if (action === 'deposit') { toast.innerText = "{{ dep_msg }}"; }
                else { toast.innerText = "{{ with_msg }}"; }
            } else {
                toast.innerText = "✅ Redirecting to secure payment gateway...";
            }
            
            toast.className = "show";
            setTimeout(function(){ toast.className = toast.className.replace("show", ""); }, 3000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    if SETTINGS["mode"] == "auto":
        SETTINGS["current_crash"] = round(random.uniform(1.10, 5.50), 2)
    return render_template_string(HTML_PAGE, 
                                  crash=SETTINGS["current_crash"],
                                  maintenance=SETTINGS["maintenance_mode"],
                                  dep_msg=SETTINGS["deposit_msg"],
                                  with_msg=SETTINGS["withdraw_msg"])

@app.route('/api/prediction')
def get_prediction():
    return jsonify({"prediction": SETTINGS["current_crash"]})

@app.route('/api/settings', methods=['GET', 'POST'])
def update_settings():
    if request.method == 'POST':
        data = request.json
        for key in data:
            if key in SETTINGS:
                SETTINGS[key] = data[key]
        return jsonify({"status": "success"})
    return jsonify(SETTINGS)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
  
