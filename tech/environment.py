from copy import deepcopy
import sys
from pathlib import Path


def _add_root_to_path():
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


_add_root_to_path()
from shared_data import CUSTOMERS, ORDERS  # noqa: E402


class EcommerceEnvironment:
    """
    Fake e-commerce technical environment for a single active customer context.

    State is seeded from shared_data (CUSTOMERS + ORDERS) so that technical
    sandbox IDs are consistent with billing and retention sandboxes.

    Call set_customer(customer_id) before processing each ticket to reset the
    environment to the correct customer's data from shared_data.
    """

    def __init__(self, customer_id: str = "C001"):
        self.state = self._build_state(customer_id)

    def _build_state(self, customer_id: str) -> dict:
        customer = CUSTOMERS.get(customer_id) or CUSTOMERS["C001"]
        tech = customer.get("tech_state", {})

        # Populate orders: only those that have a tech_state entry.
        orders = {}
        for order_id, order_data in ORDERS.items():
            ts = order_data.get("tech_state")
            if ts is not None:
                orders[order_id] = {
                    "exists": ts.get("exists", True),
                    "visible": ts.get("visible", True),
                    "sync_status": ts.get("sync_status", "HEALTHY"),
                    "status": ts.get("status", "ACTIVE"),
                }

        return {
            "customer": {
                "customer_id": customer_id,
                "account_status": tech.get("account_status", "ACTIVE"),
                "session_status": tech.get("session_status", "ACTIVE"),
                "login_failures": tech.get("login_failures", 0),
            },

            "orders": orders,

            "dashboard": {
                "status": "HEALTHY",
                "error_code": None
            },

            "cart": {
                "status": "HEALTHY",
                "sync_status": "HEALTHY"
            },

            "search": {
                "status": "HEALTHY",
                "index_status": "HEALTHY"
            },

            "checkout": {
                "status": "HEALTHY",
                "session_status": "ACTIVE"
            },

            "notifications": {
                "status": "HEALTHY"
            },

            "services": {
                "order_service": "HEALTHY",
                "dashboard_service": "HEALTHY",
                "cart_service": "HEALTHY",
                "checkout_service": "HEALTHY",
                "notification_service": "HEALTHY"
            }
        }

    def set_customer(self, customer_id: str) -> None:
        """Reset the environment for a new customer context (call before each ticket)."""
        self.state = self._build_state(customer_id)

    def get_state(self) -> dict:
        return deepcopy(self.state)