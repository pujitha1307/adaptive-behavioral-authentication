# 🛡️ Adaptive Behavioral Authentication System

A state-of-the-art **Continuous Behavioral Biometrics Authentication** system that monitors mouse movement dynamics in real time to evaluate user authenticity.

Instead of relying solely on one-time login credentials, this system applies **unsupervised Machine Learning (IsolationForest)** to continuously evaluate **speed, acceleration, and jerk**. It dynamically computes a **Confidence Score (%)** and **Risk Score (%)**, enforcing adaptive step-up security controls (OTP & Credential Re-authentication with Specified Reasons) whenever anomalous behavior is detected.

---

## 🌟 Key Features

- 🖱️ **Continuous Mouse Biometrics Tracking**
  - Captures spatial coordinates \((x, y)\) and timestamps \((t)\) in 10-second evaluation windows.
  - Extracts 2nd & 3rd order derivative features: **Velocity/Speed**, **Acceleration**, and **Jerk**.

- 🧠 **Machine Learning Anomaly Engine**
  - Powered by `scikit-learn` **IsolationForest** combined with persistent **StandardScaler** feature normalization.
  - Trained on baseline human mouse trajectory patterns to identify subtle behavioral deviations.

- 📈 **Exact Confidence & Risk Score Computation**
  - Maps model decision function scores via sigmoidal transformation into exact **Confidence (%)** and **Risk (%)** metrics.
  - Smooth real-time risk progress bar with dynamic color transitions (Green \(\rightarrow\) Amber \(\rightarrow\) Red).

- 🔐 **Adaptive Multi-Tiered Step-Up Security**
  - **Low Risk (<60% / Confidence >40%)**: Seamless background monitoring.
  - **Medium Risk (60% – 90%)**: **Sticky OTP Verification** prompt (OTP logged to terminal/file).
  - **High Risk (>90% / Confidence <10%)**: **Sticky Modal Screen Lock** requiring **Specified Reason Dropdown** selection + **Username & Password Re-authentication**.

- 🎨 **Modern Glassmorphism & Telemetry Visualizer UI**
  - Live HTML5 Canvas glowing neon trail visualizer displaying mouse motion vectors in real time.
  - Sleek dark-mode glassmorphism interface with active telemetry metrics.

---

## 🔐 Risk Thresholds & Action Matrix

| Risk Score | Confidence Score | System Status | Security Action Taken |
|---|---|---|---|
| **`< 60%`** | **`> 40%`** | `AUTHENTICATED` | **Normal Session**: Uninterrupted monitoring in background. |
| **`60% – 90%`** | **`10% – 40%`** | `OTP_REQUIRED` | **Step-Up OTP**: Sticky prompt asking for 6-digit OTP logged to terminal. |
| **`> 90%`** | **`< 10%`** | `HIGH_RISK_WARNING` | **Critical Lockout**: Must select specified reason from dropdown & re-enter credentials (`user_01` / `password123`). |

---

## 🛠️ Tech Stack

- **Backend Framework:** Python 3, Flask
- **Machine Learning & Data Science:** `scikit-learn` (`IsolationForest`, `StandardScaler`), `pandas`, `numpy`, `joblib`
- **Frontend Technologies:** HTML5, Vanilla CSS (Glassmorphism design system), JavaScript (HTML5 Canvas Trail Rendering, Fetch API)

---

## 📂 Project Structure

```text
adaptive-behavioral-authentication/
│
├── app.py                  # Flask routing, session state management & endpoints
├── authenticate.py         # Anomaly scoring & sigmoidal risk/confidence mapping
├── extract_features.py     # Biometric feature extraction (speed, acceleration, jerk)
├── train_model.py          # ML model & StandardScaler training script
├── requirements.txt        # Dependencies list
│
├── model/
│   ├── user_01.pkl         # Trained IsolationForest anomaly detection model
│   └── scaler.pkl          # Trained StandardScaler normalization model
│
├── dataset/
│   └── user_01/
│       ├── baseline.csv    # Initial baseline training trajectory
│       ├── session_live.csv# Real-time session coordinate logs
│       ├── latest_otp.txt  # Secure OTP log
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

## ▶️ How to Run the Project Locally

### 1️⃣ Clone the repository
```bash
git clone https://github.com/pujitha1307/adaptive-behavioral-authentication.git
cd adaptive-behavioral-authentication
```

### 2️⃣ Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Train the Machine Learning Model & Scaler
```bash
python train_model.py
```
*Output:*
```text
Generating representative baseline training dataset for user_01...
✅ Model trained successfully and saved to: model/user_01.pkl
✅ Scaler fitted and saved to: model/scaler.pkl
```

### 5️⃣ Launch the Application
```bash
python app.py
```

### 6️⃣ Open in Browser
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

---

## 🔑 Default Test Credentials

When testing **High Risk (>90%) Re-authentication**:
- **Username:** `user_01`
- **Password:** `password123`

---

## 🧪 Testing the Behavioral Biometrics Engine

1. **Normal Movement (<60% Risk)**: Move your mouse smoothly and naturally across the window. Status remains `Authenticated (Normal)`.
2. **OTP Step-Up (60% – 90% Risk)**: Move the cursor at varying speed. When risk crosses 60%, a sticky OTP prompt appears. Check your terminal output or `dataset/user_01/latest_otp.txt` for the 6-digit OTP code.
3. **High Risk Re-Authentication (>90% Risk)**: Shake the mouse rapidly back and forth. The screen locks with a critical warning modal requiring you to select a reason from the dropdown and enter `user_01` / `password123`.

---

## 👩‍💻 Author

**Pujitha Raju**  
Computer Science Engineering Student  
*Interested in AI-driven Security, Data Systems, and Behavioral Biometrics*
