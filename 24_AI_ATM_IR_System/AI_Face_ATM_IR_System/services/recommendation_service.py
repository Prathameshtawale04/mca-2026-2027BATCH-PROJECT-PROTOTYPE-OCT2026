import numpy as np

def generate_savings_recommendations(user, account, transactions, savings_goals) -> dict:
    """
    Generates personalized savings planning, 50/30/20 budget analysis,
    and intelligent financial recommendations.
    """
    balance = account.balance if account else 1000.0

    # Categorize and analyze historical spending
    withdrawals = [tx for tx in transactions if tx.type == "withdraw"]
    deposits = [tx for tx in transactions if tx.type == "deposit"]

    total_withdrawn = sum(tx.amount for tx in withdrawals) if withdrawals else 0.0
    total_deposited = sum(tx.amount for tx in deposits) if deposits else balance

    # Monthly estimated income & outflow
    est_monthly_income = max(1500.0, total_deposited * 1.5 if total_deposited > 0 else 3000.0)
    
    # 50/30/20 standard budgeting targets
    needs_budget = round(est_monthly_income * 0.50, 2)       # 50% Essentials
    wants_budget = round(est_monthly_income * 0.30, 2)       # 30% Discretionary
    savings_budget = round(est_monthly_income * 0.20, 2)     # 20% Savings & Debt

    # Current savings goals analysis
    total_goal_target = sum(g.target_amount for g in savings_goals)
    total_saved = sum(g.current_amount for g in savings_goals)
    has_emergency_fund = any("emergency" in g.title.lower() or g.category.lower() == "emergency fund" for g in savings_goals)

    recommendations = []

    # Recommendation 1: Emergency Fund Buffer
    emergency_target = round(needs_budget * 3, 2)  # 3 months of essential expenses
    if not has_emergency_fund:
        recommendations.append({
            "id": "rec_emergency",
            "type": "create_goal",
            "priority": "HIGH",
            "title": "Establish a 3-Month Safety Cushion",
            "description": f"You currently do not have an active Emergency Fund. Based on your profile, target ${emergency_target:,.2f} to cover 3 months of essential buffer.",
            "suggested_target": emergency_target,
            "category": "Emergency Fund",
            "action_label": "Create Emergency Goal"
        })

    # Recommendation 2: Automated Round-Up / Micro-Savings
    recommendations.append({
        "id": "rec_roundup",
        "type": "feature",
        "priority": "MEDIUM",
        "title": "Automate 5% Round-Up on ATM Withdrawals",
        "description": "Enabling Mira Smart Round-Up deposits an extra $2 to $10 into your highest-priority savings goal each time you withdraw cash.",
        "action_label": "Enable Round-Up"
    })

    # Recommendation 3: High-Yield Savings Optimization
    if balance > 1500.0:
        annual_yield = round(balance * 0.0425, 2)
        recommendations.append({
            "id": "rec_hysa",
            "type": "product",
            "priority": "HIGH",
            "title": "Earn 4.25% APY with Mira High-Yield Vault",
            "description": f"Your current cash balance of ${balance:,.2f} could earn approximately ${annual_yield:,.2f} in interest per year if moved to a High-Yield vault.",
            "action_label": "Explore High-Yield"
        })

    # Recommendation 4: Discretionary Cash Discipline
    if total_withdrawn > wants_budget * 0.7:
        recommendations.append({
            "id": "rec_cash_limit",
            "type": "advice",
            "priority": "MEDIUM",
            "title": "Optimize Discretionary Cash Spending",
            "description": f"Your cash withdrawals (${total_withdrawn:,.2f}) are near 70% of your discretionary spending allowance. Mira suggests setting a $150 weekly ATM cash limit.",
            "action_label": "Set Weekly Limit"
        })

    return {
        "budget_breakdown": {
            "estimated_monthly_income": est_monthly_income,
            "needs_50_pct": needs_budget,
            "wants_30_pct": wants_budget,
            "savings_20_pct": savings_budget,
            "current_total_saved": round(total_saved, 2),
            "current_goals_target": round(total_goal_target, 2),
        },
        "spending_categories": [
            {"category": "Essentials & Bills", "amount": round(est_monthly_income * 0.45, 2), "percentage": 45},
            {"category": "Dining & Entertainment", "amount": round(est_monthly_income * 0.22, 2), "percentage": 22},
            {"category": "ATM Cash Withdrawals", "amount": round(total_withdrawn if total_withdrawn > 0 else 240.0, 2), "percentage": 15},
            {"category": "Transfers & Misc", "amount": round(est_monthly_income * 0.08, 2), "percentage": 8},
            {"category": "Investments & Goals", "amount": round(est_monthly_income * 0.10, 2), "percentage": 10},
        ],
        "recommendations": recommendations
    }
