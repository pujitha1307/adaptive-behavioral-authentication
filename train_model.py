import os
import pandas as pd
from extract_features import extract
from sklearn.ensemble import IsolationForest
import joblib

USER_DIR = "dataset/user_01"
MODEL_PATH = "model/user_01.pkl"

all_features = []

for file in os.listdir(USER_DIR):
    if file.endswith(".csv"):
        path = os.path.join(USER_DIR, file)
        all_features.append(extract(path))

X_train = pd.concat(all_features)

model = IsolationForest(
    n_estimators=150,
    contamination=0.1,
    random_state=42
)

model.fit(X_train)

joblib.dump(model, MODEL_PATH)

print("Model trained and saved to", MODEL_PATH)
