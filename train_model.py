import os
import pandas as pd
import numpy as np
from extract_features import extract_raw
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import joblib

USER_DIR = "dataset/user_01"
MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "user_01.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

os.makedirs(USER_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# Generate or reload baseline data
baseline_path = os.path.join(USER_DIR, "baseline.csv")

print("Generating representative baseline training dataset for user_01...")
t = 1000
x, y = 300, 300
rows = []
np.random.seed(42)
for i in range(300):
    t += int(max(10, np.random.normal(30, 8)))
    x += int(np.random.normal(4, 12))
    y += int(np.random.normal(2, 8))
    rows.append([t, x, y])

df_base = pd.DataFrame(rows, columns=["t", "x", "y"])
df_base.to_csv(baseline_path, index=False, header=False)

# Extract raw features from baseline
raw_features = extract_raw(df_base)

# Fit StandardScaler on baseline dataset
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(raw_features)
X_train = pd.DataFrame(X_train_scaled, columns=raw_features.columns)

# Fit IsolationForest
model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)
model.fit(X_train)

# Save both model and scaler
joblib.dump(model, MODEL_PATH)
joblib.dump(scaler, SCALER_PATH)

print("✅ Model trained successfully and saved to:", MODEL_PATH)
print("✅ Scaler fitted and saved to:", SCALER_PATH)
