import asyncio
import unittest
from unittest.mock import patch

import numpy as np

from services import webrtc_service
from services.emotion_service import EmotionPrediction
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
        self.assertEqual(
            webrtc_service.transcription_statuses[self.session_id],
            "listening",
        )


if __name__ == "__main__":
    unittest.main()
