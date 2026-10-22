"""
Mira AI Conversational Financial Copilot
Integrates Information Retrieval (IR) with banking customer intelligence:
- Natural Language Intent Classification
- Retrieval-Augmented Generation (RAG) over banking policies and IR documents
- Contextual financial advice (Balance, ATM Limits, 50/30/20 budgeting, card security)
- Executable quick-action buttons for seamless ATM terminal operations
"""

import re
from database.db import query_all, query_one
from language_models.lm_ranker import LanguageModelRanker

class MiraAICopilot:
    def __init__(self):
        self.lm_ranker = LanguageModelRanker()

    @staticmethod
    def classify_intent(message: str) -> str:
        msg = message.lower().strip()
        if any(w in msg for w in ["freeze", "block", "lock card", "stolen", "lost"]):
            return "freeze_card"
        if any(w in msg for w in ["balance", "funds", "how much money", "account balance"]):
            return "balance_inquiry"
        if any(w in msg for w in ["limit", "maximum", "how much can i withdraw", "daily limit"]):
            return "limit_inquiry"
        if any(w in msg for w in ["save", "saving", "50/30/20", "budget", "emergency fund", "wealth"]):
            return "savings_advice"
        if any(w in msg for w in ["fraud", "suspicious", "scam", "unauthorized", "dispute"]):
            return "fraud_dispute"
        if any(w in msg for w in ["face", "biometric", "camera", "liveness", "spoof", "haar"]):
            return "biometric_inquiry"
        if any(w in msg for w in ["fee", "charge", "cost", "wire fee", "interchange"]):
            return "fee_inquiry"
        if any(w in msg for w in ["withdraw", "cash", "dispense"]):
            return "withdraw_inquiry"
        return "general_faq"

    def generate_response(self, account_number: str, user_message: str, ir_algorithm: str = "dirichlet") -> dict:
        intent = self.classify_intent(user_message)
        
        # Fetch user and account details
        user = query_one("SELECT account_number, full_name, is_locked FROM users WHERE account_number = ?", (account_number,))
        account = query_one("SELECT balance, daily_limit FROM accounts WHERE account_number = ?", (account_number,))
        
        balance = account["balance"] if account else 0.0
        daily_limit = account["daily_limit"] if account else 5000.0
        first_name = user["full_name"].split()[0] if user else "Customer"
        is_locked = bool(user["is_locked"]) if user else False

        # RAG retrieval over banking policy documents
        search_results = self.lm_ranker.rank(user_message, smoothing="dirichlet" if ir_algorithm == "dirichlet" else "jelinek_mercer")
        top_doc = search_results[0] if search_results else None

        reply_text = ""
        quick_actions = []

        if intent == "balance_inquiry":
            reply_text = (
                f"Hello {first_name}! Your primary checking account currently holds **${balance:,.2f}**. "
                f"Your daily remaining ATM cash withdrawal ceiling is **${daily_limit:,.2f}**."
            )
            quick_actions = [
                {"label": "Withdraw $40", "action": "quick_withdraw", "amount": 40},
                {"label": "Withdraw $100", "action": "quick_withdraw", "amount": 100},
                {"label": "50/30/20 Budget Advice", "action": "savings_advice"}
            ]

        elif intent == "freeze_card":
            if is_locked:
                reply_text = "🔒 Your account card is **already locked**. No withdrawals can occur. Contact security administration to unlock."
                quick_actions = [{"label": "View Security Logs", "action": "view_logs"}]
            else:
                reply_text = (
                    f"🚨 **Emergency Security Action**: I can immediately place a cryptographic lock on your account "
                    f"`{account_number}` to block all unauthorized ATM cash dispensing and transactions."
                )
                quick_actions = [
                    {"label": "Confirm Freeze Account", "action": "freeze_account", "style": "danger"},
                    {"label": "Keep Active", "action": "dismiss"}
                ]

        elif intent == "limit_inquiry":
            reply_text = (
                f"Your standard daily ATM withdrawal ceiling is **${daily_limit:,.2f}**. "
                f"Single-transaction dispensing limit at this terminal is **$800.00** per cash cycle in bills of $100, $50, and $20."
            )
            quick_actions = [
                {"label": "Withdraw $200", "action": "quick_withdraw", "amount": 200},
                {"label": "View Mini-Statement", "action": "view_transactions"}
            ]

        elif intent == "savings_advice":
            needs = round(balance * 0.50, 2)
            wants = round(balance * 0.30, 2)
            savings = round(balance * 0.20, 2)
            reply_text = (
                f"Smart financial strategy, {first_name}! Based on your current balance of **${balance:,.2f}**, "
                f"here is your optimal **50/30/20 wealth allocation**:\n\n"
                f"- **50% Essentials (Needs):** ~${needs:,.2f} (Housing, utilities, groceries)\n"
                f"- **30% Discretionary (Wants):** ~${wants:,.2f} (Entertainment, dining)\n"
                f"- **20% Wealth Building (Savings):** ~${savings:,.2f} (Emergency buffer & investments)\n\n"
                f"Would you like to allocate $50 into your Emergency Fund today?"
            )
            quick_actions = [
                {"label": "Deposit $50 into Emergency Buffer", "action": "quick_save", "amount": 50},
                {"label": "Check Balance", "action": "ask_balance"}
            ]

        elif intent == "biometric_inquiry":
            reply_text = (
                "🛡️ **Biometric Optical Defense**: This terminal enforces multi-factor liveness testing. "
                "Beyond Local Binary Patterns Histograms (LBPH), our optical scanner tests for:\n"
                "- **Laplacian Texture Variance:** Identifies blurry 2D printed photo attacks.\n"
                "- **YCrCb Skin Reflectance:** Validates genuine human skin chrominance spectrum.\n"
                "- **Specular Screen Glare:** Detects screen replays and backlight reflections."
            )
            quick_actions = [
                {"label": "Open Biometric Lab", "action": "view_biometrics"},
                {"label": "Check Security Status", "action": "ask_balance"}
            ]

        elif intent == "withdraw_inquiry":
            reply_text = f"You can withdraw cash directly at this terminal. Current balance is **${balance:,.2f}**."
            quick_actions = [
                {"label": "Withdraw $20", "action": "quick_withdraw", "amount": 20},
                {"label": "Withdraw $60", "action": "quick_withdraw", "amount": 60},
                {"label": "Withdraw $100", "action": "quick_withdraw", "amount": 100}
            ]

        else:
            # Fallback to IR RAG Knowledge Retrieval
            doc_context = ""
            if top_doc:
                doc_context = f"\n\n*Relevant Policy [{top_doc['category']}]:* **{top_doc['title']}**\n{top_doc['snippet'][:180]}..."
            reply_text = (
                f"I processed your query through our Language Model Retrieval engine.{doc_context}\n\n"
                f"How else may I assist with your ATM banking operations today, {first_name}?"
            )
            quick_actions = [
                {"label": "Check Balance", "action": "ask_balance"},
                {"label": "50/30/20 Budget Advice", "action": "savings_advice"}
            ]

        return {
            "success": True,
            "intent": intent,
            "reply": reply_text,
            "response": reply_text,
            "quick_actions": quick_actions,
            "retrieved_doc": top_doc["title"] if top_doc else None
        }
