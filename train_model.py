import os
import json
import logging
import pandas as pd
import numpy as np
from extract_features import extract_raw
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

USER_DIR = "dataset/user_01"
MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "user_01.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
THRESHOLDS_PATH = os.path.join(MODEL_DIR, "thresholds.json")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")

os.makedirs(USER_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# Generate baseline mouse movement telemetry dataset
baseline_path = os.path.join(USER_DIR, "baseline.csv")

logger.info("Generating representative baseline training dataset for user_01...")
t = 1000
x, y = 300, 300
rows = []
np.random.seed(42)
for i in range(400):
    t += int(max(10, np.random.normal(30, 8)))
    x += int(np.random.normal(4, 12))
    y += int(np.random.normal(2, 8))
    rows.append([t, x, y])

df_base = pd.DataFrame(rows, columns=["t", "x", "y"])
df_base.to_csv(baseline_path, index=False, header=False)

# Hold out 20% of baseline data for validation
split_idx = int(len(df_base) * 0.8)
df_train = df_base.iloc[:split_idx].copy()
df_val = df_base.iloc[split_idx:].copy()

raw_train_features = extract_raw(df_train)
raw_val_features = extract_raw(df_val)

# Fit StandardScaler on 80% training features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(raw_train_features)
X_train = pd.DataFrame(X_train_scaled, columns=raw_train_features.columns)

X_val_scaled = scaler.transform(raw_val_features)
X_val = pd.DataFrame(X_val_scaled, columns=raw_val_features.columns)

# Fit IsolationForest model
model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)
model.fit(X_train)

# 1. Fit s_mid to the mean of the training decision scores
train_scores = model.decision_function(X_train)
s_mean = float(np.mean(train_scores))
s_p15 = float(np.percentile(train_scores, 15))
s_p02 = float(np.percentile(train_scores, 2))

k = 22.0
s_mid = s_mean  # Midpoint fit from user's normal baseline mean

# Helper sigmoid function
def sigmoid_confidence(score, steepness=k, midpoint=s_mid):
    return 100.0 / (1.0 + np.exp(-steepness * (score - midpoint)))

# 2. Compute medium_risk_threshold and high_risk_threshold directly from s_p15 and s_p02
medium_risk_threshold = round(float(100.0 - sigmoid_confidence(s_p15)), 2)
high_risk_threshold = round(float(100.0 - sigmoid_confidence(s_p02)), 2)

thresholds_data = {
    "medium_risk_threshold": medium_risk_threshold,
    "high_risk_threshold": high_risk_threshold,
    "s_mid": round(s_mid, 4),
    "k": k,
    "baseline_score_mean": round(s_mean, 4),
    "baseline_score_p15": round(s_p15, 4),
    "baseline_score_p02": round(s_p02, 4)
}

with open(THRESHOLDS_PATH, "w") as f:
    json.dump(thresholds_data, f, indent=2)

# Evaluate FPR on 20% validation set using the derived medium_risk_threshold
val_scores = model.decision_function(X_val)
val_confidences = [sigmoid_confidence(s) for s in val_scores]
val_risks = [100.0 - c for c in val_confidences]

fp_count = sum(1 for r in val_risks if r >= medium_risk_threshold)
false_positive_rate = float(fp_count / len(val_risks)) if len(val_risks) > 0 else 0.0

metrics_data = {
    "train_sample_count": len(X_train),
    "val_sample_count": len(X_val),
    "false_positive_rate": round(false_positive_rate, 4),
    "medium_risk_threshold": medium_risk_threshold,
    "high_risk_threshold": high_risk_threshold
}

with open(METRICS_PATH, "w") as f:
    json.dump(metrics_data, f, indent=2)

# Save trained artifacts
joblib.dump(model, MODEL_PATH)
joblib.dump(scaler, SCALER_PATH)

logger.info("✅ Model trained successfully and saved to: %s", MODEL_PATH)
logger.info("✅ Scaler fitted and saved to: %s", SCALER_PATH)
logger.info("✅ Data-derived thresholds saved to: %s (Medium: %s%%, High: %s%%)",
            THRESHOLDS_PATH, medium_risk_threshold, high_risk_threshold)
logger.info("📊 Validation Metrics: Train Samples=%d, Val Samples=%d, Validation FPR=%.2f%%",
            len(X_train), len(X_val), false_positive_rate * 100)
