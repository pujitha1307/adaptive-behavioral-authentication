# 🛡️ Adaptive Behavioral Authentication System

A state-of-the-art **Continuous Behavioral Biometrics Authentication** web application that monitors mouse dynamics in real time to evaluate user authenticity.

Instead of relying solely on static credentials, this system applies **unsupervised Machine Learning (IsolationForest)** to continuously evaluate **speed, acceleration, and jerk**. It dynamically computes a **Confidence Score (%)** and **Risk Score (%)**, enforcing adaptive step-up security controls (OTP & Credential Re-authentication with Specified Reasons) whenever anomalous behavior is detected.

---

## 🚀 Key Features

- 🖱️ **Continuous Mouse Biometrics Tracking**
  - Captures spatial coordinates \((x, y)\) and timestamps \((t)\) in 10-second evaluation windows.
  - Extracts 2nd & 3rd order derivative features: **Velocity/Speed**, **Acceleration**, and **Jerk**.

- 🧠 **Machine Learning Anomaly Engine**
  - Powered by `scikit-learn` **IsolationForest** combined with persistent **StandardScaler** feature normalization.
  - Trained on baseline human mouse trajectory patterns to identify subtle behavioral deviations.

- 📊 **Exact Confidence & Risk Score Computation**
  - Maps model decision function scores via sigmoidal transformation into exact **Confidence (%)** and **Risk (%)** metrics.
  - Smooth real-time risk progress bar with dynamic color transitions (Green \(\rightarrow\) Amber \(\rightarrow\) Red).

- 🔐 **Debounced & Adaptive Multi-Tiered Step-Up Security**
  - **Low Risk (< Medium Threshold)**: Background monitoring with zero user disruption.
  - **Medium Risk (Medium – High Threshold)**: **Debounced OTP Verification** (requires 3 consecutive medium-risk evaluation windows before locking to prevent false positives; 5-attempt max lockout).
  - **High Risk (≥ High Threshold)**: **Immediate Sticky Screen Lock** requiring **Specified Reason Dropdown** selection + **Password Re-authentication** (`user_01` / `password123`).

- 🧪 **Automated Testing & CI/CD Pipeline**
  - Integrated `pytest` suite testing feature extraction, false-positive debounce counters, OTP lifecycle, max-attempt lockout, and input validation.
  - GitHub Actions CI workflow running automated builds on every push.

- 🎨 **Modern Glassmorphism & Telemetry Visualizer UI**
  - Live HTML5 Canvas glowing neon trail visualizer displaying mouse motion vectors in real time.
  - Sleek dark-mode glassmorphism interface with active telemetry metrics.

---

## 📊 Data-Derived Risk Thresholds & Model Evaluation

Risk score boundaries and sigmoidal mapping parameters are data-derived directly from the training set score distribution in `train_model.py`. After fitting the `IsolationForest` model on baseline telemetry, `model.decision_function()` is evaluated across the training samples to compute the baseline mean decision score (`s_mean`), which is set as the sigmoid midpoint (`s_mid`). The medium and high risk decision boundaries are computed by evaluating the 15th percentile (`s_p15`) and 2nd percentile (`s_p02`) of the user's baseline score distribution through the fitted sigmoid equation: `medium_risk_threshold = 100 - sigmoid(s_p15)` and `high_risk_threshold = 100 - sigmoid(s_p02)`. These values are saved to `model/thresholds.json`. In `train_model.py`, 20% of the baseline telemetry sequence is held out as an unseen validation set to compute the **False Positive Rate (FPR)**, saved alongside training sample sizes to `model/metrics.json` and logged during build pipelines. `authenticate.py` dynamically loads these data-derived parameters in memory rather than relying on hardcoded guesses.

---

## 🔐 Risk Thresholds & Action Matrix

