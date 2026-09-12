"""
billing_sandbox.py

This is the Billing Agent's SANDBOX — a fake, self-contained "billing system"
for a fictional e-commerce company. It is NOT a real payment system.

Design rules (from the master project context, section 12/13/15):
  1. The agent NEVER edits state directly. It only calls tool functions.
  2. The sandbox owns the ground-truth state (hidden from the ticket text).
  3. The same customer complaint can map to DIFFERENT hidden root causes.
  4. Every tool call is logged so we can show "before -> after" as evidence.

Think of this file as a tiny fake database + a set of allowed operations
on top of it.
"""

from dataclasses import dataclass, field
from typing import Optional
import copy


@dataclass
class BillingRecord:
    order_id: str
    customer_id: str
    amount: float
    payment_status: str      # SUCCESS | FAILED | REFUND_INITIATED
    refund_status: str       # NOT_REQUESTED | PENDING | PARTIAL | PROCESSED | REJECTED | MANUAL_REVIEW
    invoice_status: str      # GENERATED | MISSING | CORRUPTED
    days_since_request: int  # how long the customer has been waiting
    reject_reason: Optional[str] = None
    duplicate_charge: bool = False
    subscription_id: Optional[str] = None


class BillingSandbox:
    """
    A tiny in-memory "billing system". Call `.tools.<n>(...)` style
    functions below to inspect / act on it. Every action is logged in
    `self.log` so the dashboard / vetting layer can show real state changes.
    """

    def __init__(self):
        # --- Ground truth data (the agent does NOT get to see this directly,
        # it must "investigate" via check_* tools) ---
        self._records: dict[str, BillingRecord] = {
            # Scenario A: refund genuinely stuck at the payment gateway
            "O-1001": BillingRecord(
                order_id="O-1001", customer_id="C-01", amount=49.99,
                payment_status="REFUND_INITIATED", refund_status="PENDING",
                invoice_status="GENERATED", days_since_request=2,
            ),
            # Scenario B: refund failed because of bad bank details
            "O-1002": BillingRecord(
                order_id="O-1002", customer_id="C-02", amount=120.00,
                payment_status="FAILED", refund_status="REJECTED",
                invoice_status="GENERATED", days_since_request=3,
                reject_reason="Invalid destination bank account",
            ),
            # Scenario C: refund already succeeded on the billing side.
            # The customer's complaint is actually a TECHNICAL / display issue.
            "O-1003": BillingRecord(
                order_id="O-1003", customer_id="C-03", amount=76.50,
                payment_status="SUCCESS", refund_status="PROCESSED",
                invoice_status="GENERATED", days_since_request=2,
            ),
            # Scenario D: invoice was never generated
            "O-1004": BillingRecord(
                order_id="O-1004", customer_id="C-04", amount=32.00,
                payment_status="SUCCESS", refund_status="NOT_REQUESTED",
                invoice_status="MISSING", days_since_request=1,
            ),
            # Scenario E: customer charged twice for the same order
            "O-1005": BillingRecord(
                order_id="O-1005", customer_id="C-05", amount=58.20,
                payment_status="SUCCESS", refund_status="NOT_REQUESTED",
                invoice_status="GENERATED", days_since_request=1,
                duplicate_charge=True,
            ),
            # Scenario F: subscription billed twice in the same cycle
            "O-1006": BillingRecord(
                order_id="O-1006", customer_id="C-06", amount=15.00,
                payment_status="SUCCESS", refund_status="NOT_REQUESTED",
                invoice_status="GENERATED", days_since_request=4,
                duplicate_charge=True, subscription_id="SUB-55",
            ),
            # Scenario G: refund only partially processed
            "O-1007": BillingRecord(
                order_id="O-1007", customer_id="C-07", amount=200.00,
                payment_status="REFUND_INITIATED", refund_status="PARTIAL",
                invoice_status="GENERATED", days_since_request=5,
            ),
        }
        self.log: list[dict] = []

    # ---------- internal helper ----------
    def _snapshot(self, order_id: str) -> dict:
        r = self._records[order_id]
        return {
            "payment_status": r.payment_status,
            "refund_status": r.refund_status,
            "invoice_status": r.invoice_status,
            "duplicate_charge": r.duplicate_charge,
        }

    def _record_action(self, order_id: str, action: str, before: dict, after: dict):
        self.log.append({
            "order_id": order_id,
            "action": action,
            "before": before,
            "after": after,
        })

    # ---------- READ-ONLY investigation tools ----------
    def check_payment_status(self, order_id: str) -> dict:
        r = self._records[order_id]
        return {"order_id": order_id, "payment_status": r.payment_status}

    def check_refund_status(self, order_id: str) -> dict:
        r = self._records[order_id]
        return {
            "order_id": order_id,
            "refund_status": r.refund_status,
            "days_since_request": r.days_since_request,
            "reject_reason": r.reject_reason,
        }

    def check_invoice(self, order_id: str) -> dict:
        r = self._records[order_id]
        return {"order_id": order_id, "invoice_status": r.invoice_status}

    def check_duplicate_charge(self, order_id: str) -> dict:
        r = self._records[order_id]
        return {
            "order_id": order_id,
            "duplicate_charge": r.duplicate_charge,
            "subscription_id": r.subscription_id,
        }

    # ---------- ACTION tools (these change state) ----------
    def release_pending_refund(self, order_id: str) -> dict:
        """Use when refund_status == PENDING and it has been stuck too long."""
        r = self._records[order_id]
        before = self._snapshot(order_id)
        if r.refund_status == "PENDING":
            r.refund_status = "PROCESSED"
            r.payment_status = "SUCCESS"
        after = self._snapshot(order_id)
        self._record_action(order_id, "release_pending_refund", before, after)
        return {"order_id": order_id, "new_refund_status": r.refund_status}

    def flag_for_manual_review(self, order_id: str, reason: str) -> dict:
        """Use when the refund cannot be auto-fixed (e.g. bad bank details)."""
        before = self._snapshot(order_id)
        r = self._records[order_id]
        r.refund_status = "MANUAL_REVIEW"
        after = self._snapshot(order_id)
        self._record_action(order_id, f"flag_for_manual_review:{reason}", before, after)
        return {"order_id": order_id, "new_refund_status": r.refund_status}

    def reissue_invoice(self, order_id: str) -> dict:
        before = self._snapshot(order_id)
        r = self._records[order_id]
        r.invoice_status = "GENERATED"
        after = self._snapshot(order_id)
        self._record_action(order_id, "reissue_invoice", before, after)
        return {"order_id": order_id, "invoice_status": r.invoice_status}

    def confirm_refund_already_processed(self, order_id: str) -> dict:
        """No state change — used when investigation shows billing is already
        correct and the customer's issue lies elsewhere (e.g. technical)."""
        before = self._snapshot(order_id)
        after = self._snapshot(order_id)
        self._record_action(order_id, "confirm_refund_already_processed (no-op)", before, after)
        return {"order_id": order_id, "refund_status": self._records[order_id].refund_status}

    def refund_duplicate_charge(self, order_id: str) -> dict:
        """Use when duplicate_charge == True: refund the extra charge."""
        before = self._snapshot(order_id)
        r = self._records[order_id]
        if r.duplicate_charge:
            r.duplicate_charge = False
            r.refund_status = "PROCESSED"
        after = self._snapshot(order_id)
        self._record_action(order_id, "refund_duplicate_charge", before, after)
        return {"order_id": order_id, "duplicate_charge": r.duplicate_charge, "refund_status": r.refund_status}

    def complete_partial_refund(self, order_id: str) -> dict:
        """Use when refund_status == PARTIAL: finish the remaining refund."""
        before = self._snapshot(order_id)
        r = self._records[order_id]
        if r.refund_status == "PARTIAL":
            r.refund_status = "PROCESSED"
            r.payment_status = "SUCCESS"
        after = self._snapshot(order_id)
        self._record_action(order_id, "complete_partial_refund", before, after)
        return {"order_id": order_id, "refund_status": r.refund_status}

    # ---------- utility for the demo / dashboard ----------
    def get_full_state(self, order_id: str) -> dict:
        return copy.deepcopy(self._snapshot(order_id))