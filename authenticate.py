import numpy as np
import joblib
from extract_features import extract

MODEL_PATH = "model/user_01.pkl"

def compute_risk(csv_file):
    model = joblib.load(MODEL_PATH)
    X = extract(csv_file)

    if len(X) == 0:
        return 0.0

    scores = model.decision_function(X)
    mean_score = np.mean(scores)

    risk = 100 - ((mean_score + 0.5) * 100)
    return round(risk, 2)
