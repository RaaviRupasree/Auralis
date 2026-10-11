import unittest
from unittest.mock import patch

import numpy as np

from services.emotion_service import (
    EmotionPrediction,
    classify_emotion,
)
from services.vad_service import SAMPLE_RATE


class FakeEmotionPipeline:
    def __init__(self, predictions):
        self.predictions = predictions
        self.audio_input = None

    def __call__(self, audio_input):
        self.audio_input = audio_input
        return self.predictions


class EmotionServiceTests(unittest.TestCase):
    def test_returns_highest_scoring_model_prediction(self):
        classifier = FakeEmotionPipeline(
            [
                {"label": "sad", "score": 0.18},
                {"label": "angry", "score": 0.82},
            ]
        )
        samples = np.array([0.1, -0.1], dtype=np.float32)

        with patch("services.emotion_service._pipeline", classifier):
            prediction = classify_emotion(samples)

        self.assertEqual(prediction, EmotionPrediction("angry", 0.82))
        self.assertEqual(classifier.audio_input["sampling_rate"], SAMPLE_RATE)
        np.testing.assert_array_equal(classifier.audio_input["raw"], samples)

    def test_rejects_empty_speech_segments(self):
        with self.assertRaisesRegex(ValueError, "empty speech segment"):
            classify_emotion(np.empty(0, dtype=np.float32))

    def test_reports_empty_model_predictions(self):
        classifier = FakeEmotionPipeline([])
        with patch("services.emotion_service._pipeline", classifier):
            with self.assertRaisesRegex(RuntimeError, "no predictions"):
                classify_emotion(np.ones(512, dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
