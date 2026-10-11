import unittest

import numpy as np

from services.vad_service import FRAME_SAMPLE_COUNT, StreamingSileroVAD


class FakeSession:
    def __init__(self, probabilities):
        self.probabilities = iter(probabilities)
        self.hidden_states = []

    def run(self, _, inputs):
        self.hidden_states.append(inputs["h"].copy())
        probability = next(self.probabilities)
        return (
            np.array([[probability]], dtype=np.float32),
            inputs["h"] + 1,
            inputs["c"] + 1,
        )


class FakeModel:
    def __init__(self, probabilities):
        self.session = FakeSession(probabilities)


class StreamingSileroVADTests(unittest.TestCase):
    def test_processes_only_complete_silero_frames(self):
        vad = StreamingSileroVAD(FakeModel([0.8]))
        samples = np.arange(FRAME_SAMPLE_COUNT, dtype=np.float32)

        self.assertEqual(vad.process(samples[:300]), [])
        frames = vad.process(samples[300:])

        self.assertEqual(len(frames), 1)
        np.testing.assert_array_equal(frames[0].samples, samples)
        self.assertTrue(frames[0].speech_started)

    def test_requires_sustained_silence_and_resets_after_speech_end(self):
        probabilities = [0.8] + [0.4] * 25 + [0.1] * 25 + [0.8]
        model = FakeModel(probabilities)
        vad = StreamingSileroVAD(model)
        samples = np.zeros(FRAME_SAMPLE_COUNT * len(probabilities), dtype=np.float32)

        frames = vad.process(samples)

        self.assertTrue(frames[0].speech_started)
        self.assertFalse(any(frame.speech_ended for frame in frames[:26]))
        self.assertTrue(frames[50].speech_ended)
        self.assertTrue(frames[51].speech_started)
        np.testing.assert_array_equal(
            model.session.hidden_states[51],
            np.zeros((1, 1, 128), dtype=np.float32),
        )


if __name__ == "__main__":
    unittest.main()
