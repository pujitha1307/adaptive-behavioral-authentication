import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def extract(file_path):
    df = pd.read_csv(file_path, names=["t", "x", "y"])

    df["dx"] = df["x"].diff()
    df["dy"] = df["y"].diff()
    df["dt"] = df["t"].diff() / 1000  # ms → seconds

    df["speed"] = np.sqrt(df["dx"]**2 + df["dy"]**2) / df["dt"]
    df["acc"] = df["speed"].diff() / df["dt"]

    df = df.replace([np.inf, -np.inf], 0).fillna(0)

    # 🔥 SCALE FEATURES (CRITICAL)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[["speed", "acc"]])

    return pd.DataFrame(scaled, columns=["speed", "acc"])
