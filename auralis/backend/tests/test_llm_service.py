import json
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from services.llm_service import (
    LLMServiceError,
    generate_response,
)


class LLMServiceTests(unittest.TestCase):
    def test_sends_transcript_emotion_and_confidence_to_ollama(self):
        ollama_response = Mock()
        ollama_response.__enter__ = Mock(
            return_value=Mock(
                read=Mock(
                    return_value=json.dumps(
                        {"message": {"content": "Let's take one step at a time."}}
                    ).encode("utf-8")
                )
            )
        )
        ollama_response.__exit__ = Mock(return_value=False)

        with patch(
            "services.llm_service.urlopen",
            return_value=ollama_response,
        ) as open_url:
            result = generate_response("I feel scared.", "fear", 0.84)

        request = open_url.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(result.text, "Let's take one step at a time.")
        self.assertGreaterEqual(result.latency_ms, 0)
        self.assertEqual(body["model"], "llama3.2:1b")
        self.assertFalse(body["stream"])
        self.assertIn(
            "crisis-negotiation training assistant",
            body["messages"][0]["content"],
        )
        self.assertIn("I feel scared.", body["messages"][1]["content"])
        self.assertIn("fear", body["messages"][1]["content"])
        self.assertIn("0.84", body["messages"][1]["content"])

    def test_reports_when_ollama_is_unavailable(self):
        with patch(
            "services.llm_service.urlopen",
            side_effect=URLError("connection refused"),
        ):
            with self.assertRaisesRegex(LLMServiceError, "Ollama server is not available"):
                generate_response("Hello.", "neutral", 0.5)

    def test_reports_how_to_install_a_missing_model(self):
        error_body = b'{"error":"model not found; pull the model first"}'
        model_error = HTTPError(
            "http://localhost:11434/api/chat",
            404,
            "Not Found",
            {},
            Mock(read=Mock(return_value=error_body)),
        )
        with patch("services.llm_service.urlopen", side_effect=model_error):
            with self.assertRaisesRegex(LLMServiceError, "ollama pull llama3.2:1b"):
                generate_response("Hello.", "neutral", 0.5)

    def test_reports_an_ollama_timeout(self):
        with patch(
            "services.llm_service.urlopen",
            side_effect=TimeoutError(),
        ):
            with self.assertRaisesRegex(LLMServiceError, "did not respond"):
                generate_response("Hello.", "neutral", 0.5)

    def test_rejects_empty_transcripts(self):
        with self.assertRaisesRegex(ValueError, "empty transcript"):
            generate_response("  ", "unknown", 0.0)


if __name__ == "__main__":
    unittest.main()
