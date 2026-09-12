import json
import re
import requests


OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.1"


EMOTION_PROMPT = """
You are the emotional-intelligence component of a customer Retention Agent.

Analyze the customer's message carefully.

Your job is to identify the customer's emotional state and retention-related
signals.

Look for emotions such as:
- anger
- frustration
- irritation
- helplessness
- disappointment
- anxiety
- betrayal
- sadness
- confusion
- urgency-related distress
- calmness

Do not invent emotions that are not supported by the customer's wording.

Emotion intensity must be a number from 0 to 1.

Also identify:
- frustration level from 0 to 1
- helplessness level from 0 to 1
- churn risk from 0 to 1
- explicit cancellation request: true or false
- retention signals expressed by the customer

IMPORTANT:
Do NOT generate an urgency score.
Urgency is supplied separately by the system.

Do NOT decide whether the Retention Agent wins the ticket.
Do NOT invent actions.

Customer ticket:
{ticket_text}

Return ONLY valid JSON in exactly this structure:

{{
    "primary_emotion": "string",
    "emotion_intensity": 0.0,
    "frustration_level": 0.0,
    "helplessness_level": 0.0,
    "churn_risk": 0.0,
    "explicit_cancellation_request": false,
    "retention_signals": []
}}
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


def _extract_json(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found.")
    return json.loads(match.group(0))


def _validate(result: dict) -> dict:

    required = [
        "primary_emotion",
        "emotion_intensity",
        "frustration_level",
        "helplessness_level",
        "churn_risk",
        "explicit_cancellation_request",
        "retention_signals",
    ]

    for key in required:
        if key not in result:
            raise ValueError(f"Missing emotion field: {key}")

    for key in [
        "emotion_intensity",
        "frustration_level",
        "helplessness_level",
        "churn_risk",
    ]:
        value = float(result[key])

        if not 0 <= value <= 1:
            raise ValueError(
                f"{key} must be between 0 and 1."
            )

        result[key] = round(value, 3)

    result["explicit_cancellation_request"] = bool(
        result["explicit_cancellation_request"]
    )

    if not isinstance(result["retention_signals"], list):
        raise ValueError("retention_signals must be a list.")

    return result


def analyze_emotion(ticket_text: str) -> dict:

    prompt = EMOTION_PROMPT.format(
        ticket_text=ticket_text
    )

    try:

        raw = _call_ollama(prompt)

        result = _extract_json(raw)

        return _validate(result)

    except (
        requests.exceptions.RequestException,
        json.JSONDecodeError,
        ValueError,
        KeyError,
        TypeError
    ):

        # Conservative fallback.
        return {
            "primary_emotion": "unknown",
            "emotion_intensity": 0.0,
            "frustration_level": 0.0,
            "helplessness_level": 0.0,
            "churn_risk": 0.0,
            "explicit_cancellation_request": False,
            "retention_signals": []
        }