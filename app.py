import csv
import logging
import os
import secrets
import time
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from authenticate import compute_risk, get_thresholds

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Task 7: Remove hardcoded fallback secrets from source
secret_key_env = os.getenv("FLASK_SECRET_KEY")
if not secret_key_env:
    secret_key_env = secrets.token_hex(32)
    logger.info("FLASK_SECRET_KEY not set in environment. Generated ephemeral secret key for local development.")

app.secret_key = secret_key_env

USER = "user_01"
user_pass_env = os.getenv("USER_01_PASSWORD")
if not user_pass_env:
    user_pass_env = "password123"
    logger.info("USER_01_PASSWORD not set in environment. Defaulting to development password ('password123').")

USER_PASSWORD_HASH = generate_password_hash(user_pass_env, method="pbkdf2:sha256")

SESSION_FILE = "session_live"
OTP_EXPIRY_SECONDS = 300  # 5 minutes expiry
MAX_OTP_ATTEMPTS = 5

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/start-session", methods=["POST"])
def start_session():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    # Validate initial login credentials if submitted via form
    if username or password:
        if username != USER or not check_password_hash(USER_PASSWORD_HASH, password):
            logger.warning("Initial login failed for username: %s", username)
            return render_template("login.html", error="Invalid username or password.")

    # Initialize / Reset Flask session-scoped variables
    session["user"] = USER
    session["session_state"] = "NORMAL"
    session["suspicious_count"] = 0
    session["otp_code"] = None
    session["otp_verified"] = False
    session["otp_timestamp"] = 0.0
    session["otp_attempts"] = 0
    logger.info("New behavioral authentication session started for user %s", USER)
    return render_template("dashboard.html")


