import json
import random
import requests

from environment import EcommerceEnvironment
from faultinject import inject_fault


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"


# These are the only faults that can exist in our simulator.
VALID_FAULTS = [
    "ORDER_SYNC_FAILURE",
    "ACCOUNT_LOCKED",
    "SESSION_EXPIRED",
    "DASHBOARD_FAILURE",
    "CART_SYNC_FAILURE",
    "SEARCH_FAILURE",
    "CHECKOUT_SESSION_FAILURE",
    "NOTIFICATION_FAILURE",
    "ORDER_SERVICE_FAILURE",
    "NO_TECHNICAL_FAULT"
]


SYSTEM_PROMPT = """
You are the hidden fault generator for a simulated e-commerce
technical support environment.

You receive a customer's support ticket.

Your job is NOT to solve the ticket.

Your job is to determine what hidden backend problem could
plausibly explain what the customer is experiencing.

The customer does NOT explicitly tell you the underlying fault.

You must return ONLY valid JSON.

Determine:

1. issue_family
2. technical_relevance
3. plausible_faults

technical_relevance:
- true if a technical/backend problem could plausibly explain
  the customer's complaint.
- false if there is no plausible technical problem.

If technical_relevance is false, plausible_faults MUST contain
only:

NO_TECHNICAL_FAULT

If technical_relevance is true, plausible_faults may contain
ONLY these fault IDs:

ORDER_SYNC_FAILURE
ACCOUNT_LOCKED
SESSION_EXPIRED
DASHBOARD_FAILURE
CART_SYNC_FAILURE
SEARCH_FAILURE
CHECKOUT_SESSION_FAILURE
NOTIFICATION_FAILURE
ORDER_SERVICE_FAILURE
NO_TECHNICAL_FAULT

Do NOT invent new fault IDs.

Only include faults that could realistically explain the ticket.

For ambiguous tickets, do not immediately select only the
single most obvious explanation.

Consider multiple different hidden backend causes that could
produce the same customer experience.

When multiple causes are genuinely plausible, return 2-4
plausible faults.

The plausible faults should represent different possible
underlying states, not merely different names for the same
problem.

Do not include a fault just to increase the number of options.
Every returned fault must be realistically capable of causing
the customer's complaint.

Remember:
The ticket describes the customer's EXPERIENCE.
It does not reveal the actual hidden backend state.

Return exactly:

{
    "issue_family": "string",
    "technical_relevance": true,
    "plausible_faults": ["FAULT_ID"]
}
"""


def ask_qwen(ticket):
    """
    Ask Qwen to analyze the ticket and generate
    a set of plausible hidden faults.
    """

    payload = {
        "model": OLLAMA_MODEL,

        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"Customer ticket:\n{ticket}"
            }
        ],

        "stream": False,

        # Ask Ollama to return JSON.
        "format": "json",

        "options": {
            "temperature": 0.2
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    content = data["message"]["content"]

    return json.loads(content)


def validate_result(result):
    """
    Validate Qwen's response before allowing it
    to influence the simulator.
    """

    issue_family = result.get(
        "issue_family",
        "UNKNOWN"
    )

    technical_relevance = result.get(
        "technical_relevance",
        True
    )

    plausible_faults = result.get(
        "plausible_faults",
        []
    )

    # Make sure plausible_faults is actually a list.
    if not isinstance(plausible_faults, list):
        plausible_faults = []

    # Keep only faults that our simulator actually supports.
    plausible_faults = [
        fault
        for fault in plausible_faults
        if fault in VALID_FAULTS
    ]

    # If Qwen says this isn't technical,
    # force the no-fault state.
    if technical_relevance is False:

        return {
            "issue_family": issue_family,
            "technical_relevance": False,
            "plausible_faults": [
                "NO_TECHNICAL_FAULT"
            ]
        }

    # If Qwen returned nothing usable,
    # safely fall back to no technical fault.
    if not plausible_faults:

        plausible_faults = [
            "NO_TECHNICAL_FAULT"
        ]

    return {
        "issue_family": issue_family,
        "technical_relevance": True,
        "plausible_faults": plausible_faults
    }


def generate_fault(ticket, environment):
    """
    Main FaultGen pipeline.

    1. Qwen analyzes the ticket.
    2. Plausible faults are extracted.
    3. Python randomly selects one.
    4. The selected fault is injected into the environment.

    The selected fault is simulator-side information and
    MUST NOT be passed to the Technical Agent.
    """

    try:

        result = ask_qwen(ticket)

        result = validate_result(result)

    except Exception as e:

        print(f"[FaultGen] Error communicating with Ollama: {e}")

        result = {
            "issue_family": "UNKNOWN",
            "technical_relevance": True,
            "plausible_faults": [
                "NO_TECHNICAL_FAULT"
            ]
        }

    plausible_faults = result["plausible_faults"]

    # Randomness happens AFTER Qwen determines
    # what is plausible.
    selected_fault = random.choice(
        plausible_faults
    )

    target = None

    if selected_fault in {
        "ORDER_SYNC_FAILURE"
    }:
        target = random.choice(
            list(environment.state["orders"].keys())
        )

    # Actually create that hidden state
    # inside the simulated environment.
    injection_result = inject_fault(
        environment,
        selected_fault,
        target
    )

    return {
        "issue_family": result["issue_family"],

        "technical_relevance":
            result["technical_relevance"],

        "plausible_faults":
            plausible_faults,

        # ---------------------------------------------
        # HIDDEN SIMULATOR INFORMATION
        # ---------------------------------------------
        #
        # The demo/simulator can see this.
        # The Technical Agent must NOT see this.
        #
        "selected_fault": selected_fault,

        "target": target,

        "injection_result": injection_result
    }


if __name__ == "__main__":

    # Temporary direct run so we can see FaultGen working.
    # This is NOT the Technical Agent yet.

    ticket = (
        "my order was showing yesterday but now "
        "it has completely disappeared from my orders page"
    )

    environment = EcommerceEnvironment()

    result = generate_fault(
        ticket,
        environment
    )

    print("\n--- FaultGen Result ---")
    print(json.dumps(result, indent=4))

    print("\n--- Hidden Environment State ---")
    print(json.dumps(
        environment.get_state(),
        indent=4
    ))