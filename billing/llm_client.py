"""
llm_client.py

Single wiring point for real LLM calls. Everything else (bidding.py,
agent.py) calls call_llm() and treats it as a black box — swap the body
here (Ollama / vLLM / hosted API) without touching callers.

Default implementation below targets a local Ollama server. Run:
    ollama pull llama3.2:3b
    ollama serve
before using this. Falls back to raising LLMUnavailableError, which
callers should catch and fall back to their rule-based logic.
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:7b"


class LLMUnavailableError(Exception):
    """Raised when the LLM backend can't be reached or errors out."""


def call_llm(prompt: str, model: str = DEFAULT_MODEL, timeout: float = 2.0) -> str:
    """
    Sends `prompt` to a local Ollama server and returns the raw text
    response. Raises LLMUnavailableError on any failure so callers can
    decide whether to retry or fall back to rule-based logic.
    """
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data.get("response", "").strip()
        if not text:
            raise LLMUnavailableError("LLM returned an empty response.")
        return text
    except requests.exceptions.RequestException as e:
        raise LLMUnavailableError(f"Could not reach LLM backend: {e}") from e
    except (KeyError, ValueError) as e:
        raise LLMUnavailableError(f"Malformed LLM response: {e}") from e


# ---- Example for a hosted API instead of Ollama (swap in if you prefer) ----
# import os
# from anthropic import Anthropic
# _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
#
# def call_llm(prompt: str, model: str = "claude-sonnet-4-6", timeout: float = 15.0) -> str:
#     try:
#         msg = _client.messages.create(
#             model=model,
#             max_tokens=200,
#             messages=[{"role": "user", "content": prompt}],
#         )
#         return msg.content[0].text.strip()
#     except Exception as e:
#         raise LLMUnavailableError(f"API call failed: {e}") from e