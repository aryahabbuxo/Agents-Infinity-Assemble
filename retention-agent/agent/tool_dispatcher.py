class ToolDispatcher:

    def __init__(self, tools):
        self.tools = tools

    def execute(self, tool_name, customer_id):

        if tool_name == "get_customer_profile":
            return self.tools.get_customer_profile(customer_id)

        elif tool_name == "check_cancellation_status":
            return self.tools.check_cancellation_status(customer_id)

        elif tool_name == "check_retention_offer":
            return self.tools.check_retention_offer(customer_id)

        elif tool_name == "apply_retention_offer":
            return self.tools.apply_retention_offer(customer_id)

        elif tool_name == "cancel_subscription":
            return self.tools.cancel_subscription(customer_id)

        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }