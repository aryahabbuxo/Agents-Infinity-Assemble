from copy import deepcopy
from datetime import datetime
import sys
from pathlib import Path

def _add_root_to_path():
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

_add_root_to_path()
from shared_data import shared_state_log  # noqa: E402


class TechnicalSandbox:

    def __init__(self, environment):

        self.environment = environment
        self.audit_log = []

    def _log(self, event, details=None):

        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "details": details
        })

    # ==========================================
    # DIAGNOSTIC TOOLS
    # ==========================================

    def list_orders(self):
        orders = self.environment.state["orders"]

        result = []

        for order_id, order in orders.items():
            result.append({
                "order_id": order_id,
                "exists": order["exists"],
                "visible": order["visible"],
                "status": order["status"]
            })

        return {
            "success": True,
            "orders": result
        }

    def check_account(self):

        state = self.environment.state["customer"]

        result = {
            "account_status": state["account_status"],
            "session_status": state["session_status"],
            "login_failures": state["login_failures"]
        }

        self._log("check_account", result)

        return result

    def check_order(self, order_id):
        orders = self.environment.state["orders"]

        if order_id not in orders:
            return {
                "success": False,
                "error": f"Order {order_id} not found."
            }

        order = orders[order_id]

        return {
            "success": True,
            "order_id": order_id,
            "exists": order["exists"],
            "visible": order["visible"],
            "sync_status": order["sync_status"],
            "status": order["status"]
        }

    def check_dashboard(self):

        result = deepcopy(
            self.environment.state["dashboard"]
        )

        self._log("check_dashboard", result)

        return result

    def check_cart(self):

        result = deepcopy(
            self.environment.state["cart"]
        )

        self._log("check_cart", result)

        return result

    def check_search(self):

        result = deepcopy(
            self.environment.state["search"]
        )

        self._log("check_search", result)

        return result

    def check_checkout(self):

        result = deepcopy(
            self.environment.state["checkout"]
        )

        self._log("check_checkout", result)

        return result

    def check_notifications(self):

        result = deepcopy(
            self.environment.state["notifications"]
        )

        self._log("check_notifications", result)

        return result

    def check_service_health(self):

        result = deepcopy(
            self.environment.state["services"]
        )

        self._log("check_service_health", result)

        return result

    # ==========================================
    # ACTION TOOLS
    # ==========================================

    def unlock_account(self):

        state = self.environment.state["customer"]

        if state["account_status"] != "LOCKED":

            result = {
                "success": False,
                "message": "Account is not locked."
            }

            self._log("unlock_account", result)

            return result

        before = deepcopy(state)
        state["account_status"] = "ACTIVE"
        state["login_failures"] = 0
        after = deepcopy(state)

        result = {
            "success": True,
            "message": "Account unlocked successfully."
        }

        self._log("unlock_account", result)
        t_id = getattr(self, "current_ticket_id", "T004")
        shared_state_log.record(
            ticket_id=t_id,
            agent="technical_agent",
            action="unlock_account",
            customer_id=state.get("customer_id"),
            before=before,
            after=after
        )

        return result

    def reset_session(self):

        self.environment.state["customer"]["session_status"] = "ACTIVE"

        result = {
            "success": True,
            "message": "Session reset successfully."
        }

        self._log("reset_session", result)

        return result

    def resync_orders(self, order_id):
        orders = self.environment.state["orders"]

        if order_id not in orders:
            return {
                "success": False,
                "error": f"Order {order_id} not found."
            }

        order = orders[order_id]

        # The repair only makes sense if the order exists.
        if not order["exists"]:
            return {
                "success": False,
                "error": f"Order {order_id} does not exist."
            }

        before = deepcopy(order)
        order["sync_status"] = "HEALTHY"
        order["visible"] = True
        after = deepcopy(order)

        t_id = getattr(self, "current_ticket_id", "T007")
        shared_state_log.record(
            ticket_id=t_id,
            agent="technical_agent",
            action="resync_orders",
            order_id=order_id,
            before=before,
            after=after
        )

        return {
            "success": True,
            "order_id": order_id,
            "sync_status": order["sync_status"],
            "visible": order["visible"],
            "message": f"Order {order_id} successfully resynchronized."
        }
    
    def restore_dashboard(self):

        dashboard = self.environment.state["dashboard"]

        if dashboard["status"] == "HEALTHY":

            result = {
                "success": False,
                "message": "Dashboard is already healthy."
            }

            self._log("restore_dashboard", result)

            return result

        dashboard["status"] = "HEALTHY"
        dashboard["error_code"] = None

        result = {
            "success": True,
            "message": "Dashboard restored successfully."
        }

        self._log("restore_dashboard", result)

        return result

    def refresh_cart(self):

        cart = self.environment.state["cart"]

        cart["status"] = "HEALTHY"
        cart["sync_status"] = "HEALTHY"

        result = {
            "success": True,
            "message": "Cart refreshed successfully."
        }

        self._log("refresh_cart", result)

        return result

    def rebuild_search_index(self):

        search = self.environment.state["search"]

        search["status"] = "HEALTHY"
        search["index_status"] = "HEALTHY"

        result = {
            "success": True,
            "message": "Search index rebuilt successfully."
        }

        self._log("rebuild_search_index", result)

        return result

    def reset_checkout_session(self):

        checkout = self.environment.state["checkout"]

        checkout["status"] = "HEALTHY"
        checkout["session_status"] = "ACTIVE"

        result = {
            "success": True,
            "message": "Checkout session reset successfully."
        }

        self._log("reset_checkout_session", result)

        return result

    def restore_notifications(self):

        notifications = self.environment.state["notifications"]

        notifications["status"] = "HEALTHY"

        self.environment.state["services"][
            "notification_service"
        ] = "HEALTHY"

        result = {
            "success": True,
            "message": "Notification service restored successfully."
        }

        self._log("restore_notifications", result)

        return result

    # ==========================================
    # VERIFICATION
    # ==========================================

    def verify_order(self, order_id):

        orders = self.environment.state["orders"]

        if order_id not in orders:
            return {
                "success": False,
                "message": "Order not found."
            }

        order = orders[order_id]

        result = {
            "order_exists": order["exists"],
            "order_visible": order["visible"],
            "sync_healthy": order["sync_status"] == "HEALTHY"
        }

        self._log("verify_order", result)

        return result

    def verify_account(self):

        state = self.environment.state["customer"]

        result = {
            "account_active":
                state["account_status"] == "ACTIVE",

            "session_active":
                state["session_status"] == "ACTIVE"
        }

        self._log("verify_account", result)

        return result

    def verify_dashboard(self):

        dashboard = self.environment.state["dashboard"]

        result = {
            "dashboard_healthy":
                dashboard["status"] == "HEALTHY"
        }

        self._log("verify_dashboard", result)

        return result

    # ==========================================
    # AUDIT
    # ==========================================

    def get_audit_log(self):

        return deepcopy(self.audit_log)