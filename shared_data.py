"""
shared_data.py  —  Single Source of Truth

All three agent sandboxes (billing, technical, retention) read their initial
state from this file.  Any state-changing action taken during a run is
collected here via SharedStateLog, and the orchestrator writes the entire log
to shared_state_log.json at the end of the run for cross-agent review.

ID conventions (unified across all agents):
  Customers  : C001, C002, C003, C004
  Orders     : O-1001 … O-1007
  Tickets    : T002, T003, T004, T007
"""

import json
import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMERS
#   billing_state  → used by BillingSandbox (no extra fields needed, billing
#                    uses ORDERS for its per-order records)
#   tech_state     → used by EcommerceEnvironment
#   retention fields (all top-level keys except tech_state) → RetentionSandbox
# ─────────────────────────────────────────────────────────────────────────────
CUSTOMERS: dict = {
    "C001": {
        # Identity
        "name": "Rahul",
        # Retention fields
        "subscription": "premium",
        "subscription_status": "active",
        "months_as_customer": 36,
        "complaints_last_30_days": 3,
        "satisfaction_score": 45,
        "cancellation_requested": False,
        "loyalty_points": 1200,
        "retention_offer_available": False,
        # Technical environment state
        "tech_state": {
            "account_status": "ACTIVE",
            "session_status": "ACTIVE",
            "login_failures": 0,
        },
    },
    "C002": {
        "name": "Priya",
        "subscription": "basic",
        "subscription_status": "active",
        "months_as_customer": 2,
        "complaints_last_30_days": 0,
        "satisfaction_score": 82,
        "cancellation_requested": False,
        "loyalty_points": 100,
        "retention_offer_available": False,
        "tech_state": {
            "account_status": "ACTIVE",
            "session_status": "ACTIVE",
            "login_failures": 0,
        },
    },
    "C003": {
        "name": "Arjun",
        "subscription": "premium",
        "subscription_status": "active",
        "months_as_customer": 18,
        "complaints_last_30_days": 5,
        "satisfaction_score": 32,
        "cancellation_requested": True,   # explicit cancellation already on file
        "loyalty_points": 850,
        "retention_offer_available": False,
        "tech_state": {
            "account_status": "ACTIVE",
            "session_status": "ACTIVE",
            "login_failures": 0,
        },
    },
    "C004": {
        "name": "Meera",
        "subscription": "basic",
        "subscription_status": "active",
        "months_as_customer": 7,
        "complaints_last_30_days": 1,
        "satisfaction_score": 60,
        "cancellation_requested": False,
        "loyalty_points": 250,
        "retention_offer_available": False,
        "tech_state": {
            "account_status": "LOCKED",   # fault: account locked (T004 scenario)
            "session_status": "EXPIRED",
            "login_failures": 5,
        },
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# ORDERS
#   billing fields  → payment_status, refund_status, invoice_status, etc.
#   tech_state      → visible, sync_status, status  (None = no tech entry)
#   customer_id     → links order to customer (unified ID)
# ─────────────────────────────────────────────────────────────────────────────
ORDERS: dict = {
    # Scenario A — refund stuck at payment gateway (T002, customer C002)
    "O-1001": {
        "customer_id": "C002",
        "amount": 49.99,
        "payment_status": "REFUND_INITIATED",
        "refund_status": "PENDING",
        "invoice_status": "GENERATED",
        "days_since_request": 2,
        "reject_reason": None,
        "duplicate_charge": False,
        "subscription_id": None,
        "tech_state": {
            "exists": True,
            "visible": True,
            "sync_status": "HEALTHY",
            "status": "DELIVERED",
        },
    },
    # Scenario B — refund rejected due to bad bank details (T003, customer C003)
    "O-1002": {
        "customer_id": "C003",
        "amount": 120.00,
        "payment_status": "FAILED",
        "refund_status": "REJECTED",
        "invoice_status": "GENERATED",
        "days_since_request": 3,
        "reject_reason": "Invalid destination bank account",
        "duplicate_charge": False,
        "subscription_id": None,
        "tech_state": {
            "exists": True,
            "visible": True,
            "sync_status": "HEALTHY",
            "status": "ACTIVE",
        },
    },
    # Scenario C — refund already processed; order invisible (T007, customer C001)
    # Billing side: PROCESSED.  Tech side: display fault (visible=False, sync=FAILED)
    "O-1003": {
        "customer_id": "C001",
        "amount": 76.50,
        "payment_status": "SUCCESS",
        "refund_status": "PROCESSED",
        "invoice_status": "GENERATED",
        "days_since_request": 2,
        "reject_reason": None,
        "duplicate_charge": False,
        "subscription_id": None,
        "tech_state": {
            "exists": True,
            "visible": False,            # fault: order not visible in dashboard
            "sync_status": "FAILED",     # fault: desynchronised
            "status": "RETURN_REQUESTED",
        },
    },
    # Scenario D — invoice never generated (T004, customer C004)
    # Billing side: invoice MISSING.  Tech side: healthy (account is LOCKED, not order issue)
    "O-1004": {
        "customer_id": "C004",
        "amount": 32.00,
        "payment_status": "SUCCESS",
        "refund_status": "NOT_REQUESTED",
        "invoice_status": "MISSING",
        "days_since_request": 1,
        "reject_reason": None,
        "duplicate_charge": False,
        "subscription_id": None,
        "tech_state": {
            "exists": True,
            "visible": True,
            "sync_status": "HEALTHY",
            "status": "DELIVERED",
        },
    },
    # Scenario E — duplicate charge on a standalone order
    "O-1005": {
        "customer_id": "C001",
        "amount": 58.20,
        "payment_status": "SUCCESS",
        "refund_status": "NOT_REQUESTED",
        "invoice_status": "GENERATED",
        "days_since_request": 1,
        "reject_reason": None,
        "duplicate_charge": True,
        "subscription_id": None,
        "tech_state": None,
    },
    # Scenario F — subscription billed twice in same cycle
    "O-1006": {
        "customer_id": "C002",
        "amount": 15.00,
        "payment_status": "SUCCESS",
        "refund_status": "NOT_REQUESTED",
        "invoice_status": "GENERATED",
        "days_since_request": 4,
        "reject_reason": None,
        "duplicate_charge": True,
        "subscription_id": "SUB-55",
        "tech_state": None,
    },
    # Scenario G — refund only partially processed
    "O-1007": {
        "customer_id": "C003",
        "amount": 200.00,
        "payment_status": "REFUND_INITIATED",
        "refund_status": "PARTIAL",
        "invoice_status": "GENERATED",
        "days_since_request": 5,
        "reject_reason": None,
        "duplicate_charge": False,
        "subscription_id": None,
        "tech_state": None,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# TICKETS
#   The orchestrator iterates over this list in order.
#   T007 — multi-domain: billing (refund) + technical (display)
#   T002 — billing: pending refund
#   T003 — retention: subscription cancellation (+ billing anomaly in sandbox)
#   T004 — technical: locked account (exercises technical_agent as lead)
# ─────────────────────────────────────────────────────────────────────────────
TICKETS: list = [
    {
        "ticket_id": "T007",
        "urgency_score": 72,
        "text": (
            "I had an item marked for return and refund however it's no longer visible "
            "in my orders section in my profile dashboard. I want my money transferred "
            "back to me immediately. I am losing my patience, this issue hasn't been "
            "addressed since 2 days."
        ),
        "order_id": "O-1003",
        "customer_id": "C001",
    },
    {
        "ticket_id": "T002",
        "urgency_score": 40,
        "text": "My refund hasn't shown up yet, it's been 2 days, please check the payment.",
        "order_id": "O-1001",
        "customer_id": "C002",
    },
    {
        "ticket_id": "T003",
        "urgency_score": 85,
        "text": (
            "I have been a customer for 3 years and I've had so many issues recently. "
            "Nobody helps me. I want to cancel my subscription immediately!"
        ),
        "order_id": "O-1002",
        "customer_id": "C003",
    },
    {
        "ticket_id": "T004",
        "urgency_score": 60,
        "text": (
            "I cannot log into my account at all! It keeps saying my account is locked. "
            "I have tried multiple times but nothing works. Please unlock my account."
        ),
        "order_id": "O-1004",
        "customer_id": "C004",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# SHARED STATE LOG
#   Written to disk after each orchestrator run so every state change made by
#   every agent is visible in one place for review and cross-checking.
# ─────────────────────────────────────────────────────────────────────────────
STATE_LOG_PATH = Path(__file__).parent / "shared_state_log.json"


class SharedStateLog:
    """
    Accumulator for all sandbox state-change events across all agents.
    The orchestrator calls .dump() once at the end of the run to persist to disk.
    """

    entries: list = []

    def __init__(self):
        pass

    def record(
        self,
        *,
        ticket_id: str,
        agent: str,
        action: str,
        order_id: str | None = None,
        customer_id: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
        extra: dict | None = None,
    ) -> None:
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "ticket_id": ticket_id,
            "agent": agent,
            "action": action,
        }
        if order_id is not None:
            entry["order_id"] = order_id
        if customer_id is not None:
            entry["customer_id"] = customer_id
        if before is not None:
            entry["before"] = before
        if after is not None:
            entry["after"] = after
        if extra:
            entry.update(extra)
        SharedStateLog.entries.append(entry)

    def dump(self) -> int:
        """Write all entries to STATE_LOG_PATH. Returns number of entries written."""
        with open(STATE_LOG_PATH, "w", encoding="utf-8") as fh:
            json.dump(SharedStateLog.entries, fh, indent=2, default=str)
        return len(SharedStateLog.entries)


# Global singleton instance for cross-agent state logging
shared_state_log = SharedStateLog()

