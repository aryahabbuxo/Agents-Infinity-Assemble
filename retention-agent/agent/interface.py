class RetentionAgentInterface:

    AGENT_ID = "retention_agent"

    CAPABILITY_CARD = {
        "agent_id": "retention_agent",
        "display_name": "Retention Agent",

        "handles": [
            "customer dissatisfaction",
            "churn risk",
            "customer retention",
            "retention offers",
            "subscription cancellation",
            "customer loyalty"
        ],

        "does_not_handle": [
            "technical system problems",
            "dashboard / UI bugs",
            "login / authentication problems",
            "payments",
            "refunds",
            "invoices",
            "billing disputes"
        ],

        "best_suited_for": (
            "Tickets involving customer dissatisfaction, frustration, "
            "churn risk, subscription cancellation, customer loyalty, "
            "and opportunities to retain an at-risk customer."
        )
    }

    def get_capabilities(self):
        return self.CAPABILITY_CARD