from copy import deepcopy


class EcommerceEnvironment:

    def __init__(self):
        self.state = {
            "customer": {
                "customer_id": "C1001",
                "account_status": "ACTIVE",
                "session_status": "ACTIVE",
                "login_failures": 0
            },

            "orders": {
                "ORDER1001": {
                    "exists": True,
                    "visible": True,
                    "sync_status": "HEALTHY",
                    "status": "DELIVERED"
                },

                "ORDER1002": {
                    "exists": True,
                    "visible": True,
                    "sync_status": "HEALTHY",
                    "status": "ACTIVE"
                }
            },

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

    def get_state(self):
        return deepcopy(self.state)