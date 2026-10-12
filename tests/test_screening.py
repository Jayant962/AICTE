import os

import pytest

from src import database
from src.anomaly_detection import InsufficientDataError, load_model, predict_record, train_anomaly_model
from src.feature_engineering import build_feature_frame, record_features
from src.screening import screen


def test_categories():
    assert screen(1.0, [], [], {"flag": False})["category"] == "Low concern"
    assert screen(0.5, [], [], {})["category"] == "Needs review"
    fail = [{"status": "FAIL", "rule": "x", "explanation": "e"}]
    assert screen(1.0, fail, [], {})["category"] == "High concern"
    review = [{"status": "REVIEW", "rule": "x", "explanation": "e"}]
    assert screen(1.0, review, [], {})["category"] == "Needs review"
    assert screen(1.0, [], [], {"flag": True, "score": -0.1})["category"] == "Needs review"
    near = [{"match_type": "near", "reasons": ["r"], "other": {"id": 1}}]
    exact = [{"match_type": "exact", "reasons": ["r"], "other": {"id": 1}}]
    assert screen(1.0, [], near, {})["category"] == "Needs review"
    assert screen(1.0, [], exact, {})["category"] == "High concern"


def test_disclaimer_present():
    assert "human" in screen(1.0, [], [], {})["disclaimer"]


def test_features_reject_invalid():
    assert record_features({"total": 10, "subtotal": 0, "tax": 1}) is None
    assert record_features({"total": -5, "subtotal": 5, "tax": 1}) is None
    assert record_features({"total": float("inf"), "subtotal": 5, "tax": 1}) is None
    assert record_features({"total": 10, "subtotal": 8, "tax": None}) is None
    assert record_features({"total": 10, "subtotal": 8, "tax": 2}) is not None
    assert build_feature_frame([]).empty


def test_model_missing_gives_fallback(tmp_path):
    out = predict_record({"total": 10, "subtotal": 8, "tax": 2}, path=str(tmp_path / "none.joblib"))
    assert out["available"] is False and "not trained" in out["message"]


def test_refuses_to_train_on_too_little_data(tmp_path):
    with pytest.raises(InsufficientDataError):
        train_anomaly_model([{"total": 10, "subtotal": 8, "tax": 2}] * 5, path=str(tmp_path / "m.joblib"))
    assert not os.path.exists(tmp_path / "m.joblib")


def test_train_save_load_predict_roundtrip(tmp_path):
    """Mechanics test on randomly generated numbers (NOT real invoices, no performance claim)."""
    import numpy as np
    rng = np.random.default_rng(0)
    recs = []
    for _ in range(150):
        sub = float(rng.uniform(50, 500)); tax = sub * float(rng.choice([0.0, 0.05, 0.12, 0.18]))
        recs.append({"subtotal": sub, "tax": tax, "total": sub + tax})
    path = str(tmp_path / "m.joblib")
    art = train_anomaly_model(recs, contamination=0.05, path=path)
    assert art["n_train"] == 150 and load_model(path) is not None
    normal = predict_record({"subtotal": 200.0, "tax": 36.0, "total": 236.0}, path=path)
    odd = predict_record({"subtotal": 1e7, "tax": 9e6, "total": 1.9e7}, path=path)
    # Mechanics + ordering only: the unusual record must score as MORE anomalous (lower) than the typical one.
    # (Whether it crosses the contamination threshold depends on the data; no detection claim is made.)
    assert normal["scorable"] and odd["scorable"] and isinstance(odd["flag"], bool)
    assert odd["score"] < normal["score"]
    assert predict_record({"total": 5}, path=path)["scorable"] is False


def test_invalid_contamination(tmp_path):
    with pytest.raises(ValueError):
        train_anomaly_model([], contamination=0.9, path=str(tmp_path / "m.joblib"))


def test_sqlite_persistence_and_no_overwrite():
    conn = database.connect(":memory:")
    rec = {"file_hash": "abc", "vendor": "V", "invoice_number": "N1", "total": 10.0}
    assert database.insert_record(conn, rec) == 1
    assert database.insert_record(conn, {**rec, "total": 99.0}) is None  # same file: not overwritten
    assert database.fetch_all(conn)[0]["total"] == 10.0
    with pytest.raises(ValueError):
        database.insert_record(conn, {"file_hash": "x", "total": "ten"})
    with pytest.raises(ValueError):
        database.insert_record(conn, {"vendor": "no hash"})
    database.reset_db(conn)
    assert database.count(conn) == 0
