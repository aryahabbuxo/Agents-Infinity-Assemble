import json
import requests


RETENTION_URL = "http://127.0.0.1:8001"
BILLING_URL = "http://127.0.0.1:8000"


def print_json(title, data):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print(json.dumps(data, indent=2))


def check_connection():

    retention = requests.get(
        f"{RETENTION_URL}/health",
        timeout=5,
    )

    billing = requests.get(
        f"{BILLING_URL}/capability",
        timeout=5,
    )

    print_json(
        "RETENTION AGENT",
        retention.json(),
    )

    print_json(
        "BILLING CAPABILITY",
        billing.json(),
    )


def test_billing_to_retention_negotiation():

    proposal = {
        "sender": "billing_agent",
        "receiver": "retention_agent",
        "action": "PROPOSE",

        "my_assigned_subtask": (
            "Verify and resolve the billing side "
            "of the customer's refund issue."
        ),

        "your_requested_subtask": (
            "Assess customer frustration and "
            "cancellation risk and perform appropriate "
            "retention actions."
        ),

        "rationale": (
            "The billing transaction is being handled "
            "by Billing, but the customer is highly "
            "dissatisfied and considering cancellation."
        ),
    }

    response = requests.post(
        f"{RETENTION_URL}/negotiate",
        json=proposal,
        timeout=10,
    )

    response.raise_for_status()

    print_json(
        "BILLING → RETENTION : PROPOSE",
        proposal,
    )

    print_json(
        "RETENTION → BILLING : RESPONSE",
        response.json(),
    )


def test_retention_to_billing_negotiation():

    proposal = {
        "sender": "retention_agent",
        "receiver": "billing_agent",
        "action": "PROPOSE",

        "my_assigned_subtask": (
            "Handle customer dissatisfaction and "
            "retention risk."
        ),

        "your_requested_subtask": (
            "Verify the customer's refund and "
            "billing transaction."
        ),

        "rationale": (
            "The customer is angry about a missing "
            "refund and is considering cancellation."
        ),
    }

    response = requests.post(
        f"{BILLING_URL}/negotiate",
        json=proposal,
        timeout=10,
    )

    response.raise_for_status()

    print_json(
        "RETENTION → BILLING : PROPOSE",
        proposal,
    )

    print_json(
        "BILLING → RETENTION : RESPONSE",
        response.json(),
    )


if __name__ == "__main__":

    print()
    print("==============================================")
    print("  BILLING ↔ RETENTION INTEGRATION TEST")
    print("==============================================")

    check_connection()

    test_billing_to_retention_negotiation()

    test_retention_to_billing_negotiation()

    print()
    print("==============================================")
    print("  COMMUNICATION TEST COMPLETE")
    print("==============================================")