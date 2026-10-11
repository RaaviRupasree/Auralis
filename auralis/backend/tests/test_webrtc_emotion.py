import asyncio
import unittest
from unittest.mock import patch

import numpy as np

from services import webrtc_service
from services.emotion_service import EmotionPrediction
from services.llm_service import LLMResponse, LLMServiceError
from utils.latency import start_timer


class WebRTCEmotionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session_id = "emotion-test-session"
        webrtc_service.transcriptions[self.session_id] = ""
        webrtc_service.transcription_statuses[self.session_id] = "processing"
        webrtc_service.segment_results[self.session_id] = [
            {
                "transcript": "",
                "transcript_status": "processing",
                "emotion": None,
                "emotion_status": "processing",
                "response": "",
                "response_status": "processing",
                "response_error": None,
                "llm_latency_ms": None,
            }
        ]
        webrtc_service.capture_statuses[self.session_id] = "listening"
        webrtc_service.pending_transcriptions[self.session_id] = 1
        webrtc_service.transcription_lock = asyncio.Lock()

    async def asyncTearDown(self):
        webrtc_service.transcriptions.pop(self.session_id, None)
        webrtc_service.transcription_statuses.pop(self.session_id, None)
        webrtc_service.segment_results.pop(self.session_id, None)
        webrtc_service.capture_statuses.pop(self.session_id, None)
        webrtc_service.pending_transcriptions.pop(self.session_id, None)

    async def test_keeps_transcription_and_emotion_paired_on_segment(self):
        with (
            patch(
                "services.webrtc_service.transcribe_samples",
                return_value="I need help immediately.",
            ),
            patch(
                "services.webrtc_service.classify_emotion",
                return_value=EmotionPrediction("angry", 0.82),
            ),
            patch(
                "services.webrtc_service.generate_response",
                return_value=LLMResponse("I hear your frustration.", 345.6),
            ) as generate_response,
        ):
            await webrtc_service._analyze_segment(
                self.session_id,
                0,
                np.ones(16000, dtype=np.float32),
                start_timer(),
            )

        result = webrtc_service.segment_results[self.session_id][0]
        self.assertEqual(result["transcript"], "I need help immediately.")
        self.assertEqual(
            result["emotion"],
            {"label": "angry", "confidence": 0.82},
        )
        self.assertEqual(result["transcript_status"], "ready")
        self.assertEqual(result["emotion_status"], "ready")
        self.assertEqual(result["response"], "I hear your frustration.")
        self.assertEqual(result["response_status"], "ready")
        self.assertEqual(result["llm_latency_ms"], 345.6)
        generate_response.assert_called_once_with(
            "I need help immediately.",
            "angry",
            0.82,
        )
        self.assertEqual(
            webrtc_service.transcriptions[self.session_id],
            "I need help immediately.",
        )
        self.assertEqual(
            webrtc_service.transcription_statuses[self.session_id],
            "listening",
        )
        self.assertNotIn(self.session_id, webrtc_service.pending_transcriptions)

    async def test_emotion_failure_does_not_discard_transcript(self):
        with (
            patch(
                "services.webrtc_service.transcribe_samples",
                return_value="Keep the recognized words.",
            ),
            patch(
                "services.webrtc_service.classify_emotion",
                side_effect=RuntimeError("model unavailable"),
            ),
            patch(
                "services.webrtc_service.generate_response",
                return_value=LLMResponse("Let's take this slowly.", 210.0),
            ),
        ):
            await webrtc_service._analyze_segment(
                self.session_id,
                0,
                np.ones(16000, dtype=np.float32),
                start_timer(),
            )

        result = webrtc_service.segment_results[self.session_id][0]
        self.assertEqual(result["transcript"], "Keep the recognized words.")
        self.assertEqual(result["transcript_status"], "ready")
        self.assertEqual(result["emotion_status"], "error")
        self.assertIsNone(result["emotion"])
        self.assertEqual(result["response_status"], "ready")
        self.assertEqual(
            result["response"],
            "Let's take this slowly.",
        )
        self.assertEqual(
            webrtc_service.transcription_statuses[self.session_id],
            "listening",
        )

    async def test_llm_failure_does_not_crash_or_discard_segment_results(self):
        with (
            patch(
                "services.webrtc_service.transcribe_samples",
                return_value="I feel frightened.",
            ),
            patch(
                "services.webrtc_service.classify_emotion",
                return_value=EmotionPrediction("fear", 0.67),
            ),
            patch(
                "services.webrtc_service.generate_response",
                side_effect=LLMServiceError(
                    "Ollama server is not available. Please start Ollama and try again."
                ),
            ),
        ):
            await webrtc_service._analyze_segment(
                self.session_id,
                0,
                np.ones(16000, dtype=np.float32),
                start_timer(),
            )

        result = webrtc_service.segment_results[self.session_id][0]
        self.assertEqual(result["transcript"], "I feel frightened.")
        self.assertEqual(result["emotion"]["label"], "fear")
        self.assertEqual(result["response_status"], "error")
        self.assertIn("start Ollama", result["response_error"])
        self.assertEqual(
            webrtc_service.transcription_statuses[self.session_id],
            "listening",
        )

    async def test_empty_transcript_skips_llm_request(self):
        with (
            patch("services.webrtc_service.transcribe_samples", return_value=""),
            patch(
                "services.webrtc_service.classify_emotion",
                return_value=EmotionPrediction("neutral", 0.51),
            ),
            patch("services.webrtc_service.generate_response") as generate_response,
        ):
            await webrtc_service._analyze_segment(
                self.session_id,
                0,
                np.ones(16000, dtype=np.float32),
                start_timer(),
            )

        self.assertEqual(
            webrtc_service.segment_results[self.session_id][0]["response_status"],
            "skipped",
        )
        generate_response.assert_not_called()


if __name__ == "__main__":
    unittest.main()
