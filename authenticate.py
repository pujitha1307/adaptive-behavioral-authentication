import os
import json
import logging
import pandas as pd
import numpy as np
import joblib
from extract_features import extract

logger = logging.getLogger(__name__)

MODEL_PATH = "model/user_01.pkl"
SCALER_PATH = "model/scaler.pkl"
THRESHOLDS_PATH = "model/thresholds.json"

# Task 4: In-Memory Caching for Model, Scaler, and Thresholds
_CACHE = {
    "model": None,
    "model_mtime": 0.0,
    "scaler": None,
    "scaler_mtime": 0.0,
    "thresholds": None,
    "thresholds_mtime": 0.0
}

def get_thresholds():
    """Load and return data-derived risk thresholds from cached thresholds.json."""
    if not os.path.exists(THRESHOLDS_PATH):
        return {
            "medium_risk_threshold": 60.0,
            "high_risk_threshold": 90.0,
            "s_mid": 0.04,
            "k": 22.0
        }

    try:
        mtime = os.path.getmtime(THRESHOLDS_PATH)
        if _CACHE["thresholds"] is None or _CACHE["thresholds_mtime"] < mtime:
            with open(THRESHOLDS_PATH, "r") as f:
                _CACHE["thresholds"] = json.load(f)
            _CACHE["thresholds_mtime"] = mtime
        return _CACHE["thresholds"]
    except Exception as e:
        logger.warning("Could not read thresholds.json: %s", e)
        return {
            "medium_risk_threshold": 60.0,
            "high_risk_threshold": 90.0,
            "s_mid": 0.04,
            "k": 22.0
        }

def _get_model_and_scaler():
    """Task 4: Load model and scaler with in-memory caching based on file mtime."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        return None, None

    try:
        model_mtime = os.path.getmtime(MODEL_PATH)
        scaler_mtime = os.path.getmtime(SCALER_PATH)

        if _CACHE["model"] is None or _CACHE["model_mtime"] < model_mtime:
            _CACHE["model"] = joblib.load(MODEL_PATH)
            _CACHE["model_mtime"] = model_mtime

        if _CACHE["scaler"] is None or _CACHE["scaler_mtime"] < scaler_mtime:
            _CACHE["scaler"] = joblib.load(SCALER_PATH)
            _CACHE["scaler_mtime"] = scaler_mtime

        return _CACHE["model"], _CACHE["scaler"]
    except Exception as e:
        logger.error("Error loading cached model assets: %s", e)
        return None, None

def compute_risk(csv_file, window_size=120):
    thresholds = get_thresholds()
    s_mid = thresholds.get("s_mid", 0.04)
    k = thresholds.get("k", 22.0)

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

    model, scaler = _get_model_and_scaler()
    if model is None or scaler is None:
        return {"risk": 0.0, "confidence": 100.0}

    X = extract(df, scaler=scaler)
    if len(X) == 0:
        return {"risk": 0.0, "confidence": 100.0}

    scores = model.decision_function(X)
    mean_score = float(np.mean(scores))

    # Exact Sigmoidal Confidence Mapping derived from baseline distribution
    confidence = 100.0 / (1.0 + np.exp(-k * (mean_score - s_mid)))

    confidence = float(max(1.0, min(99.0, confidence)))
    risk = float(100.0 - confidence)

    return {
        "risk": round(risk, 2),
        "confidence": round(confidence, 2)
    }