| Risk Score | System Status | Security Action & Debounce Requirement |
|---|---|---|
| **`< Medium Threshold`** | `AUTHENTICATED` | **Normal Session**: Uninterrupted background monitoring. Resets debounce counter to 0. |
| **`Medium – High Threshold`** | `OTP_REQUIRED` | **Debounced Step-Up OTP**: Requires **3 consecutive medium-risk windows** to trigger sticky 6-digit OTP prompt. 5 max failed attempts lockout. |
| **`≥ High Threshold`** | `HIGH_RISK_WARNING` | **Immediate Lockout**: Bypasses debounce. Must select specified reason from dropdown & re-enter credentials (`user_01` / `password123`). |

---

## 🛠️ Tech Stack

- **Backend Framework:** Python 3.9+, Flask, `python-dotenv`, `Werkzeug` (PBKDF2 SHA-256 Password Hashing)
- **Machine Learning & Data Science:** `scikit-learn` (`IsolationForest`, `StandardScaler`), `pandas`, `numpy`, `joblib`
- **Testing & CI:** `pytest`, `pytest-flask`, GitHub Actions
- **Production Server:** `gunicorn`
- **Frontend Technologies:** HTML5, Vanilla CSS (Glassmorphism design system), JavaScript (HTML5 Canvas Trail Rendering, Fetch API)

---

## 📂 Project Structure

```text
adaptive-behavioral-authentication/
│
├── app.py                  # Flask routing, session-scoped state, debounce & endpoints
├── authenticate.py         # Anomaly scoring & sigmoidal risk/confidence mapping
├── extract_features.py     # Biometric feature extraction (speed, acceleration, jerk)
├── train_model.py          # ML model & StandardScaler training script
├── test_app.py             # Pytest automated unit test suite
├── Procfile                # Production deployment configuration (Gunicorn)
├── .env.example            # Environment configuration template
├── requirements.txt        # Core production dependencies
├── requirements-dev.txt    # Developer & testing dependencies
│
├── .github/
│   └── workflows/
│       └── test.yml        # GitHub Actions CI workflow
│
├── model/
│   ├── user_01.pkl         # Trained IsolationForest anomaly detection model
│   ├── scaler.pkl          # Trained StandardScaler normalization model
│   ├── thresholds.json     # Data-derived score thresholds & parameters
│   └── metrics.json        # Validation metrics (sample counts, false positive rate)
│
├── dataset/
│   └── user_01/
│       ├── baseline.csv    # Initial baseline training trajectory
│       ├── session_live.csv# Real-time session coordinate logs
│       └── security_reasons.txt # Audit logs of submitted reasons & re-authentications
│
├── static/
│   └── mouse.js            # Real-time mouse tracking, trail canvas visualizer & risk gauge
│
└── templates/
    ├── login.html          # Secure landing / pre-session authentication UI
    └── dashboard.html     # Real-time continuous biometrics monitoring dashboard
```

---

## ▶️ How to Run Locally

### 1️⃣ Clone the repository & setup environment
```bash
git clone https://github.com/pujitha1307/adaptive-behavioral-authentication.git
cd adaptive-behavioral-authentication

python3 -m venv venv
source venv/bin/activate   # macOS / Linux
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### 3️⃣ Train the Machine Learning Model & Scaler
```bash
python train_model.py
```

### 4️⃣ Run Automated Test Suite
```bash
pytest -v
```

### 5️⃣ Launch Application
```bash
python app.py
```
Open browser: 👉 **`http://127.0.0.1:8000`**

---

## 🔑 Default Test Credentials

When testing **High Risk Re-authentication**:
- **Username:** `user_01`
- **Password:** `password123`

---

## ⚠️ Known Limitations & Deployment Notes

- **Single-Tenant Model for Demo**: The live project and local demo are configured around a single baseline user (`user_01`) to demonstrate real-time telemetry extraction, scoring, and step-up auth without requiring complex multi-tenant onboarding.
- **Environment Variables**: Local development configuration uses `.env` (derived from `.env.example`). Never commit production secrets or actual `.env` files to git.

---

## 👩‍💻 Author

**Pujitha Raju**  
Computer Science Engineering Student  
*Interested in AI-driven Security, Data Systems, and Behavioral Biometrics*
