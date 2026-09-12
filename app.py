from flask import Flask, render_template, request
import csv
import os
import random
from authenticate import compute_risk

app = Flask(__name__)

USER = "user_01"
PASSWORD = "password123"
SESSION = "session_live"

# 🔐 Session Security State: "NORMAL", "LOCKED_OTP", "LOCKED_WARNING"
otp_code = None
otp_verified = False
session_state = "NORMAL"

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/start-session", methods=["POST"])
def start_session():
    global otp_code, otp_verified, session_state
    otp_code = None
    otp_verified = False
    session_state = "NORMAL"
    return render_template("dashboard.html")

@app.route("/collect", methods=["POST"])
def collect():
    global otp_code, otp_verified, session_state

    os.makedirs(f"dataset/{USER}", exist_ok=True)
    file_path = f"dataset/{USER}/{SESSION}.csv"

    data = request.json
    if data:
        with open(file_path, "a", newline="") as f:
            writer = csv.writer(f)
            for d in data:
                writer.writerow([d["t"], d["x"], d["y"]])

    eval_result = compute_risk(file_path)
    risk = eval_result["risk"]
    confidence = eval_result["confidence"]

    # 🔒 PERSISTENT LOCKOUT: If already locked in Warning or OTP state, enforce lock until verified!
    if session_state == "LOCKED_WARNING":
        return {
            "risk": risk,
            "confidence": confidence,
            "status": "HIGH_RISK_WARNING"
        }

    if session_state == "LOCKED_OTP" and not otp_verified:
        return {
            "risk": risk,
            "confidence": confidence,
            "status": "OTP_REQUIRED"
        }

    # Evaluate new risk thresholds
    # 🔴 Critical High Risk (> 90%): Lock in Warning state requiring Re-Authentication
    if risk >= 90:
        session_state = "LOCKED_WARNING"
        status = "HIGH_RISK_WARNING"

    # 🟡 Suspicious (>= 60%): Lock in OTP state
    elif risk >= 60 and not otp_verified:
        session_state = "LOCKED_OTP"
        status = "OTP_REQUIRED"
        if otp_code is None:
            otp_code = random.randint(100000, 999999)
            print("\n==========================================")
            print(f"🔐 SECURITY OTP GENERATED FOR USER_01: {otp_code}")
            print("==========================================\n")
            with open(f"dataset/{USER}/latest_otp.txt", "w") as f:
                f.write(str(otp_code))

    # 🟢 Normal (< 60%)
    else:
        status = "AUTHENTICATED"

    return {
        "risk": risk,
        "confidence": confidence,
        "status": status
    }

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    global otp_verified, session_state
    entered_otp = request.json.get("otp")

    try:
        if otp_code and int(entered_otp) == otp_code:
            otp_verified = True
            session_state = "NORMAL"
            return {"result": "OTP_VERIFIED"}
    except (ValueError, TypeError):
        pass

    return {"result": "OTP_INVALID"}

@app.route("/verify-credentials", methods=["POST"])
def verify_credentials():
    global session_state
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    reason = data.get("reason", "").strip()
    details = data.get("details", "").strip()

    if not reason:
        return {"result": "REASON_REQUIRED"}

    if username == USER and password == PASSWORD:
        os.makedirs(f"dataset/{USER}", exist_ok=True)
        with open(f"dataset/{USER}/security_reasons.txt", "a") as f:
            f.write(f"Re-auth Success | Reason: {reason} | Details: {details}\n")

        # Unlock session state after valid credentials + reason provided
        session_state = "NORMAL"
        return {"result": "CREDENTIALS_VERIFIED"}

    return {"result": "INVALID_CREDENTIALS"}

@app.route("/logout", methods=["POST"])
def logout():
    global otp_code, otp_verified, session_state

    # Reset session state
    otp_code = None
    otp_verified = False
    session_state = "NORMAL"

    return {"status": "LOGGED_OUT"}

if __name__ == "__main__":
    app.run(debug=True, port=8000)
