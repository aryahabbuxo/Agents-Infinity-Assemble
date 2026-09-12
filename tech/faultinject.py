"""
faultinject.py

Applies a hidden fault to the simulated e-commerce environment.
This file contains deterministic Python logic only.
"""


def inject_fault(env, fault_id, target=None):

    if fault_id == "ORDER_SYNC_FAILURE":
        return inject_order_sync_failure(env,target)

    elif fault_id == "ACCOUNT_LOCKED":
        return inject_account_locked(env)

    elif fault_id == "SESSION_EXPIRED":
        return inject_session_expired(env)

    elif fault_id == "DASHBOARD_FAILURE":
        return inject_dashboard_failure(env)

    elif fault_id == "CART_SYNC_FAILURE":
        return inject_cart_sync_failure(env)

    elif fault_id == "SEARCH_FAILURE":
        return inject_search_failure(env)

    elif fault_id == "CHECKOUT_SESSION_FAILURE":
        return inject_checkout_session_failure(env)

    elif fault_id == "NOTIFICATION_FAILURE":
        return inject_notification_failure(env)

    elif fault_id == "ORDER_SERVICE_FAILURE":
        return inject_order_service_failure(env)

    elif fault_id == "NO_TECHNICAL_FAULT":
        return inject_no_technical_fault(env)

    else:
        raise ValueError(f"Unknown fault ID: {fault_id}")


# ---------------------------------------------------------
# Individual fault injections
# ---------------------------------------------------------

def inject_order_sync_failure(env, order_id):

    if order_id is None:
        raise ValueError("ORDER_SYNC_FAILURE requires an order ID")

    if order_id not in env.state["orders"]:
        raise ValueError(f"Unknown order ID: {order_id}")

    env.state["orders"][order_id]["visible"] = False
    env.state["orders"][order_id]["sync_status"] = "FAILED"

    return f"Order synchronization failure injected for {order_id}."


def inject_account_locked(env):

    env.state["customer"]["account_status"] = "LOCKED"

    return "Account lock injected."


def inject_session_expired(env):

    env.state["customer"]["session_status"] = "EXPIRED"

    return "Session expiry injected."


def inject_dashboard_failure(env):

    env.state["dashboard"]["status"] = "FAILED"
    env.state["dashboard"]["error_code"] = "DASH-500"

    return "Dashboard failure injected."


def inject_cart_sync_failure(env):

    env.state["cart"]["sync_status"] = "FAILED"

    return "Cart synchronization failure injected."


def inject_search_failure(env):

    env.state["search"]["status"] = "FAILED"
    env.state["search"]["index_status"] = "STALE"

    return "Search failure injected."


def inject_checkout_session_failure(env):

    env.state["checkout"]["session_status"] = "EXPIRED"

    return "Checkout session failure injected."


def inject_notification_failure(env):

    env.state["notifications"]["status"] = "FAILED"
    env.state["services"]["notification_service"] = "DEGRADED"

    return "Notification failure injected."


def inject_order_service_failure(env):

    env.state["services"]["order_service"] = "DEGRADED"

    return "Order service failure injected."


def inject_no_technical_fault(env):

    # Intentionally do nothing.
    # The environment remains healthy.

    return "No technical fault injected."