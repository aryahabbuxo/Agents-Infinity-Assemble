import sys
from pathlib import Path

def _add_root_to_path():
    root = Path(__file__).parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

_add_root_to_path()
from shared_data import shared_state_log  # noqa: E402


class RetentionTools:

    def __init__(self, sandbox):
        self.sandbox = sandbox

    # =========================================================
    # READ-ONLY TOOLS
    # =========================================================

    def get_customer_profile(self, customer_id):

        customer = self.sandbox.get_customer(
            customer_id
        )

        if customer is None:
            return {
                "success": False,
                "error": f"Customer {customer_id} not found."
            }

        return {
            "success": True,
            "customer_id": customer_id,
            "profile": customer.copy()
        }

    def check_cancellation_status(self, customer_id):

        customer = self.sandbox.get_customer(
            customer_id
        )

        if customer is None:
            return {
                "success": False,
                "error": f"Customer {customer_id} not found."
            }

        return {
            "success": True,
            "cancellation_requested": customer.get(
                "cancellation_requested",
                False
            ),
            "subscription_status": customer.get(
                "subscription_status"
            )
        }

    def check_retention_offer(self, customer_id):

        customer = self.sandbox.get_customer(
            customer_id
        )

        if customer is None:
            return {
                "success": False,
                "error": f"Customer {customer_id} not found."
            }

        return {
            "success": True,
            "offer_available": customer.get(
                "retention_offer_available",
                False
            )
        }

    # =========================================================
    # STATE-CHANGING TOOLS
    # =========================================================

    def apply_retention_offer(self, customer_id):

        customer = self.sandbox.get_customer(
            customer_id
        )

        if customer is None:
            return {
                "success": False,
                "error": f"Customer {customer_id} not found."
            }

        # -----------------------------------------------------
        # Verify offer availability
        # -----------------------------------------------------

        if not customer.get(
            "retention_offer_available",
            False
        ):

            return {
                "success": False,
                "error": "No retention offer is currently available."
            }

        # -----------------------------------------------------
        # Capture state BEFORE action
        # -----------------------------------------------------

        before = customer.copy()

        # -----------------------------------------------------
        # Perform controlled state change
        # -----------------------------------------------------

        customer["retention_offer_available"] = False

        current_satisfaction = customer.get(
            "satisfaction_score",
            0
        )

        customer["satisfaction_score"] = min(
            100,
            current_satisfaction + 20
        )

        self.sandbox.save()

        # -----------------------------------------------------
        # Capture state AFTER action
        # -----------------------------------------------------

        after = customer.copy()

        evidence = {
            "customer_id": customer_id,
            "action": "apply_retention_offer",
            "before": before,
            "after": after
        }

        self.sandbox.record_action(
            evidence
        )
        t_id = getattr(self.sandbox, "current_ticket_id", "T003")
        shared_state_log.record(
            ticket_id=t_id,
            agent="retention_agent",
            action="apply_retention_offer",
            customer_id=customer_id,
            before=before,
            after=after
        )

        return {
            "success": True,
            "action": "retention_offer_applied",
            "state_before_after": evidence
        }

    # =========================================================
    # CANCEL SUBSCRIPTION
    # =========================================================

    def cancel_subscription(self, customer_id):

        customer = self.sandbox.get_customer(
            customer_id
        )

        if customer is None:
            return {
                "success": False,
                "error": f"Customer {customer_id} not found."
            }

        # -----------------------------------------------------
        # SAFETY GUARD
        # -----------------------------------------------------

        if not customer.get(
            "cancellation_requested",
            False
        ):

            return {
                "success": False,
                "error": (
                    "Cancellation rejected. "
                    "The customer has not explicitly requested "
                    "cancellation."
                )
            }

        # -----------------------------------------------------
        # Already cancelled
        # -----------------------------------------------------

        if customer.get(
            "subscription_status"
        ) == "cancelled":

            return {
                "success": False,
                "error": "Subscription is already cancelled."
            }

        # -----------------------------------------------------
        # Capture BEFORE
        # -----------------------------------------------------

        before = customer.copy()

        # -----------------------------------------------------
        # Controlled state mutation
        # -----------------------------------------------------

        customer["subscription_status"] = "cancelled"

        self.sandbox.save()

        # -----------------------------------------------------
        # Capture AFTER
        # -----------------------------------------------------

        after = customer.copy()

        evidence = {
            "customer_id": customer_id,
            "action": "cancel_subscription",
            "before": before,
            "after": after
        }

        self.sandbox.record_action(
            evidence
        )
        t_id = getattr(self.sandbox, "current_ticket_id", "T003")
        shared_state_log.record(
            ticket_id=t_id,
            agent="retention_agent",
            action="cancel_subscription",
            customer_id=customer_id,
            before=before,
            after=after
        )

        return {
            "success": True,
            "action": "subscription_cancelled",
            "state_before_after": evidence
        }