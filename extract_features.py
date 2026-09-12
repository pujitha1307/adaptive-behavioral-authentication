import os
import logging
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib

logger = logging.getLogger(__name__)
SCALER_PATH = "model/scaler.pkl"

def extract_raw(df):
    df = df.copy()
    df["dx"] = df["x"].diff()
    df["dy"] = df["y"].diff()
    df["dt"] = df["t"].diff() / 1000.0  # ms -> seconds

    # Prevent division by zero
    df["dt"] = df["dt"].replace(0, 0.001)

    df["speed"] = np.sqrt(df["dx"]**2 + df["dy"]**2) / df["dt"]
    df["acc"] = df["speed"].diff() / df["dt"]
    df["jerk"] = df["acc"].diff() / df["dt"]

    features = df[["speed", "acc", "jerk"]].replace([np.inf, -np.inf], 0).fillna(0)
    return features

def extract(file_path, scaler=None, fit=False):
    if isinstance(file_path, str):
        if not os.path.exists(file_path):
            return pd.DataFrame()
        df = pd.read_csv(file_path, names=["t", "x", "y"])
    elif isinstance(file_path, pd.DataFrame):
        df = file_path
    else:
        return pd.DataFrame()

    if len(df) < 3:
        return pd.DataFrame()

    features = extract_raw(df)

    if scaler is not None:
        scaled = scaler.transform(features)
        return pd.DataFrame(scaled, columns=features.columns)

    if fit:
        new_scaler = StandardScaler()
        scaled = new_scaler.fit_transform(features)
        return pd.DataFrame(scaled, columns=features.columns), new_scaler

    if os.path.exists(SCALER_PATH):
        try:
            loaded_scaler = joblib.load(SCALER_PATH)
            scaled = loaded_scaler.transform(features)
            return pd.DataFrame(scaled, columns=features.columns)
        except Exception as e:
            logger.warning("Could not load pre-fitted scaler from %s: %s", SCALER_PATH, e)

    # Fallback if no pre-fitted scaler is present
    fallback_scaler = StandardScaler()
    scaled = fallback_scaler.fit_transform(features)
    return pd.DataFrame(scaled, columns=features.columns)
