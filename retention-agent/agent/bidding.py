import re
import requests


OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.1"


CONFIDENCE_PROMPT = """
You are the Retention Agent in an autonomous customer-support market.

Your specialization is:
- customer dissatisfaction
- customer retention
- churn risk
- subscription cancellation
- customer loyalty

Determine how confident you are that the Retention Agent can meaningfully
handle or resolve this ticket using its available capabilities.

IMPORTANT:
- Do NOT consider urgency when calculating confidence.
- Urgency is supplied separately by the market/system.
- A ticket can contain anger or frustration but still be outside the
  Retention Agent's actual capabilities.
- Do not claim capability to perform refunds, payments, technical fixes,
  invoices, or other billing/technical actions.

Customer ticket:
{ticket_text}

Customer emotional assessment:
{emotion_json}

Return ONLY a single number between 0 and 1.
Do not include words or explanation.
"""


def _call_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        },
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]


def _rule_based_confidence(ticket_text: str) -> float:
    """
    Offline fallback.

    This is intentionally conservative. Emotional language by itself
    should not make the Retention Agent claim high capability.
    """

    text = ticket_text.lower()

    retention_keywords = {
        "cancel": 0.30,
        "cancellation": 0.30,
        "leaving": 0.25,
        "leave": 0.25,
        "churn": 0.25,
        "retention": 0.30,
        "unhappy": 0.20,
        "dissatisfied": 0.20,
        "frustrated": 0.20,
        "frustrating": 0.20,
        "angry": 0.15,
        "terrible service": 0.20,
        "loyal": 0.15,
        "customer service": 0.15,
    }

    out_of_scope_keywords = {
        "refund": 0.25,
        "payment": 0.25,
        "invoice": 0.25,
        "charged": 0.25,
        "billing": 0.25,
        "dashboard bug": 0.30,
        "login": 0.30,
        "authentication": 0.30,
        "api": 0.30,
    }

    score = 0.10

    for keyword, weight in retention_keywords.items():
        if keyword in text:
            score += weight

    for keyword, penalty in out_of_scope_keywords.items():
        if keyword in text:
            score -= penalty

    return max(0.0, min(score, 0.97))


def estimate_raw_confidence(
    ticket_text: str,
    emotion_analysis: dict | None = None
) -> float:

    emotion_analysis = emotion_analysis or {}

    prompt = CONFIDENCE_PROMPT.format(
        ticket_text=ticket_text,
        emotion_json=emotion_analysis
    )

    try:
        raw = _call_ollama(prompt)

        match = re.search(r"(\d+(?:\.\d+)?)", raw)

        if not match:
            raise ValueError("No confidence value found.")

        value = float(match.group(1))

        if value > 1:
            value = value / 100

        return max(0.0, min(value, 0.97))

    except (
        requests.exceptions.RequestException,
        KeyError,
        ValueError,
        TypeError
    ):
        return _rule_based_confidence(ticket_text)


def compute_final_bid(
    raw_confidence: float,
    current_load: int,
    urgency_score: int
) -> dict:

    load_penalty = min(current_load * 0.15, 0.6)

    urgency_weight = 1 + (urgency_score / 100) * 0.3

    final_bid = (
        raw_confidence
        * (1 - load_penalty)
        * urgency_weight
    )

    return {
        "raw_confidence": round(raw_confidence, 3),
        "load_penalty": round(load_penalty, 3),
        "urgency_weight": round(urgency_weight, 3),
        "final_bid": round(final_bid, 3),
    }