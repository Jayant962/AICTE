"""Isolation Forest anomaly detector (unsupervised).

Anomaly score != fraud probability. The model only says a record's (log_total, tax_ratio)
is unusual relative to the training population. contamination is the *assumed* share of
outliers in the training data; it sets the decision threshold, not a measured fraud rate.
"""
import os
from datetime import datetime, timezone

import joblib
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .feature_engineering import FEATURE_NAMES, build_feature_frame, record_features

MIN_TRAIN_RECORDS = 100
DEFAULT_MODEL_PATH = os.path.join("models", "anomaly_model.joblib")


class InsufficientDataError(ValueError):
    pass


def train_anomaly_model(records, contamination=0.05, path=DEFAULT_MODEL_PATH,
                        min_records=MIN_TRAIN_RECORDS, random_state=42):
    """Fit scaler + IsolationForest on scorable records and save with joblib."""
    if not 0 < contamination <= 0.5:
        raise ValueError("contamination must be in (0, 0.5].")
    X = build_feature_frame(records)
    if len(X) < min_records:
        raise InsufficientDataError(
            f"Only {len(X)} scorable records (need >= {min_records}). Not training a model on so little data.")
    pipe = Pipeline([("scale", StandardScaler()),
                     ("forest", IsolationForest(n_estimators=200, contamination=contamination,
                                                random_state=random_state))])
    pipe.fit(X)
    artifact = {"pipeline": pipe, "features": FEATURE_NAMES, "contamination": contamination,
                "n_train": int(len(X)), "trained_at": datetime.now(timezone.utc).isoformat(),
                "sklearn_version": __import__("sklearn").__version__}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    joblib.dump(artifact, path)
    return artifact


def load_model(path=DEFAULT_MODEL_PATH):
    """Return the artifact dict or None if missing/unreadable."""
    if not os.path.exists(path):
        return None
    try:
        art = joblib.load(path)
        return art if "pipeline" in art else None
    except Exception:
        return None


def predict_record(record: dict, artifact=None, path=DEFAULT_MODEL_PATH) -> dict:
    """Always returns a dict with keys available, scorable, flag, score, message."""
    artifact = artifact or load_model(path)
    if artifact is None:
        return {"available": False, "scorable": False, "flag": None, "score": None,
                "message": "Anomaly model not trained. Run scripts/train_model.py once >= "
                           f"{MIN_TRAIN_RECORDS} real invoice records are available."}
    feats = record_features(record)
    if feats is None:
        return {"available": True, "scorable": False, "flag": None, "score": None,
                "message": "Record lacks valid total/subtotal/tax, so it cannot be scored."}
    import pandas as pd
    X = pd.DataFrame([feats], columns=artifact["features"])
    pipe = artifact["pipeline"]
    score = float(pipe.decision_function(X)[0])  # negative = more anomalous
    flag = bool(pipe.predict(X)[0] == -1)
    return {"available": True, "scorable": True, "flag": flag, "score": round(score, 4),
            "message": ("Unusual relative to the training data (not proof of fraud)." if flag
                        else "Within the range seen in the training data.")}
