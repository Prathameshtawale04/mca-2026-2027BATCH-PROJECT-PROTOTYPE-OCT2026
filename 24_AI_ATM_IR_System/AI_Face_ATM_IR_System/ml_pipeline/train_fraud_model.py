import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
try:
    from ml_pipeline.synthetic_data_generator import generate_synthetic_transactions
except ImportError:
    from synthetic_data_generator import generate_synthetic_transactions

FEATURE_COLS = [
    "amount",
    "hour_of_day",
    "balance_drain_ratio",
    "velocity_1h",
    "amount_zscore",
    "is_night",
    "is_near_limit"
]

def train_and_save_models():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    models_dir = os.path.join(base_dir, "saved_models")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    csv_path = os.path.join(data_dir, "synthetic_transactions.csv")
    if not os.path.exists(csv_path):
        print("Generating new synthetic dataset...")
        df = generate_synthetic_transactions(3500, fraud_ratio=0.08)
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)

    X = df[FEATURE_COLS].values
    y = df["is_fraud"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    print(f"Training set: {X_train.shape[0]} samples, Test set: {X_test.shape[0]} samples")

    # 1. Supervised Random Forest
    rf = RandomForestClassifier(
        n_estimators=120,
        max_depth=8,
        min_samples_split=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)

    y_pred_rf = rf.predict(X_test)
    y_prob_rf = rf.predict_proba(X_test)[:, 1]
    rf_auc = roc_auc_score(y_test, y_prob_rf)
    rf_f1 = f1_score(y_test, y_pred_rf)
    rf_prec = precision_score(y_test, y_pred_rf)
    rf_rec = recall_score(y_test, y_pred_rf)

    print("--- Random Forest Metrics ---")
    print(f"ROC-AUC: {rf_auc:.4f}")
    print(f"Precision: {rf_prec:.4f}")
    print(f"Recall: {rf_rec:.4f}")
    print(f"F1-Score: {rf_f1:.4f}")

    # 2. Unsupervised Isolation Forest (trained on normal samples + slight contamination)
    iforest = IsolationForest(
        n_estimators=120,
        contamination=0.08,
        random_state=42,
        n_jobs=-1
    )
    iforest.fit(X_train)

    # Save models
    rf_path = os.path.join(models_dir, "fraud_rf_model.pkl")
    iforest_path = os.path.join(models_dir, "fraud_iforest_model.pkl")
    joblib.dump(rf, rf_path)
    joblib.dump(iforest, iforest_path)
    print(f"Saved models to:\n  {rf_path}\n  {iforest_path}")

    return {
        "status": "success",
        "samples_trained": int(X_train.shape[0]),
        "samples_tested": int(X_test.shape[0]),
        "metrics": {
            "roc_auc": round(float(rf_auc), 4),
            "precision": round(float(rf_prec), 4),
            "recall": round(float(rf_rec), 4),
            "f1_score": round(float(rf_f1), 4)
        }
    }

if __name__ == "__main__":
    train_and_save_models()
