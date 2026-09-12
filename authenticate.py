import os
import logging
import pandas as pd
import numpy as np
import joblib
from extract_features import extract

logger = logging.getLogger(__name__)

MODEL_PATH = "model/user_01.pkl"
SCALER_PATH = "model/scaler.pkl"

def compute_risk(csv_file, window_size=120):
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        logger.warning("Model or Scaler file not found. Defaulting risk to 0.0, confidence to 100.0.")
        return {"risk": 0.0, "confidence": 100.0}

    if isinstance(csv_file, str):
        if not os.path.exists(csv_file):
            return {"risk": 0.0, "confidence": 100.0}
        try:
            df = pd.read_csv(csv_file, names=["t", "x", "y"])
            if len(df) > window_size:
                df = df.tail(window_size)
        except Exception as e:
            logger.error("Error reading csv telemetry file %s: %s", csv_file, e)
            return {"risk": 0.0, "confidence": 100.0}
    elif isinstance(csv_file, pd.DataFrame):
        df = csv_file.tail(window_size)
    else:
        return {"risk": 0.0, "confidence": 100.0}

    if len(df) < 5:
        return {"risk": 0.0, "confidence": 100.0}

    try:
        scaler = joblib.load(SCALER_PATH)
        model = joblib.load(MODEL_PATH)
    except Exception as e:
        logger.error("Failed to load model artifacts: %s", e)
        return {"risk": 0.0, "confidence": 100.0}

    X = extract(df, scaler=scaler)
    if len(X) == 0:
        return {"risk": 0.0, "confidence": 100.0}

    scores = model.decision_function(X)
    mean_score = float(np.mean(scores))

    # Exact Sigmoidal Confidence Mapping derived from baseline distribution
    k = 22.0
    s_mid = 0.04
    confidence = 100.0 / (1.0 + np.exp(-k * (mean_score - s_mid)))

    confidence = float(max(1.0, min(99.0, confidence)))
    risk = float(100.0 - confidence)

    return {
        "risk": round(risk, 2),
        "confidence": round(confidence, 2)
    }
