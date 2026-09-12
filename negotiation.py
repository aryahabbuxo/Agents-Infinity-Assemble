"""
negotiation.py

Section 10 of the master context: Speech-Act style structured messages,
bounded to N=3 negotiation rounds (LOCKED — do not change MAX_NEGOTIATION_ROUNDS).

MockTechnicalAgent is kept as a local stand-in for tests / offline demos.
RemoteTechnicalAgent calls the real Technical Agent's HTTP service once it
exists — point TECHNICAL_AGENT_URL at your teammate's running service.

The exact universal schema is explicitly NOT finalized yet (section 26),
so this stays dict-based and easy to reshape.
"""

import requests

MAX_NEGOTIATION_ROUNDS = 3
TECHNICAL_AGENT_URL = "http://localhost:8001/negotiate"  # your teammate's service


def make_propose(sender, receiver, my_subtask, requested_subtask, rationale):
    return {
        "sender": sender,
        "receiver": receiver,
        "action": "PROPOSE",
        "my_assigned_subtask": my_subtask,
        "your_requested_subtask": requested_subtask,
        "rationale": rationale,
    }


def make_counter(sender, modified_scope, rationale):
    return {"sender": sender, "action": "COUNTER", "modified_scope": modified_scope, "rationale": rationale}


def make_accept(sender):
    return {"sender": sender, "action": "ACCEPT"}


def make_reject(sender, rationale):
    return {"sender": sender, "action": "REJECT", "rationale": rationale}


class MockTechnicalAgent:
    """
    STUB — simulates how the Technical Agent might respond to a PROPOSE.
    Keep this around for offline tests even after RemoteTechnicalAgent
    exists; it's a fast, dependency-free way to test negotiation logic.
    """
    agent_id = "technical_agent"

    def respond_to_proposal(self, proposal: dict) -> dict:
        return make_accept(self.agent_id)


class RemoteTechnicalAgent:
    """
    Calls the REAL Technical Agent's HTTP service. Falls back to
    MockTechnicalAgent's behaviour if the service is unreachable, so a
    teammate's downtime never breaks your demo.
    """
    agent_id = "technical_agent"

    def __init__(self, url: str = TECHNICAL_AGENT_URL, timeout: float = 5.0):
        self.url = url
        self.timeout = timeout
        self._fallback = MockTechnicalAgent()

    def respond_to_proposal(self, proposal: dict) -> dict:
        try:
            resp = requests.post(self.url, json=proposal, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException:
            return self._fallback.respond_to_proposal(proposal)


def run_negotiation(billing_proposal: dict, counterpart_agent) -> list[dict]:
    """
    Runs up to MAX_NEGOTIATION_ROUNDS turns between the billing proposal
    and a counterpart agent object exposing `.respond_to_proposal(msg)`.
    Returns the full transcript.
    """
    transcript = [billing_proposal]
    current = billing_proposal
    for _ in range(MAX_NEGOTIATION_ROUNDS):
        response = counterpart_agent.respond_to_proposal(current)
        transcript.append(response)
        if response["action"] in ("ACCEPT", "REJECT"):
            break
        current = response  # a COUNTER becomes the new "current" to react to
    return transcript