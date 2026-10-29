import os
from functools import lru_cache
import joblib
import pandas as pd

MODEL_PATH = os.getenv("MODEL_PATH", "artifacts/heart_model.joblib")

@lru_cache(maxsize=1)
def load_heart_model():
    if not os.path.exists(MODEL_PATH):
        return None
    return joblib.load(MODEL_PATH)

def predict_heart_risk(payload):
    model = load_heart_model()
    if model is None:
        raise FileNotFoundError("Model artifact missing")

    expected = getattr(model, "feature_names_in_", None)
    if expected is None:
        raise ValueError("Model artifact does not expose expected feature names")
    missing = [str(c) for c in expected if c not in payload]
    extra = [str(c) for c in payload if c not in expected]
    if missing:
        raise ValueError(f"Missing required feature(s): {', '.join(missing)}")
    if extra:
        raise ValueError(f"Unexpected feature(s): {', '.join(extra)}")

    row = pd.DataFrame([{c: payload[c] for c in expected}])
    prediction = int(model.predict(row)[0])
    score = None
    if hasattr(model, "predict_proba"):
        score = float(model.predict_proba(row)[0][1])
    return {
        "model": "uci-heart-disease-educational-baseline",
        "model_output_class": prediction,
        "estimated_positive_class_score": score,
        "interpretation": "Model output only; not an individual clinical probability or diagnosis."
    }
