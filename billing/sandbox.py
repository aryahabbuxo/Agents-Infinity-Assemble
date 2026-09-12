"""
billing_sandbox.py

The Billing Agent's SANDBOX — a fake, self-contained "billing system"
for a fictional e-commerce company. It is NOT a real payment system.

Design rules (from the master project context, section 12/13/15):
  1. The agent NEVER edits state directly. It only calls tool functions.
  2. The sandbox owns the ground-truth state (hidden from the ticket text).
  3. The same customer complaint can map to DIFFERENT hidden root causes.
  4. Every tool call is logged so we can show "before -> after" as evidence.

Initial state is loaded from shared_data.ORDERS so that customer IDs,
order IDs, and order states are consistent across all three agent sandboxes.
"""

from dataclasses import dataclass, field
from typing import Optional
import copy
import sys
from pathlib import Path

# Resolve shared_data from the project root regardless of working directory.
def _add_root_to_path():
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

_add_root_to_path()
from shared_data import ORDERS, shared_state_log  # noqa: E402


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
    A tiny in-memory "billing system". Call tool functions below to inspect /
    act on it. Every action is logged in `self.log` so the dashboard / vetting
    layer can show real state changes.

    Initial state is seeded from shared_data.ORDERS — edit that file to change
    the scenario data instead of modifying this class.
    """

    def __init__(self):
        # Build records from shared_data so IDs are consistent across agents.
        self._records: dict[str, BillingRecord] = {}
        for order_id, data in ORDERS.items():
            self._records[order_id] = BillingRecord(
                order_id=order_id,
                customer_id=data["customer_id"],
                amount=data["amount"],
                payment_status=data["payment_status"],
                refund_status=data["refund_status"],
                invoice_status=data["invoice_status"],
                days_since_request=data["days_since_request"],
                reject_reason=data.get("reject_reason"),
                duplicate_charge=data.get("duplicate_charge", False),
                subscription_id=data.get("subscription_id"),
            )
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
        cust_id = self._records[order_id].customer_id if order_id in self._records else None
        ticket_id = getattr(self, "current_ticket_id", "T000")
        shared_state_log.record(
            ticket_id=ticket_id,
            agent="billing_agent",
            action=action,
            order_id=order_id,
            customer_id=cust_id,
            before=before,
            after=after
        )

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