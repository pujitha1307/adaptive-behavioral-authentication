from flask import Flask, render_template, request
import csv
import os
import random
from authenticate import compute_risk

app = Flask(__name__)

USER = "user_01"
SESSION = "session_live"

# 🔐 Session state
otp_code = None
otp_verified = False
suspicious_count = 0

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/start-session", methods=["POST"])
def start_session():
    return render_template("dashboard.html")

@app.route("/collect", methods=["POST"])
def collect():
    global otp_code, otp_verified, suspicious_count

    os.makedirs(f"dataset/{USER}", exist_ok=True)
    file_path = f"dataset/{USER}/{SESSION}.csv"

    data = request.json
    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)
        for d in data:
            writer.writerow([d["t"], d["x"], d["y"]])

    risk = compute_risk(file_path)

    response = {
        "risk": risk,
        "status": "AUTHENTICATED"
    }

    # 🔴 High risk
    if risk >= 70:
        response["status"] = "BLOCKED"
        suspicious_count = 0

    # 🟡 Suspicious (persistent)
    elif risk >= 40 and not otp_verified:
        suspicious_count += 1

        if suspicious_count >= 3:
            response["status"] = "OTP_REQUIRED"
            if otp_code is None:
                otp_code = random.randint(100000, 999999)
                print("🔐 Generated OTP:", otp_code)
        else:
            response["status"] = "AUTHENTICATED"

    # 🟢 Normal
    else:
        suspicious_count = 0

    return response

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    global otp_verified
    entered_otp = int(request.json.get("otp"))

    if entered_otp == otp_code:
        otp_verified = True
        return {"result": "OTP_VERIFIED"}
    else:
        return {"result": "OTP_INVALID"}

@app.route("/logout", methods=["POST"])
def logout():
    global otp_code, otp_verified, suspicious_count

    # Reset session state
    otp_code = None
    otp_verified = False
    suspicious_count = 0

    return {"status": "LOGGED_OUT"}

if __name__ == "__main__":
    app.run(debug=True, port=8000)
