"""
capability.py

Section 9 of the master context: agents broadcast a short description of
what they can and can't do, BEFORE any ticket arrives. Other agents use
this when deciding who to negotiate with.
"""

CAPABILITY_CARD = {
    "agent_id": "billing_agent",
    "display_name": "Billing Agent",
    "handles": [
        "payments",
        "refunds",
        "transactions",
        "invoices",
        "charges / billing disputes",
        "subscription payment issues",
        "duplicate charges",
    ],
    "does_not_handle": [
        "dashboard / UI bugs",
        "login / authentication problems",
        "API errors",
        "customer retention / cancellation conversations",
    ],
    "best_suited_for": (
        "Tickets about money: refunds not received, incorrect charges, "
        "failed payments, missing or wrong invoices, subscription billing, "
        "duplicate/double charges."
    ),
}

# crude keyword weights used for the rule-based raw_confidence estimate.
# This is also the offline fallback if the LLM call in bidding.py fails.
BILLING_KEYWORDS = {
    "refund": 0.35,
    "money": 0.25,
    "charge": 0.25,
    "charged": 0.25,
    "payment": 0.3,
    "invoice": 0.3,
    "billing": 0.3,
    "transaction": 0.25,
    "subscription": 0.25,
    "price": 0.15,
    "receipt": 0.2,
    "refunded": 0.35,
    "transferred back": 0.3,
    "duplicate": 0.3,
    "twice": 0.25,
    "double": 0.2,
    "double-billed": 0.3,
    "double charged": 0.3,
}