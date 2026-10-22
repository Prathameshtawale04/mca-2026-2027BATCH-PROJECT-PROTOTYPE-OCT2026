import os
import joblib
import numpy as np
from datetime import datetime, timedelta

MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "ml_pipeline", "saved_models")
os.makedirs(MODEL_DIR, exist_ok=True)
RF_MODEL_PATH = os.path.join(MODEL_DIR, "fraud_rf_model.pkl")
IFOREST_MODEL_PATH = os.path.join(MODEL_DIR, "fraud_iforest_model.pkl")

# Global model cache
_rf_model = None
_iforest_model = None


def load_models():
    """Loads saved ML models from disk if present."""
    global _rf_model, _iforest_model
    try:
        if os.path.exists(RF_MODEL_PATH):
            _rf_model = joblib.load(RF_MODEL_PATH)
        if os.path.exists(IFOREST_MODEL_PATH):
            _iforest_model = joblib.load(IFOREST_MODEL_PATH)
    except Exception as e:
        print(f"Notice: Models will use rule-based ensemble until trained: {e}")


def extract_transaction_features(
    amount: float,
    current_balance: float,
    recent_transactions: list,
    timestamp: datetime = None
) -> np.ndarray:
    """
    Extracts 7 numerical features for the fraud ML models:
    [amount, hour_of_day, amount_to_balance_ratio, velocity_1h, amount_zscore, is_night, is_near_limit]
    """
    if timestamp is None:
        timestamp = datetime.utcnow()

    hour = timestamp.hour
    is_night = 1.0 if (0 <= hour <= 5) else 0.0
    balance_ratio = float(amount) / max(1.0, current_balance)
    is_near_limit = 1.0 if amount >= 750.0 else 0.0

    # Calculate recent 1-hour transaction velocity
    one_hour_ago = timestamp - timedelta(hours=1)
    recent_1h = [tx for tx in recent_transactions if hasattr(tx, 'timestamp') and tx.timestamp >= one_hour_ago]
    velocity_1h = float(len(recent_1h))

    # Calculate customer amount historical z-score
    past_amounts = [tx.amount for tx in recent_transactions if hasattr(tx, 'amount')]
    if len(past_amounts) >= 3:
        mean_amt = np.mean(past_amounts)
        std_amt = np.std(past_amounts) + 1e-4
        zscore = float((amount - mean_amt) / std_amt)
    else:
        # Default baseline if limited history: baseline mean $100, std $60
        zscore = float((amount - 100.0) / 60.0)

    features = np.array([
        amount,
        float(hour),
        balance_ratio,
        velocity_1h,
        zscore,
        is_night,
        is_near_limit
    ], dtype=np.float32)

    return features


def assess_transaction_risk(
    amount: float,
    current_balance: float,
    recent_transactions: list,
    tx_type: str = "withdraw",
    timestamp: datetime = None
) -> dict:
    """
    Evaluates real-time fraud probability combining ML inference (Random Forest + Isolation Forest)
    and banking compliance rules.
    """
    features = extract_transaction_features(amount, current_balance, recent_transactions, timestamp)
    reasons = []
    
    # 1. Rule-based safety evaluations
    if features[2] > 0.90 and amount > 300:
        reasons.append("Attempted withdrawal drains over 90% of entire account balance")
    if features[3] >= 3:
        reasons.append(f"High velocity surge: {int(features[3])} transactions within 60 minutes")
    if features[5] == 1.0 and amount > 400:
        reasons.append("Unusual high-value transaction during off-hours (midnight to 5 AM)")
    if features[4] > 3.0:
        reasons.append(f"Amount is statistical anomaly ({features[4]:.1f} std deviations above customer average)")
    if amount > 800.0 and tx_type == "withdraw":
        reasons.append("Amount exceeds standard single-transaction ATM safety threshold ($800)")

    # 2. Machine Learning Inference
    load_models()
    ml_score = 0.0

    if _rf_model is not None and _iforest_model is not None:
        try:
            feats_2d = features.reshape(1, -1)
            # Supervised RF fraud probability
            rf_prob = float(_rf_model.predict_proba(feats_2d)[0][1])
            # Unsupervised Isolation Forest anomaly score (-0.5 to 0.5 typical, normalize to 0..1)
            iforest_raw = float(_iforest_model.decision_function(feats_2d)[0])
            iforest_score = max(0.0, min(1.0, 0.5 - (iforest_raw * 1.5)))
            
            # Blend: 60% RF supervised, 40% Isolation Forest anomaly
            ml_score = round(0.6 * rf_prob + 0.4 * iforest_score, 3)
        except Exception as e:
            print(f"ML inference error: {e}")
            ml_score = 0.15
    else:
        # Heuristic scoring fallback based on engineered features
        heuristic = 0.05
        if features[5] == 1.0: heuristic += 0.20
        if features[2] > 0.8: heuristic += 0.25
        if features[3] >= 3: heuristic += 0.35
        if features[4] > 2.5: heuristic += 0.25
        ml_score = min(0.95, round(heuristic, 3))

    # Determine risk category & action
    if ml_score >= 0.70 or len(reasons) >= 2:
        tier = "CRITICAL" if ml_score >= 0.85 else "HIGH"
        is_flagged = True
        status = "flagged"
    elif ml_score >= 0.40 or len(reasons) == 1:
        tier = "MEDIUM"
        is_flagged = False
        status = "completed"
    else:
        tier = "LOW"
        is_flagged = False
        status = "completed"

    return {
        "fraud_score": ml_score,
        "risk_tier": tier,
        "is_flagged": is_flagged,
        "status": status,
        "flag_reasons": reasons if reasons else ["Normal transaction patterns within behavioral baseline"],
        "features": {
            "amount": float(features[0]),
            "hour": int(features[1]),
            "balance_drain_ratio": round(float(features[2]), 3),
            "recent_velocity": int(features[3]),
            "amount_zscore": round(float(features[4]), 2),
            "is_night": bool(features[5]),
        }
    }
