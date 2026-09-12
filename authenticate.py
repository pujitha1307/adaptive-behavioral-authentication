import os
import pandas as pd
import numpy as np
import joblib
from extract_features import extract

MODEL_PATH = "model/user_01.pkl"
SCALER_PATH = "model/scaler.pkl"

def compute_risk(csv_file, window_size=120):
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        return {"risk": 0.0, "confidence": 100.0}

    if isinstance(csv_file, str):
        if not os.path.exists(csv_file):
            return {"risk": 0.0, "confidence": 100.0}
        try:
            df = pd.read_csv(csv_file, names=["t", "x", "y"])
            if len(df) > window_size:
                df = df.tail(window_size)
        except Exception:
            return {"risk": 0.0, "confidence": 100.0}
    elif isinstance(csv_file, pd.DataFrame):
        df = csv_file.tail(window_size)
    else:
        return {"risk": 0.0, "confidence": 100.0}

    if len(df) < 5:
        return {"risk": 0.0, "confidence": 100.0}

    scaler = joblib.load(SCALER_PATH)
    model = joblib.load(MODEL_PATH)

    X = extract(df, scaler=scaler)
    if len(X) == 0:
        return {"risk": 0.0, "confidence": 100.0}

    # Evaluate exact IsolationForest anomaly scores
    scores = model.decision_function(X)
    mean_score = float(np.mean(scores))

    # Exact Sigmoidal Confidence Mapping derived from baseline distribution:
    # Baseline inlier score mean ≈ 0.12 -> Confidence ~ 85%
    # Score 0.02 -> Confidence ~ 40% (Risk 60% -> OTP)
    # Score -0.07 -> Confidence ~ 9% (Risk 91% -> High Risk)
    k = 22.0
    s_mid = 0.04
    confidence = 100.0 / (1.0 + np.exp(-k * (mean_score - s_mid)))

    confidence = float(max(1.0, min(99.0, confidence)))
    risk = float(100.0 - confidence)

    return {
        "risk": round(risk, 2),
        "confidence": round(confidence, 2)
    }
