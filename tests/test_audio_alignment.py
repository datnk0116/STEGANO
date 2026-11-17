import unittest
from pathlib import Path
import sys

import numpy as np
from scipy.signal import resample_poly

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from audio_alignment import align_audio


class TestAudioAlignment(unittest.TestCase):
    def test_resamples_different_sample_rates_and_aligns_delay(self):
        rng = np.random.default_rng(2026)
        reference = rng.normal(size=6000)
        reference = np.convolve(reference, np.ones(9) / 9, mode="same")
        # Represent the same duration at twice the sample rate.
        target_body = resample_poly(reference, 2, 1)
        target = np.concatenate((np.zeros(240), target_body, np.zeros(160)))

        actual, aligned_reference, info = align_audio(
            target, 16000, reference, 8000
        )

        self.assertEqual(info["lag_samples"], 240)
        self.assertEqual(info["sample_rate"], 16000)
        self.assertGreater(info["correlation"], 0.99)
        self.assertEqual(len(actual), len(aligned_reference))

    def test_different_lengths_return_only_shared_overlap(self):
        rng = np.random.default_rng(42)
        reference = rng.normal(size=5000)
        target = np.concatenate((np.zeros(125), reference, np.zeros(75)))

        actual, aligned_reference, info = align_audio(target, 8000, reference, 8000)

        self.assertEqual(info["lag_samples"], 125)
        self.assertEqual(info["target_start_sample"], 125)
        self.assertEqual(info["overlap_samples"], 5000)
        np.testing.assert_allclose(actual, aligned_reference, atol=1e-12)

    def test_rejects_invalid_sample_rate(self):
        with self.assertRaises(ValueError):
            align_audio(np.ones(10), 0, np.ones(10), 8000)


if __name__ == "__main__":
    unittest.main()
