import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_synthetic_transactions(num_samples: int = 3000, fraud_ratio: float = 0.08) -> pd.DataFrame:
    """
    Generates synthetic ATM transaction dataset with engineered features and ground-truth fraud labels.
    """
    np.random.seed(42)
    random.seed(42)

    data = []
    num_fraud = int(num_samples * fraud_ratio)
    num_normal = num_samples - num_fraud

    # 1. Normal Transactions
    for i in range(num_normal):
        # Normal daytime hours (6 AM to 11 PM)
        hour = int(np.random.choice(range(6, 24), p=[0.02, 0.04, 0.07, 0.08, 0.09, 0.10, 0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.04, 0.03, 0.01, 0.01, 0.00, 0.00]))
        # Typical cash amounts: $20, $40, $60, $100, $200
        amount = float(np.random.choice([20, 40, 60, 80, 100, 150, 200, 300], p=[0.25, 0.25, 0.15, 0.10, 0.12, 0.06, 0.05, 0.02]))
        current_balance = float(np.random.uniform(500, 8000))
        balance_ratio = amount / current_balance
        velocity_1h = int(np.random.choice([0, 1, 2], p=[0.85, 0.13, 0.02]))
        mean_past = float(np.random.uniform(50, 120))
        std_past = float(np.random.uniform(20, 50))
        zscore = (amount - mean_past) / std_past
        is_night = 1 if (0 <= hour <= 5) else 0
        is_near_limit = 1 if amount >= 750 else 0

        data.append({
            "amount": amount,
            "hour_of_day": hour,
            "balance_drain_ratio": round(balance_ratio, 4),
            "velocity_1h": velocity_1h,
            "amount_zscore": round(zscore, 3),
            "is_night": is_night,
            "is_near_limit": is_near_limit,
            "is_fraud": 0,
            "fraud_type": "none"
        })

    # 2. Fraudulent Transactions
    fraud_types = ["card_skimming_burst", "midnight_drain", "statistical_spike", "limit_drain"]
    for i in range(num_fraud):
        f_type = random.choice(fraud_types)
        
        if f_type == "midnight_drain":
            hour = random.choice([1, 2, 3, 4])
            amount = float(random.choice([500, 600, 700, 800]))
            current_balance = float(random.uniform(amount, amount * 1.25))
            balance_ratio = amount / current_balance
            velocity_1h = random.choice([1, 2])
            zscore = float(random.uniform(2.5, 4.5))
            is_night = 1
            is_near_limit = 1 if amount >= 750 else 0

        elif f_type == "card_skimming_burst":
            hour = random.randint(12, 23)
            amount = float(random.choice([400, 500, 600, 800]))
            current_balance = float(random.uniform(1000, 4000))
            balance_ratio = amount / current_balance
            velocity_1h = random.choice([3, 4, 5, 6])  # High burst
            zscore = float(random.uniform(3.0, 5.0))
            is_night = 0
            is_near_limit = 1 if amount >= 750 else 0

        elif f_type == "statistical_spike":
            hour = random.randint(8, 22)
            amount = float(random.choice([700, 800, 850]))
            current_balance = float(random.uniform(2000, 5000))
            balance_ratio = amount / current_balance
            velocity_1h = random.choice([1, 2])
            zscore = float(random.uniform(4.0, 7.0))  # Huge deviation
            is_night = 0
            is_near_limit = 1

        else: # limit_drain
            hour = random.choice([0, 1, 2, 23])
            amount = 800.0
            current_balance = float(random.uniform(850, 1100))
            balance_ratio = amount / current_balance
            velocity_1h = random.choice([2, 3])
            zscore = float(random.uniform(3.2, 5.5))
            is_night = 1 if (0 <= hour <= 5) else 0
            is_near_limit = 1

        data.append({
            "amount": amount,
            "hour_of_day": hour,
            "balance_drain_ratio": round(balance_ratio, 4),
            "velocity_1h": velocity_1h,
            "amount_zscore": round(zscore, 3),
            "is_night": is_night,
            "is_near_limit": is_near_limit,
            "is_fraud": 1,
            "fraud_type": f_type
        })

    df = pd.DataFrame(data)
    # Shuffle dataset
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    return df


if __name__ == "__main__":
    out_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_csv = os.path.join(out_dir, "synthetic_transactions.csv")
    df = generate_synthetic_transactions(3500, fraud_ratio=0.08)
    df.to_csv(out_csv, index=False)
    print(f"Generated {len(df)} synthetic transactions -> {out_csv}")
    print(f"Fraud distribution:\n{df['is_fraud'].value_counts(normalize=True)}")
