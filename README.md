# Adaptive Behavioral Authentication System

A **continuous authentication system** that uses **behavioral biometrics (mouse dynamics)** to verify users in real time.  
Instead of relying only on passwords, the system continuously monitors user behavior and applies **adaptive risk scoring** with **OTP-based step-up authentication** when suspicious activity is detected.

This approach improves security while maintaining a smooth user experience.

---

## 🚀 Key Features

- 🖱️ **Mouse Dynamics-Based Authentication**
  - Captures real-time mouse movement data (x, y, timestamp)
  - Extracts behavioral features such as speed and acceleration

- 📊 **Live Risk Scoring**
  - Machine learning model evaluates user behavior continuously
  - Risk score updates in real time during browsing

- 🔐 **Adaptive OTP Authentication**
  - OTP is triggered only when suspicious behavior is detected
  - Prevents unnecessary interruptions for genuine users

- 🔄 **Continuous Authentication**
  - Authentication is not one-time (unlike passwords)
  - Session is monitored throughout the interaction

---

## 🧠 How the System Works

1. The user logs in and starts interacting with the application.
2. Mouse movements are captured continuously on the frontend.
3. Mouse data is sent to the backend in real time.
4. Behavioral features (speed, acceleration) are extracted.
5. A trained machine learning model computes a **risk score**.
6. Based on the risk score:
   - Low risk → user remains authenticated
   - Medium risk → OTP verification is required
   - High risk → session is blocked

---

## 🔐 Risk-Based Authentication Logic

| Risk Score Range | Action Taken |
|------------------|--------------|
| `< 40` | Authenticated (Genuine User) |
| `40 – 70` | OTP Verification Required |
| `> 70` | Session Blocked |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask  
- **Frontend:** HTML, JavaScript  
- **Machine Learning:** scikit-learn, NumPy, Pandas  
- **Behavioral Biometrics:** Mouse dynamics  
- **Authentication:** Risk-based + OTP  
- **Version Control:** Git, GitHub  

---

## 📂 Project Structure

```text
adaptive-behavioral-authentication/
│
├── app.py                  # Flask app and routing
├── authenticate.py         # Risk scoring & OTP logic
├── extract_features.py     # Mouse feature extraction
├── train_model.py          # ML model training
│
├── static/
│   └── mouse.js            # Mouse movement capture
│
├── templates/
│   ├── login.html          # Pre-entry authentication UI
│   └── dashboard.html     # Authenticated dashboard
│
├── .gitignore
└── README.md
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
python -m venv venv
source venv/bin/activate   # macOS / Linux
```

### 3️⃣ Install dependencies
```bash
pip install flask pandas numpy scikit-learn joblib
```

### 4️⃣ Run the application
```bash
python app.py
```

### 5️⃣ Open in browser
```
http://127.0.0.1:8000
```

Move your mouse naturally to observe **live risk score updates**.

---

## 🌟 Why This Project Stands Out

- Uses behavioral biometrics, not static credentials  
- Implements continuous authentication  
- Reduces false positives using adaptive OTP  
- Reflects real-world enterprise security systems  
- Combines Machine Learning + Full Stack + Security  

---

## 🔮 Future Enhancements

- Email/SMS-based OTP delivery  
- Multi-user enrollment and profiles  
- Cloud deployment (AWS / Render)  
- Additional behavioral signals (keystroke dynamics)

---

## 👩‍💻 Author

**Pujitha Raju**  
Computer Science Engineering Student  
Interested in AI-driven security, data systems, and product-focused solutions
