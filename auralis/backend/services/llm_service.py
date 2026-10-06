import json
import logging
import os
import socket
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_TIMEOUT = os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")

SYSTEM_PROMPT = """You are Auralis, a calm crisis-negotiation training assistant.
Your goal is to produce a concise, professional, de-escalating response.
Acknowledge the speaker's emotional state without treating acoustic emotion as
certain. Remain respectful, avoid escalating language, and do not claim to be a
real emergency service. Respond naturally and output only the words to say to
the speaker."""


class LLMServiceError(RuntimeError):
    """Raised when the local Ollama service cannot generate a response."""


@dataclass(frozen=True)
class LLMResponse:
    text: str
    latency_ms: float


def _timeout_seconds():
    try:
        timeout = float(OLLAMA_TIMEOUT)
    except ValueError as error:
        raise LLMServiceError(
            "OLLAMA_TIMEOUT_SECONDS must be a positive number."
        ) from error

    if timeout <= 0:
        raise LLMServiceError("OLLAMA_TIMEOUT_SECONDS must be a positive number.")
    return timeout


def _context_prompt(transcript, emotion, confidence):
    return (
        "Speaker transcript:\n"
        f"{transcript.strip()}\n\n"
        "Detected acoustic emotion:\n"
        f"{emotion}\n\n"
        "Emotion confidence:\n"
        f"{confidence:.2f}\n\n"
        "Respond naturally to the speaker. Acknowledge the emotional context, "
        "but do not present the detected emotion as certain."
    )


def generate_response(transcript, emotion, confidence):
    transcript = transcript.strip()
    if not transcript:
        raise ValueError("Cannot generate an LLM response for an empty transcript.")
    if not OLLAMA_MODEL.strip():
        raise LLMServiceError("OLLAMA_MODEL must name an installed Ollama model.")

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _context_prompt(transcript, emotion, confidence),
            },
        ],
        "options": {"temperature": 0.4, "num_predict": 128},
    }
    request = Request(
        f"{OLLAMA_HOST}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started_at = time.perf_counter()
    logger.info("Sending context to Ollama; model: %s", OLLAMA_MODEL)

    try:
        with urlopen(request, timeout=_timeout_seconds()) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        if error.code == 404 and "model" in error_body.lower():
            raise LLMServiceError(
                f"Ollama model '{OLLAMA_MODEL}' is not installed. "
                f"Run `ollama pull {OLLAMA_MODEL}` and try again."
            ) from error
        raise LLMServiceError(
            f"Ollama request failed with HTTP {error.code}."
        ) from error
    except (URLError, ConnectionError) as error:
        raise LLMServiceError(
            "Ollama server is not available. Please start Ollama and try again."
        ) from error
    except (TimeoutError, socket.timeout) as error:
        raise LLMServiceError(
            f"Ollama did not respond within {_timeout_seconds():g} seconds."
        ) from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise LLMServiceError("Ollama returned an invalid response.") from error

    message = result.get("message")
    response_text = message.get("content", "").strip() if isinstance(message, dict) else ""
    if not response_text:
        raise LLMServiceError("Ollama returned an empty response.")

    latency_ms = (time.perf_counter() - started_at) * 1000
    logger.info("LLM response: %s", response_text)
    logger.info("LLM latency: %.0f ms", latency_ms)
    return LLMResponse(text=response_text, latency_ms=latency_ms)