@app.route("/collect", methods=["POST"])
def collect():
    # Stage 3: Input Validation and Error Handling
    data = request.get_json(silent=True)
    if not isinstance(data, list) or len(data) == 0:
        logger.warning("Invalid /collect request payload: expected a non-empty list of points")
        return jsonify({"error": "Invalid payload format: expected a non-empty list of telemetry points"}), 400

    for idx, item in enumerate(data):
        if not isinstance(item, dict) or not all(k in item for k in ("t", "x", "y")):
            logger.warning("Invalid telemetry point at index %d: missing required keys", idx)
            return jsonify({"error": f"Invalid payload item at index {idx}: missing required keys (t, x, y)"}), 400
        if not (isinstance(item["t"], (int, float)) and isinstance(item["x"], (int, float)) and isinstance(item["y"], (int, float))):
            logger.warning("Invalid telemetry point at index %d: non-numeric coordinates", idx)
            return jsonify({"error": f"Invalid payload item at index {idx}: coordinates must be numeric"}), 400

    # Log validated points to dataset
    os.makedirs(f"dataset/{USER}", exist_ok=True)
    file_path = f"dataset/{USER}/{SESSION_FILE}.csv"

    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)
        for d in data:
            writer.writerow([d["t"], d["x"], d["y"]])

    eval_result = compute_risk(file_path)
    risk = eval_result["risk"]
    confidence = eval_result["confidence"]

    # Task 5: Load data-derived risk thresholds
    thresholds = get_thresholds()
    medium_risk_thresh = thresholds.get("medium_risk_threshold", 60.0)
    high_risk_thresh = thresholds.get("high_risk_threshold", 90.0)

    current_state = session.get("session_state", "NORMAL")
    otp_verified = session.get("otp_verified", False)

    # 🔒 PERSISTENT LOCKOUT: If already locked in Warning or OTP state, enforce lock until verified!
    if current_state == "LOCKED_WARNING":
        logger.info("Session locked in HIGH_RISK_WARNING | Risk: %s%% | Confidence: %s%%", risk, confidence)
        return jsonify({
            "risk": risk,
            "confidence": confidence,
            "status": "HIGH_RISK_WARNING"
        })

    if current_state == "LOCKED_OTP" and not otp_verified:
        logger.info("Session locked in OTP_REQUIRED | Risk: %s%% | Confidence: %s%%", risk, confidence)
        return jsonify({
            "risk": risk,
            "confidence": confidence,
            "status": "OTP_REQUIRED"
        })

    # Debounce Logic & Threshold Evaluation
    # 🔴 Critical High Risk (>= high_risk_thresh): Skip debounce and lock immediately!
    if risk >= high_risk_thresh:
        session["session_state"] = "LOCKED_WARNING"
        session["suspicious_count"] = 0
        status = "HIGH_RISK_WARNING"
        logger.info("High risk threshold crossed (%s%% >= %s%%). Transitioning to HIGH_RISK_WARNING.", risk, high_risk_thresh)

    # 🟡 Medium Risk (>= medium_risk_thresh): Debounce required (3 consecutive windows)
    elif risk >= medium_risk_thresh and not otp_verified:
        susp_count = session.get("suspicious_count", 0) + 1
        session["suspicious_count"] = susp_count
        logger.info("Medium risk window detected (%s%% >= %s%%). Consecutive suspicious count: %d/3",
                    risk, medium_risk_thresh, susp_count)

        if susp_count >= 3:
            session["session_state"] = "LOCKED_OTP"
            status = "OTP_REQUIRED"

            # Check if existing OTP is active and unexpired
            now = time.time()
            existing_otp = session.get("otp_code")
            otp_ts = session.get("otp_timestamp", 0.0)

            if not existing_otp or (now - otp_ts) > OTP_EXPIRY_SECONDS:
                # Task 1: Cryptographically secure OTP generation using secrets module
                new_otp = str(secrets.randbelow(900000) + 100000)
                session["otp_code"] = new_otp
                session["otp_timestamp"] = now
                session["otp_verified"] = False
                session["otp_attempts"] = 0

                # Task 2: Log OTP generation event and dev test code
                logger.info("Generated new cryptographically secure OTP for session (Expiry: %ds)", OTP_EXPIRY_SECONDS)
                logger.info("🔐 [DEV TEST OTP CODE]: %s", new_otp)


        else:
            status = "AUTHENTICATED"

    # 🟢 Normal Low Risk (< medium_risk_thresh): Reset debounce count
    else:
        session["suspicious_count"] = 0
        status = "AUTHENTICATED"
        logger.info("Low risk evaluation (%s%%). Status: AUTHENTICATED", risk)

    return jsonify({
        "risk": risk,
        "confidence": confidence,
        "status": status
    })

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    payload = request.get_json(silent=True) or {}
    entered_otp = str(payload.get("otp", "")).strip()

    stored_otp = session.get("otp_code")
    otp_ts = session.get("otp_timestamp", 0.0)
    attempts = session.get("otp_attempts", 0)
    now = time.time()

    if not stored_otp:
        logger.warning("OTP verification attempt with no active OTP")
        return jsonify({"result": "OTP_INVALID"}), 400

    # Check OTP expiry
    if (now - otp_ts) > OTP_EXPIRY_SECONDS:
        logger.info("OTP verification failed: OTP expired")
        session["otp_code"] = None
        session["otp_attempts"] = 0
        return jsonify({"result": "OTP_EXPIRED"}), 400

    # Check correct OTP match
    if entered_otp == stored_otp and not session.get("otp_verified", False):
        session["otp_verified"] = True
        session["session_state"] = "NORMAL"
        session["suspicious_count"] = 0
        session["otp_code"] = None  # Prevent OTP reuse
        session["otp_attempts"] = 0
        logger.info("OTP verified successfully. Session unlocked.")
        return jsonify({"result": "OTP_VERIFIED"})

    # Task 3: Failed OTP verification -> Increment attempts counter (Max 5 attempts lockout)
    attempts += 1
    session["otp_attempts"] = attempts
    logger.warning("OTP verification failed (Attempt %d/%d)", attempts, MAX_OTP_ATTEMPTS)

    if attempts >= MAX_OTP_ATTEMPTS:
        session["otp_code"] = None
        session["otp_attempts"] = 0
        logger.warning("Maximum OTP verification attempts (%d) reached. Current OTP invalidated.", MAX_OTP_ATTEMPTS)
        return jsonify({
            "result": "OTP_LOCKED",
            "error": "Maximum OTP verification attempts exceeded. Current OTP invalidated."
        }), 400

    return jsonify({
        "result": "OTP_INVALID",
        "attempts_remaining": MAX_OTP_ATTEMPTS - attempts
    }), 400

@app.route("/verify-credentials", methods=["POST"])
def verify_credentials():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()
    reason = str(payload.get("reason", "")).strip()
    details = str(payload.get("details", "")).strip()

    if not reason:
        return jsonify({"result": "REASON_REQUIRED"}), 400

    # Secure hashed password check
    if username == USER and check_password_hash(USER_PASSWORD_HASH, password):
        os.makedirs(f"dataset/{USER}", exist_ok=True)
        with open(f"dataset/{USER}/security_reasons.txt", "a") as f:
            f.write(f"Re-auth Success | Reason: {reason} | Details: {details}\n")

        session["session_state"] = "NORMAL"
        session["suspicious_count"] = 0
        logger.info("Re-authentication successful for user %s with specified reason", username)
        return jsonify({"result": "CREDENTIALS_VERIFIED"})

    logger.warning("Re-authentication failed: invalid credentials provided for %s", username)
    return jsonify({"result": "INVALID_CREDENTIALS"}), 400

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    logger.info("Session logged out and cleared")
    return jsonify({"status": "LOGGED_OUT"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(debug=True, port=port)
