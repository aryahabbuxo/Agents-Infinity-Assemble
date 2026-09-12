import requests

MAX_NEGOTIATION_ROUNDS = 3

AGENT_URL_MAP = {
    "technical_agent": "http://localhost:8001/negotiate",
    "retention_agent": "http://localhost:8002/negotiate",
    "billing_agent": "http://localhost:8000/negotiate",
}

AGENT_COLLABORATE_MAP = {
    "technical_agent": "http://localhost:8001/collaborate",
    "retention_agent": "http://localhost:8002/collaborate",
    "billing_agent": "http://localhost:8000/collaborate",
}


def make_propose(sender, receiver, my_subtask, requested_subtask, rationale):
    return {
        "sender": sender,
        "receiver": receiver,
        "action": "PROPOSE",
        "my_assigned_subtask": my_subtask,
        "your_requested_subtask": requested_subtask,
        "rationale": rationale,
    }


def make_counter(sender, receiver, modified_scope, rationale):
    return {
        "sender": sender,
        "receiver": receiver,
        "action": "COUNTER",
        "modified_scope": modified_scope,
        "rationale": rationale,
    }


def make_accept(sender, receiver=None):
    res = {"sender": sender, "action": "ACCEPT"}
    if receiver:
        res["receiver"] = receiver
    return res


def make_reject(sender, receiver=None, rationale=""):
    res = {"sender": sender, "action": "REJECT", "rationale": rationale}
    if receiver:
        res["receiver"] = receiver
    return res


class MockTechnicalAgent:
    """STUB — simulates how a peer agent responds to a PROPOSE when offline."""

    agent_id = "technical_agent"

    def respond_to_proposal(self, proposal: dict) -> dict:
        sender = proposal.get("sender", "billing_agent")
        return make_accept(self.agent_id, receiver=sender)


class RemotePeerAgent:
    """Calls any peer agent's HTTP negotiation service."""

    def __init__(self, target_agent_id: str, url: str = None, timeout: float = 5.0):
        self.agent_id = target_agent_id
        self.url = url or AGENT_URL_MAP.get(target_agent_id, "http://localhost:8001/negotiate")
        self.collaborate_url = AGENT_COLLABORATE_MAP.get(
            target_agent_id, self.url.rsplit("/negotiate", 1)[0] + "/collaborate"
        )
        self.timeout = timeout
        self._fallback = MockTechnicalAgent()

    def respond_to_proposal(self, proposal: dict) -> dict:
        try:
            resp = requests.post(self.url, json=proposal, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            # Normalize action field if service returned message_type
            if "action" not in data and "message_type" in data:
                data["action"] = data["message_type"]
            return data
        except requests.exceptions.RequestException:
            return self._fallback.respond_to_proposal(proposal)


def run_negotiation(proposal: dict, counterpart_agent) -> list[dict]:
    """Runs up to MAX_NEGOTIATION_ROUNDS turns between the initial proposal

    and a counterpart agent object exposing `.respond_to_proposal(msg)`.

    Returns the full transcript.

    """
    transcript = [proposal]
    current = proposal
    for _ in range(MAX_NEGOTIATION_ROUNDS):
        response = counterpart_agent.respond_to_proposal(current)
        if not response or not isinstance(response, dict):
            response = {
                "sender": getattr(counterpart_agent, "agent_id", "peer_agent"),
                "action": "REJECT",
                "message_type": "REJECT",
                "rationale": "No response received.",
            }
        transcript.append(response)
        action = response.get("action") or response.get("message_type") or "REJECT"
        if action in ("ACCEPT", "REJECT"):
            break
        current = response
    return transcript