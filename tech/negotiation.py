import requests


MAX_NEGOTIATION_ROUNDS = 3


def make_propose(
    sender,
    receiver,
    my_subtask,
    requested_subtask,
    rationale
):
    return {
        "message_type": "PROPOSE",
        "sender": sender,
        "receiver": receiver,
        "my_subtask": my_subtask,
        "requested_subtask": requested_subtask,
        "rationale": rationale
    }


def make_counter(
    sender,
    receiver,
    modified_scope,
    rationale
):
    return {
        "message_type": "COUNTER",
        "sender": sender,
        "receiver": receiver,
        "modified_scope": modified_scope,
        "rationale": rationale
    }


def make_accept(
    sender,
    receiver
):
    return {
        "message_type": "ACCEPT",
        "sender": sender,
        "receiver": receiver
    }


def make_reject(
    sender,
    receiver,
    rationale
):
    return {
        "message_type": "REJECT",
        "sender": sender,
        "receiver": receiver,
        "rationale": rationale
    }


class TechnicalNegotiationHandler:

    def __init__(self):
        self.technical_terms = [
            "account",
            "authentication",
            "session",
            "dashboard",
            "order",
            "cart",
            "search",
            "checkout",
            "notification",
            "service",
            "technical",
            "website"
        ]

    def handle_proposal(self, proposal):
        """
        Decide whether Technical Agent can handle
        the requested collaboration.
        """

        requested_subtask = proposal.get(
            "requested_subtask",
            ""
        ).lower()

        is_technical = any(
            term in requested_subtask
            for term in self.technical_terms
        )

        if is_technical:
            return make_accept(
                sender="technical_agent",
                receiver=proposal.get(
                    "sender",
                    "billing_agent"
                )
            )

        return make_reject(
            sender="technical_agent",
            receiver=proposal.get(
                "sender",
                "billing_agent"
            ),
            rationale=(
                "The requested task is outside "
                "Technical Support capabilities."
            )
        )

    def handle_counter(self, counter):
        """
        Technical Agent accepts a counter only when
        the modified scope remains technical.
        """

        modified_scope = counter.get(
            "modified_scope",
            ""
        ).lower()

        is_technical = any(
            term in modified_scope
            for term in self.technical_terms
        )

        if is_technical:
            return make_accept(
                sender="technical_agent",
                receiver=counter.get(
                    "sender",
                    "billing_agent"
                )
            )

        return make_reject(
            sender="technical_agent",
            receiver=counter.get(
                "sender",
                "billing_agent"
            ),
            rationale=(
                "The modified scope is outside "
                "Technical Support capabilities."
            )
        )


def send_proposal_to_billing(
    proposal,
    billing_service_url="http://127.0.0.1:8001"
):
    """
    Send a proposal from Technical Agent to Billing Agent.

    Billing service must expose /negotiate.
    """

    try:
        response = requests.post(
            f"{billing_service_url}/negotiate",
            json=proposal,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as error:
        return {
            "message_type": "REJECT",
            "sender": "billing_agent",
            "receiver": "technical_agent",
            "rationale": (
                "Billing Agent could not be reached."
            ),
            "error": str(error)
        }


def run_technical_negotiation(
    proposal,
    billing_service_url="http://127.0.0.1:8001"
):
    """
    Run a small negotiation loop.

    The Technical Agent starts with PROPOSE.
    Billing may respond with ACCEPT, REJECT, or COUNTER.
    """

    transcript = [
        proposal
    ]

    current_message = proposal

    for _ in range(MAX_NEGOTIATION_ROUNDS):

        response = send_proposal_to_billing(
            current_message,
            billing_service_url
        )

        transcript.append(
            response
        )

        response_type = response.get(
            "message_type"
        )

        if response_type in {
            "ACCEPT",
            "REJECT"
        }:
            return {
                "status": response_type.lower(),
                "transcript": transcript,
                "final_message": response
            }

        if response_type == "COUNTER":

            modified_scope = response.get(
                "modified_scope",
                ""
            )

            current_message = {
                "message_type": "PROPOSE",
                "sender": "technical_agent",
                "receiver": "billing_agent",
                "my_subtask": proposal.get(
                    "my_subtask",
                    ""
                ),
                "requested_subtask": modified_scope,
                "rationale": (
                    "Technical Agent responds to "
                    "Billing Agent's counter-proposal."
                )
            }

            transcript.append(
                current_message
            )

    return {
        "status": "timeout",
        "transcript": transcript,
        "final_message": {
            "message_type": "REJECT",
            "sender": "technical_agent",
            "receiver": "billing_agent",
            "rationale": (
                "Negotiation exceeded the maximum "
                "number of rounds."
            )
        }
    }
