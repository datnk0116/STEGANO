import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stegano.audio import decode_sleepy_alarm  # noqa: E402
from stegano.image import decode_blue3  # noqa: E402


BLUE3_PATH = ROOT / "data" / "blue3" / "blue.png"
SLEEPY_TARGET_PATH = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast.mp3"
SLEEPY_REFERENCE_PATH = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast_original.mp3"

BLUE3_FLAG = "byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}"
SLEEPY_ALARM_FLAG = "ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}"


class TestOfficialFlagExactMatch(unittest.TestCase):
    def test_blue3_matches_the_complete_50_character_flag(self):
        result = decode_blue3(BLUE3_PATH)

        self.assertTrue(result["format_valid"])
        self.assertEqual(len(result["flag"]), 50)
        self.assertEqual(result["flag"], BLUE3_FLAG)

    def test_sleepy_alarm_matches_the_complete_reference_assisted_flag(self):
        result = decode_sleepy_alarm(SLEEPY_TARGET_PATH, SLEEPY_REFERENCE_PATH)

        self.assertTrue(result["reference_assisted"])
        self.assertTrue(result["format_valid"], result["errors"])
        self.assertEqual(len(result["decoded_text"]), 39)
        self.assertEqual(result["decoded_text"], SLEEPY_ALARM_FLAG)
        self.assertEqual(result["symbol_count"], 350)
        self.assertEqual(result["separator_count"], 38)
        self.assertEqual(result["errors"], [])

        # Cross-correlation measures the lag at run time. Do not tie exact
        # flag recovery to one fixed codec lag.
        self.assertIsNotNone(result["alignment"])
        self.assertIn("lag_samples", result["alignment"])


if __name__ == "__main__":
    unittest.main()
