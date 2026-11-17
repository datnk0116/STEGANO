import unittest
from pathlib import Path
from unittest.mock import patch

from visualization.utils import (
    BLUE3_PATH,
    SLEEPY_REFERENCE_PATH,
    SLEEPY_TARGET_PATH,
    align_sleepy_audio,
    audio_metadata,
    bounded_signal,
    image_summary,
    read_waveform,
    run_blue3,
    run_blue3_diagnostics,
    run_sleepy_alarm,
    run_sleepy_alarm_diagnostics,
    sleepy_alignment_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]


class TestVisualizationDecoderCalls(unittest.TestCase):
    @patch("visualization.utils.decode_blue3")
    def test_blue3_runner_returns_decoder_data(self, decoder):
        expected = {
            "flag": "byuctf{example}",
            "format_valid": True,
            "attempts": [{"length": 14, "candidate": "byuctf{example}"}],
        }
        decoder.return_value = expected

        run = run_blue3(BLUE3_PATH)

        decoder.assert_called_once_with(BLUE3_PATH)
        self.assertEqual(run["result"], expected)
        self.assertEqual(run["status"], "Success")

    @patch("visualization.utils.decode_sleepy_alarm")
    def test_audio_runner_passes_both_paths_and_preserves_failure_data(self, decoder):
        expected = {
            "decoded_text": "fragment}",
            "format_valid": False,
            "reference_assisted": False,
            "alignment": None,
            "symbol_count": 350,
            "separator_count": 49,
            "amplitude_centers": [0.1, 0.2, 0.3],
            "errors": [{"byte_index": 2, "bits": "101"}],
        }
        decoder.return_value = expected

        run = run_sleepy_alarm(SLEEPY_TARGET_PATH, None)

        decoder.assert_called_once_with(SLEEPY_TARGET_PATH, None)
        self.assertEqual(run["result"], expected)
        self.assertEqual(run["status"], "Failed")

    def test_missing_image_is_reported_as_failed(self):
        run = run_blue3(ROOT / "data" / "missing.png")
        self.assertEqual(run["status"], "Failed")
        self.assertIsNone(run["result"])
        self.assertIn("FileNotFoundError", run["error"])


class TestVisualizationData(unittest.TestCase):
    def test_blue3_summary_matches_decoder_baseline_and_dimensions(self):
        pixels, baseline, count = image_summary(BLUE3_PATH)
        self.assertEqual(pixels.shape, (512, 512, 3))
        self.assertEqual(baseline, (64, 77, 205))
        self.assertGreater(count, 0)

    def test_audio_metadata_and_waveform_are_bounded(self):
        info = audio_metadata(SLEEPY_TARGET_PATH)
        seconds, samples = read_waveform(SLEEPY_TARGET_PATH, max_points=1000)

        self.assertEqual(info["sample_rate"], 44100)
        self.assertEqual(info["channels"], 2)
        self.assertEqual(samples.shape[1], info["channels"])
        self.assertLessEqual(len(seconds), 1000)
        self.assertEqual(len(seconds), len(samples))
        self.assertTrue((seconds[1:] >= seconds[:-1]).all())

    def test_alignment_visualization_uses_committed_helper(self):
        target, reference, alignment = align_sleepy_audio()
        self.assertEqual(len(target), len(reference))
        self.assertEqual(alignment["sample_rate"], audio_metadata(SLEEPY_TARGET_PATH)["sample_rate"])
        self.assertGreater(alignment["correlation"], 0.9)
        self.assertGreater(alignment["overlap_samples"], 0)

    def test_alignment_diagnostics_preserve_input_and_resampled_lengths(self):
        diagnostics = sleepy_alignment_diagnostics()
        self.assertEqual(
            diagnostics["metadata"]["lag_samples"],
            diagnostics["correlation_lags"][
                int(abs(diagnostics["correlation_profile"]).argmax())
            ],
        )
        self.assertEqual(
            diagnostics["metadata"]["sample_rate"],
            diagnostics["target_sample_rate"],
        )
        self.assertEqual(
            len(diagnostics["reference_resampled"]),
            diagnostics["metadata"]["overlap_samples"]
            + diagnostics["metadata"]["reference_start_sample"],
        )
        self.assertGreater(len(diagnostics["reference_original"]), 0)

    def test_bounded_signal_limits_plot_points(self):
        indices, values = bounded_signal(range(100), max_points=10)
        self.assertLessEqual(len(indices), 10)
        self.assertEqual(len(indices), len(values))
        self.assertEqual(values[0], 0)

    def test_reference_free_decoder_failure_remains_visible(self):
        run = run_sleepy_alarm(SLEEPY_TARGET_PATH)
        self.assertEqual(run["status"], "Failed")
        self.assertIsNone(run["error"])
        self.assertFalse(run["result"]["format_valid"])
        self.assertFalse(run["result"]["reference_assisted"])
        self.assertGreater(len(run["result"]["errors"]), 0)

    def test_reference_assisted_decoder_returns_expected_output(self):
        run = run_sleepy_alarm(SLEEPY_TARGET_PATH, SLEEPY_REFERENCE_PATH)
        self.assertEqual(run["status"], "Success")
        self.assertEqual(run["result"]["decoded_text"], "ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}")
        self.assertEqual(run["result"]["alignment"]["lag_samples"], 1729)
        self.assertEqual(run["result"]["alignment"]["target_start_sample"], 1729)

    def test_sleepy_diagnostics_match_the_reference_assisted_decoder(self):
        run = run_sleepy_alarm_diagnostics(SLEEPY_TARGET_PATH, SLEEPY_REFERENCE_PATH)
        self.assertEqual(run["status"], "Success")
        result = run["result"]
        diagnostics = run["diagnostics"]
        self.assertEqual((result["symbol_count"], result["separator_count"]), (350, 38))
        self.assertEqual(len(diagnostics["amplitude_levels"]), result["symbol_count"])
        self.assertEqual(len(diagnostics["symbol_labels"]), result["symbol_count"])
        self.assertEqual([cluster["center"] for cluster in diagnostics["clusters"]], result["amplitude_centers"])
        self.assertEqual(diagnostics["sample_rate"], 44100)
        self.assertEqual(diagnostics["duration_seconds"], 7.0)
        self.assertEqual(sum(group["codepoint"] == 0 for group in diagnostics["groups"] if group["codepoint"] is not None), 0)

    def test_blue3_diagnostics_describe_the_selected_decoder_blocks(self):
        run = run_blue3_diagnostics(BLUE3_PATH)
        self.assertEqual(run["status"], "Success")
        result = run["result"]
        diagnostics = run["diagnostics"]
        self.assertEqual("".join(block["character"] for block in diagnostics["blocks"]), result["flag"])
        self.assertEqual(len(diagnostics["blocks"]), len(result["flag"]))
        self.assertEqual(diagnostics["baseline"], (64, 77, 205))
        for block in diagnostics["blocks"]:
            self.assertEqual(sum(block["rgb_delta"]), block["value"])
            self.assertEqual(ord(block["character"]), block["value"])


if __name__ == "__main__":
    unittest.main()
