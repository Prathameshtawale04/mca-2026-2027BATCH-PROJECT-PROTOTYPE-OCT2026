import os
import json
from flask import Blueprint, request, jsonify
from ml_pipeline.train_fraud_model import train_and_save_models
from ml_pipeline.evaluate_models import generate_evaluation_report
from services.fraud_service import assess_transaction_risk

ml_bp = Blueprint("ml", __name__, url_prefix="/api/ml")

@ml_bp.route("/metrics", methods=["GET"])
def get_metrics():
    metrics_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "data", "evaluation_metrics.json")
    if not os.path.exists(metrics_path):
        # Generate on the fly
        report = generate_evaluation_report()
    else:
        with open(metrics_path, "r") as f:
            report = json.load(f)

    return jsonify(report)


@ml_bp.route("/retrain", methods=["POST"])
def retrain_model():
    try:
        train_res = train_and_save_models()
        eval_res = generate_evaluation_report()
        return jsonify({
            "message": "Models successfully retrained and evaluated on fresh synthetic datasets",
            "training_summary": train_res,
            "metrics": eval_res
        })
    except Exception as e:
        return jsonify({"error": f"Retraining failed: {str(e)}"}), 500


@ml_bp.route("/test-fraud", methods=["POST"])
def test_fraud_playground():
    data = request.get_json() or {}
    amount = float(data.get("amount", 250))
    balance = float(data.get("balance", 1200))
    velocity = int(data.get("velocity", 1))
    hour = int(data.get("hour", 14))

    # Mock historical txs to simulate velocity
    class MockTx:
        def __init__(self, amt, ts):
            self.amount = amt
            self.timestamp = ts

    from datetime import datetime, timedelta
    mock_now = datetime.utcnow().replace(hour=hour)
    mock_history = [MockTx(amount, mock_now - timedelta(minutes=10 * i)) for i in range(velocity)]

    assessment = assess_transaction_risk(
        amount=amount,
        current_balance=balance,
        recent_transactions=mock_history,
        tx_type="withdraw",
        timestamp=mock_now
    )

    return jsonify({
        "input": {
            "amount": amount,
            "balance": balance,
            "velocity": velocity,
            "hour": hour
        },
        "assessment": assessment
    })
