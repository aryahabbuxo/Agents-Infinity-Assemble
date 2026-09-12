import re


AGENT_NAME = "technical_agent"

TECHNICAL_CAPABILITY_CARD = {
    "agent_id": "technical_agent",
    "display_name": "Technical Support Agent",

    "handles": [
        "account access",
        "authentication",
        "session problems",
        "dashboard problems",
        "order visibility",
        "cart synchronization",
        "search problems",
        "checkout session problems",
        "notification problems",
        "technical service health"
    ],

    "does_not_handle": [
        "payments",
        "refunds",
        "invoices",
        "billing",
        "subscription charges",
        "retention offers"
    ],

    "best_suited_for": (
        "Technical issues involving accounts, sessions, orders, "
        "dashboard, cart, search, checkout, notifications, "
        "and technical service health."
    )
}

TECHNICAL_KEYWORDS = {
    "login": 0.25,
    "log in": 0.25,
    "sign in": 0.25,
    "signin": 0.25,
    "password": 0.20,
    "account": 0.15,
    "locked": 0.30,
    "session": 0.25,
    "expired": 0.20,
    "dashboard": 0.25,
    "order disappeared": 0.35,
    "order missing": 0.30,
    "order not visible": 0.30,
    "orders page": 0.20,
    "order": 0.10,
    "cart": 0.25,
    "search": 0.25,
    "checkout": 0.25,
    "notification": 0.20,
    "notifications": 0.20,
    "page not loading": 0.25,
    "website error": 0.20,
    "error": 0.15,
    "not working": 0.10,
    "service unavailable": 0.30,
    "server": 0.20
}


def estimate_raw_confidence(ticket):
    """
    Estimate how strongly the ticket belongs to
    Technical Support.

    This is the Technical Agent's own assessment.
    """

    text = ticket.lower()

    confidence = 0.10
    matched_keywords = []

    for keyword, weight in TECHNICAL_KEYWORDS.items():

        if keyword in text:
            confidence += weight
            matched_keywords.append(keyword)

    confidence = min(confidence, 0.97)

    return {
        "raw_confidence": round(confidence, 4),
        "matched_keywords": matched_keywords
    }


def compute_final_bid(
    raw_confidence,
    current_load=0,
    urgency_score=0
):
    """
    Convert raw confidence into the final market bid.

    Load reduces the bid.
    Urgency increases the bid.
    """

    load_penalty = min(
        current_load * 0.15,
        0.60
    )

    urgency_weight = 1 + (
        (urgency_score / 100) * 0.30
    )

    final_bid = (
        raw_confidence
        * (1 - load_penalty)
        * urgency_weight
    )

    return {
        "raw_confidence": round(raw_confidence, 4),
        "load_penalty": round(load_penalty, 4),
        "urgency_weight": round(urgency_weight, 4),
        "final_bid": round(final_bid, 4)
    }


def submit_bid(
    ticket,
    current_load=0,
    urgency_score=0,
    ticket_id="T000",
    instance_index=None
):
    """
    Public bidding function used by service.py and TechnicalAgent.
    """
    text = ticket["text"] if isinstance(ticket, dict) else str(ticket)
    t_id = ticket.get("ticket_id", ticket_id) if isinstance(ticket, dict) else ticket_id

    confidence_result = estimate_raw_confidence(text)
    raw_confidence = confidence_result["raw_confidence"]

    if instance_index is not None and hasattr(instance_index, "get_adjusted_confidence"):
        raw_confidence = instance_index.get_adjusted_confidence(raw_confidence, text)

    bid_result = compute_final_bid(
        raw_confidence=raw_confidence,
        current_load=current_load,
        urgency_score=urgency_score
    )

    return {
        "agent_id": AGENT_NAME,
        "ticket_id": t_id,
        "raw_confidence": raw_confidence,
        "load_penalty": bid_result["load_penalty"],
        "urgency_weight": bid_result["urgency_weight"],
        "final_bid": bid_result["final_bid"],
        "matched_keywords": confidence_result["matched_keywords"],
    }


def share_capability():
    return TECHNICAL_CAPABILITY_CARD



def make_propose(
    requested_subtask,
    rationale,
    receiver="billing_agent"
):
    """
    Create a PROPOSE message from Technical Agent.
    """

    return {
        "type": "PROPOSE",
        "sender": AGENT_NAME,
        "receiver": receiver,
        "my_subtask": (
            "Investigate and resolve technical issues "
            "using the technical sandbox."
        ),
        "requested_subtask": requested_subtask,
        "rationale": rationale
    }


def make_counter(
    modified_scope,
    rationale,
    receiver="billing_agent"
):
    """
    Create a COUNTER message from Technical Agent.
    """

    return {
        "type": "COUNTER",
        "sender": AGENT_NAME,
        "receiver": receiver,
        "modified_scope": modified_scope,
        "rationale": rationale
    }


def make_accept(
    receiver="billing_agent"
):
    """
    Create an ACCEPT message.
    """

    return {
        "type": "ACCEPT",
        "sender": AGENT_NAME,
        "receiver": receiver
    }


def make_reject(
    rationale,
    receiver="billing_agent"
):
    """
    Create a REJECT message.
    """

    return {
        "type": "REJECT",
        "sender": AGENT_NAME,
        "receiver": receiver,
        "rationale": rationale
    }