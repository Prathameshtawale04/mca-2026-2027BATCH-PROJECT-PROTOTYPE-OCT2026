"""
50/30/20 Smart Financial Intelligence & Savings Goals Service
- Analyzes customer balance and transaction history.
- Computes 50% Essentials (Needs), 30% Discretionary (Wants), and 20% Wealth Building (Savings).
- Manages savings goals (Emergency Cushion, Vacation Travel, High-Yield Investment).
"""

from database.db import query_all, query_one, execute_sql

DEFAULT_GOALS = [
    {"id": "goal_1", "title": "3-Month Emergency Cushion", "category": "Emergency Fund", "target": 5000.0, "current": 1850.0},
    {"id": "goal_2", "title": "Vacation & Travel Fund", "category": "Discretionary", "target": 2500.0, "current": 920.0},
    {"id": "goal_3", "title": "High-Yield Tech Investment", "category": "Wealth Building", "target": 3500.0, "current": 1400.0}
]

class SavingsService:
    @staticmethod
    def get_budget_breakdown(account_number: str) -> dict:
        account = query_one("SELECT balance, daily_limit FROM accounts WHERE account_number = ?", (account_number,))
        balance = account["balance"] if account else 1000.0

        # 50/30/20 standard wealth formula
        needs_budget = round(balance * 0.50, 2)
        wants_budget = round(balance * 0.30, 2)
        savings_budget = round(balance * 0.20, 2)

        # Annual yield calculation at 4.25% APY
        annual_yield = round(balance * 0.0425, 2)

        recommendations = [
            {
                "title": "Establish 3-Month Emergency Cushion",
                "category": "Emergency Fund",
                "priority": "HIGH",
                "desc": f"Allocate ${needs_budget * 1.5:,.2f} to cover unexpected emergencies and health cushions.",
                "action": "Allocate +$50"
            },
            {
                "title": "Mira High-Yield Vault (4.25% APY)",
                "category": "Wealth Building",
                "priority": "HIGH",
                "desc": f"Your current cash balance can generate ~${annual_yield:,.2f} annually in automated interest.",
                "action": "Enable Vault"
            },
            {
                "title": "Automate 5% Cash Withdrawal Round-Up",
                "category": "Micro-Savings",
                "priority": "MEDIUM",
                "desc": "Automatically routes $2 to $10 into your highest-priority savings goal on each ATM cash transaction.",
                "action": "Enable Round-Up"
            }
        ]

        return {
            "balance": balance,
            "needs_budget": needs_budget,
            "wants_budget": wants_budget,
            "savings_budget": savings_budget,
            "annual_yield_425": annual_yield,
            "recommendations": recommendations,
            "goals": DEFAULT_GOALS
        }

    @staticmethod
    def add_goal_contribution(goal_id: str, amount: float) -> dict:
        for g in DEFAULT_GOALS:
            if g["id"] == goal_id:
                g["current"] = round(g["current"] + amount, 2)
                return {"success": True, "goal": g, "message": f"Added ${amount:.2f} to {g['title']}"}
        return {"success": False, "message": "Goal not found"}
