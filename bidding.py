"""
bidding.py

Implements section 6/7/8 of the master context:

  load_penalty   = min(current_load * 0.15, 0.6)     -- LOCKED, do not change
  urgency_weight = 1 + (urgency_score / 100) * 0.3    -- LOCKED, do not change
  final_bid      = raw_confidence * (1 - load_penalty) * urgency_weight  -- LOCKED

raw_confidence itself is each agent's own job. estimate_raw_confidence()
now tries a real LLM self-assessment first and falls back to the
keyword-based rule if the LLM is unavailable, so the demo never crashes.
"""

import re
from capability import BILLING_KEYWORDS
from llm_client import call_llm, LLMUnavailableError

CONFIDENCE_PROMPT = (
    "On a scale of 0 to 1, how confident are you — a billing specialist "
    "agent that only handles payments, refunds, invoices, charges and "
    "subscription billing — that you can resolve this customer support "
    "ticket:\n\n\"{ticket_text}\"\n\n"
    "Only output a single number between 0 and 1. No words, no explanation."
)


def _rule_based_confidence(ticket_text: str) -> float:
    """Keyword-based self-assessment, 0.0-1.0. Used as a fallback."""
    text = ticket_text.lower()
    score = 0.15  # small baseline so confidence is never exactly 0
    for kw, weight in BILLING_KEYWORDS.items():
        if kw in text:
            score += weight
    return min(score, 0.97)


def estimate_raw_confidence(ticket_text: str) -> float:
    """
    Tries a real LLM self-assessment first. Falls back to the rule-based
    keyword estimate if the LLM is unreachable or returns something we
    can't parse as a 0-1 float.
    """
    try:
        raw = call_llm(CONFIDENCE_PROMPT.format(ticket_text=ticket_text))
        match = re.search(r"(\d+(\.\d+)?)", raw)
        if not match:
            raise ValueError(f"No number found in LLM output: {raw!r}")
        value = float(match.group(1))
        if value > 1.0:  # model gave e.g. "85" meaning 0.85
            value = value / 100.0
        return max(0.0, min(value, 0.97))
    except (LLMUnavailableError, ValueError):
        return _rule_based_confidence(ticket_text)


def compute_final_bid(raw_confidence: float, current_load: int, urgency_score: int) -> dict:
    load_penalty = min(current_load * 0.15, 0.6)
    urgency_weight = 1 + (urgency_score / 100) * 0.3
    final_bid = raw_confidence * (1 - load_penalty) * urgency_weight

    return {
        "raw_confidence": round(raw_confidence, 3),
        "load_penalty": round(load_penalty, 3),
        "urgency_weight": round(urgency_weight, 3),
        "final_bid": round(final_bid, 3),
    }