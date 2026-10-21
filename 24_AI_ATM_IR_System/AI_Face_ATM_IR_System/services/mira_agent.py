import re
from datetime import datetime
from services.ir_service import kb_engine

def classify_intent(message: str) -> str:
    """Classifies user intent from natural language input."""
    msg = message.lower()
    
    if any(k in msg for k in ["freeze", "block card", "lost card", "stolen", "lock card"]):
        return "freeze_card"
    if any(k in msg for k in ["balance", "how much money", "account balance", "funds"]):
        return "balance_inquiry"
    if any(k in msg for k in ["limit", "maximum withdraw", "how much can i withdraw", "daily limit"]):
        return "limit_inquiry"
    if any(k in msg for k in ["save", "saving", "50/30/20", "budget", "emergency fund", "invest"]):
        return "savings_advice"
    if any(k in msg for k in ["fraud", "suspicious", "stolen", "unauthorized", "scam", "dispute"]):
        return "fraud_dispute"
    if any(k in msg for k in ["fee", "charge", "cost", "wire fee", "transfer fee"]):
        return "fee_inquiry"
    if any(k in msg for k in ["deposit", "cash in", "envelope"]):
        return "deposit_inquiry"
    if any(k in msg for k in ["face", "biometric", "camera", "liveness", "spoof"]):
        return "biometric_inquiry"
    if any(k in msg for k in ["travel", "foreign", "abroad", "international", "exchange"]):
        return "travel_inquiry"
    if any(k in msg for k in ["pin", "password", "reset pin"]):
        return "pin_inquiry"

    return "general_faq"


def generate_mira_response(user, account, message: str, ir_algorithm: str = "bm25") -> dict:
    """
    RAG-powered conversational agent Mira.
    Retrieves knowledge base articles and formulates tailored financial advice
    with contextual customer balance and quick action buttons.
    """
    intent = classify_intent(message)

    # 1. Retrieve most relevant knowledge base articles using IR engine
    if ir_algorithm == "tfidf":
        retrieved_docs = kb_engine.search_tfidf(message, top_k=2)
    elif ir_algorithm == "query_likelihood":
        retrieved_docs = kb_engine.search_query_likelihood(message, top_k=2)
    else:
        retrieved_docs = kb_engine.search_bm25(message, top_k=2)

    top_doc = retrieved_docs[0] if retrieved_docs else None

    # Contextual variables
    balance = account.balance if account else 0.0
    daily_rem = (account.daily_limit - account.daily_withdrawn_today) if account else 2000.0
    user_name = user.full_name.split()[0] if (user and user.full_name) else "there"

    reply_text = ""
    quick_actions = []

    if intent == "balance_inquiry":
        reply_text = (
            f"Hello {user_name}! Your primary checking account currently holds **${balance:,.2f}**. "
            f"You have **${max(0.0, daily_rem):,.2f}** remaining in your daily ATM cash limit."
        )
        quick_actions = [
            {"label": "Withdraw $40", "type": "action", "action": "quick_withdraw", "amount": 40},
            {"label": "Withdraw $100", "type": "action", "action": "quick_withdraw", "amount": 100},
            {"label": "View Goals", "type": "navigate", "tab": "savings"}
        ]

    elif intent == "freeze_card":
        reply_text = (
            f"🚨 **Security Alert**: I can immediately initiate an emergency lock on your account to halt "
            f"all ATM cash withdrawals and card transactions. "
            f"Click the confirmation button below to freeze your card right now."
        )
        quick_actions = [
            {"label": "Confirm Freeze Account", "type": "action", "action": "freeze_account", "style": "danger"},
            {"label": "Cancel / Keep Active", "type": "action", "action": "dismiss"}
        ]

    elif intent == "limit_inquiry":
        reply_text = (
            f"Your standard daily ATM withdrawal ceiling is **${account.daily_limit:,.2f}**. "
            f"You have withdrawn **${account.daily_withdrawn_today:,.2f}** today, leaving **${max(0.0, daily_rem):,.2f}** available. "
            f"The single-transaction terminal limit is **$800.00**."
        )
        quick_actions = [
            {"label": "Withdraw Max Cash", "type": "action", "action": "quick_withdraw", "amount": min(800.0, daily_rem)},
            {"label": "Savings Suggestions", "type": "navigate", "tab": "savings"}
        ]

    elif intent == "savings_advice":
        reply_text = (
            f"Great financial question, {user_name}! I recommend following the **50/30/20 budgeting framework**:\n\n"
            f"- **50% Essentials**: Rent, groceries, bills.\n"
            f"- **30% Discretionary**: Entertainment, dining.\n"
            f"- **20% Wealth Building**: Emergency savings and long-term goals.\n\n"
            f"With your balance of **${balance:,.2f}**, setting aside even $25 per week in an automated goal "
            f"accumulates **$1,300/year** with zero stress!"
        )
        quick_actions = [
            {"label": "Explore Savings Goals", "type": "navigate", "tab": "savings"},
            {"label": "Enable 5% Round-Up", "type": "action", "action": "enable_roundup"}
        ]

    elif intent == "fraud_dispute":
        reply_text = (
            f"🛡️ **Fraud Protection Assurance**: Mira AI systems continuously monitor transaction patterns. "
            f"You have **100% Zero-Liability Protection** against unauthorized transactions. "
            f"If you spot a suspicious charge in your history, you can dispute it with one click."
        )
        quick_actions = [
            {"label": "Review Transactions", "type": "navigate", "tab": "transactions"},
            {"label": "Freeze Account Now", "type": "action", "action": "freeze_account", "style": "danger"}
        ]

    elif intent == "fee_inquiry":
        reply_text = (
            f"Here is our clear fee breakdown:\n\n"
            f"- **ATM Cash Withdrawals**: $0.00 at all Mira Smart ATMs.\n"
            f"- **Internal Transfers**: Instant and 100% fee-free.\n"
            f"- **Overdraft Protection**: $0.00 penalty fee for active accounts.\n"
            f"- **External Transfers**: $1.50 network clearance fee."
        )
        quick_actions = [
            {"label": "Transfer Funds", "type": "navigate", "tab": "transfer"}
        ]

    else:
        # RAG fallback using retrieved document
        if top_doc and top_doc["relevance_score"] > 20:
            reply_text = (
                f"Here is what I found regarding your question:\n\n"
                f"**{top_doc['title']}**\n\n"
                f"{top_doc['content']}\n\n"
                f"Can I assist you with any related banking task?"
            )
        else:
            reply_text = (
                f"I am Mira, your intelligent ATM copilot. I can help you check your balances, "
                f"conduct secure cash withdrawals, explain transaction limits, freeze compromised cards, "
                f"or plan personalized savings goals. What would you like to do?"
            )
        quick_actions = [
            {"label": "Check Balance", "type": "action", "action": "ask_balance"},
            {"label": "Withdraw Cash", "type": "action", "action": "open_withdraw"},
            {"label": "Savings Advice", "type": "navigate", "tab": "savings"}
        ]

    return {
        "reply": reply_text,
        "intent": intent,
        "retrieved_docs": retrieved_docs[:2],
        "quick_actions": quick_actions,
        "timestamp": datetime.utcnow().isoformat()
    }
