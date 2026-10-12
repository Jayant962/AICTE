# models/

`anomaly_model.joblib` is **not included**: training needs >= 100 real records with total, subtotal and tax,
and none were obtainable at build time. Training refuses to run on less (no synthetic padding):

    python scripts/train_model.py --records data/processed/records.csv --contamination 0.05

The artifact holds the fitted `StandardScaler + IsolationForest` pipeline, feature names, contamination,
training size and timestamp. Until it exists the app shows "Anomaly model not trained".
