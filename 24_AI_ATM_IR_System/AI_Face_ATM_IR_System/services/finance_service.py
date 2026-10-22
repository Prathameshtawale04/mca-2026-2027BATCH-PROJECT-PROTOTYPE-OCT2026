"""Personal Finance Service: 50/30/20 Budgeting, Savings Goals, and Rule-Based Guidance."""

from datetime import datetime
from database.db import query_db, execute_db
from services.auth_service import log_audit_event

NEEDS_CATEGORIES = {"Housing", "Groceries", "Utilities", "Healthcare", "Transport", "Insurance"}
WANTS_CATEGORIES = {"Dining Out", "Entertainment", "Shopping", "Subscriptions", "Travel", "Hobbies"}
SAVINGS_CATEGORIES = {"Emergency Fund", "Investments", "Savings Vault", "Retirement"}

def add_finance_entry(user_id: int, entry_type: str, category: str, amount: float, entry_date: str = None, description: str = "") -> tuple[bool, str, dict]:
    """Record an income or expense entry with validation."""
    if entry_type not in ("INCOME", "EXPENSE"):
        return False, "Invalid entry type. Must be 'INCOME' or 'EXPENSE'.", {}
    if amount <= 0:
        return False, "Amount must be strictly positive.", {}

    if not entry_date:
        entry_date = datetime.now().strftime("%Y-%m-%d")

    res = execute_db(
        """INSERT INTO finance_entries (user_id, entry_type, category, amount, entry_date, description)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, entry_type, category.strip(), amount, entry_date, description.strip())
    )
    entry_id = res["lastrowid"]
    log_audit_event(user_id, None, "FINANCE_ENTRY", f"Added {entry_type} of ${amount:.2f} ({category})", None, "INFO")

    entry = query_db("SELECT * FROM finance_entries WHERE id = ?", (entry_id,), one=True)
    return True, f"Successfully recorded {entry_type.lower()} entry.", dict(entry)

def calculate_50_30_20_summary(user_id: int, month_year: str = None) -> dict:
    """
    Compute 50/30/20 allocation:
    - 50% Needs: Housing, Groceries, Utilities, Healthcare, Transport
    - 30% Wants: Dining, Entertainment, Shopping, Travel
    - 20% Wealth: Savings vaults, Investments, Emergency Reserve
    Generates educational rule-based financial guidance.
    """
    if not month_year:
        month_year = datetime.now().strftime("%Y-%m")

    # Fetch total income for the month
    inc_res = query_db(
        """SELECT COALESCE(SUM(amount), 0.0) as total_inc
           FROM finance_entries
           WHERE user_id = ? AND entry_type = 'INCOME' AND strftime('%Y-%m', entry_date) = ?""",
        (user_id, month_year),
        one=True
    )
    total_income = inc_res["total_inc"] if inc_res else 0.0

    # Fetch all expenses for the month
    expenses = query_db(
        """SELECT category, SUM(amount) as cat_total
           FROM finance_entries
           WHERE user_id = ? AND entry_type = 'EXPENSE' AND strftime('%Y-%m', entry_date) = ?
           GROUP BY category""",
        (user_id, month_year)
    )

    actual_needs = 0.0
    actual_wants = 0.0
    actual_savings = 0.0
    cat_breakdown = {}

    for row in expenses:
        cat = row["category"]
        amt = row["cat_total"]
        cat_breakdown[cat] = amt

        if cat in NEEDS_CATEGORIES:
            actual_needs += amt
        elif cat in WANTS_CATEGORIES:
            actual_wants += amt
        else:
            actual_savings += amt

    total_expenses = actual_needs + actual_wants + actual_savings
    net_savings = total_income - total_expenses

    # Theoretical 50/30/20 Targets based on Total Income
    target_needs = total_income * 0.50
    target_wants = total_income * 0.30
    target_savings = total_income * 0.20

    # Rule-based educational guidance
    guidance_tips = []
    if total_income > 0:
        needs_pct = (actual_needs / total_income) * 100
        wants_pct = (actual_wants / total_income) * 100
        savings_pct = (net_savings / total_income) * 100

        if needs_pct > 50:
            guidance_tips.append(
                f"Needs spending is currently at {needs_pct:.1f}% of income (target: 50%). Consider reviewing fixed utility and subscription costs."
            )
        else:
            guidance_tips.append(
                f"Excellent: Essential needs are contained at {needs_pct:.1f}% (within the 50% limit)."
            )

        if wants_pct > 30:
            guidance_tips.append(
                f"Lifestyle wants account for {wants_pct:.1f}% (target: 30%). Trimming dining out or shopping by ${(actual_wants - target_wants):.2f} would restore 50/30/20 balance."
            )
        else:
            guidance_tips.append(
                f"Discretionary spending is well-managed at {wants_pct:.1f}% of income."
            )

        if savings_pct >= 20:
            guidance_tips.append(
                f"Outstanding wealth accumulation: You are saving {savings_pct:.1f}% of monthly income (exceeding 20% benchmark)."
            )
        else:
            guidance_tips.append(
                f"Current net savings rate is {savings_pct:.1f}% (target: 20%). Allocating ${(target_savings - net_savings):.2f} to a high-yield vault is recommended."
            )
    else:
        guidance_tips.append("Log your monthly salary or income entries to generate personalized 50/30/20 guidance.")

    return {
        "month_year": month_year,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_savings": net_savings,
        "targets": {
            "needs": target_needs,
            "wants": target_wants,
            "savings": target_savings
        },
        "actuals": {
            "needs": actual_needs,
            "wants": actual_wants,
            "savings": actual_savings
        },
        "category_breakdown": cat_breakdown,
        "guidance_tips": guidance_tips,
        "disclaimer": "Educational financial simulation only. Not formal financial or investment advice."
    }

def create_savings_goal(user_id: int, goal_name: str, target_amount: float, target_date: str = None) -> tuple[bool, str, dict]:
    """Create a new savings goal vault."""
    if target_amount <= 0:
        return False, "Target amount must be greater than zero.", {}
    if not goal_name.strip():
        return False, "Goal name cannot be empty.", {}

    res = execute_db(
        """INSERT INTO savings_goals (user_id, goal_name, target_amount, current_amount, target_date, status)
           VALUES (?, ?, ?, 0.0, ?, 'IN_PROGRESS')""",
        (user_id, goal_name.strip(), target_amount, target_date)
    )
    goal = query_db("SELECT * FROM savings_goals WHERE id = ?", (res["lastrowid"],), one=True)
    log_audit_event(user_id, None, "CREATE_GOAL", f"Created savings goal '{goal_name}' (${target_amount:.2f})", None, "INFO")
    return True, "Savings goal vault established.", dict(goal)

def deposit_into_goal(user_id: int, goal_id: int, amount: float) -> tuple[bool, str, dict]:
    """Contribute funds into an existing savings vault."""
    if amount <= 0:
        return False, "Contribution amount must be positive.", {}

    goal = query_db("SELECT * FROM savings_goals WHERE id = ? AND user_id = ?", (goal_id, user_id), one=True)
    if not goal:
        return False, "Savings goal not found.", {}

    new_curr = goal["current_amount"] + amount
    new_status = "COMPLETED" if new_curr >= goal["target_amount"] else "IN_PROGRESS"

    execute_db(
        "UPDATE savings_goals SET current_amount = ?, status = ? WHERE id = ?",
        (new_curr, new_status, goal_id)
    )

    log_audit_event(user_id, None, "GOAL_DEPOSIT", f"Contributed ${amount:.2f} into goal #{goal_id}", None, "INFO")
    updated = query_db("SELECT * FROM savings_goals WHERE id = ?", (goal_id,), one=True)
    return True, f"Contributed ${amount:.2f} to '{goal['goal_name']}'.", dict(updated)

def delete_savings_goal(user_id: int, goal_id: int) -> tuple[bool, str]:
    """Delete a savings goal owned by the user."""
    goal = query_db("SELECT * FROM savings_goals WHERE id = ? AND user_id = ?", (goal_id, user_id), one=True)
    if not goal:
        return False, "Goal not found or unauthorized."

    execute_db("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
    log_audit_event(user_id, None, "DELETE_GOAL", f"Deleted goal #{goal_id}", None, "INFO")
    return True, "Savings goal deleted successfully."
