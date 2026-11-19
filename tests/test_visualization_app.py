import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP_PATHS = (
    ROOT / "visualization" / "app.py",
    ROOT / "visualization" / "pages" / "1_Blue_3.py",
    ROOT / "visualization" / "pages" / "2_Sleepy_Alarm.py",
)


class TestVisualizationPages(unittest.TestCase):
    def test_all_pages_load_without_exceptions(self):
        for path in APP_PATHS:
            with self.subTest(page=path.name):
                app = AppTest.from_file(str(path), default_timeout=30).run()
                self.assertEqual(len(app.exception), 0, f"{path.name}: {app.exception}")

                if path == APP_PATHS[0]:
                    success_messages = [element.value for element in app.success]
                    self.assertIn("Artifact SHA-256 check passed: 3/3", success_messages)
                    self.assertIn(
                        "Verification gate passed for all three artifacts and both full-flag comparisons.",
                        success_messages,
                    )
                elif path == APP_PATHS[2]:
                    metrics = {element.label: element.value for element in app.metric}
                    self.assertEqual(metrics["Baseline"], "PASS")
                    self.assertEqual(metrics["One-sided variants PASS"], "2/6")
                    robustness_rows = app.dataframe[1].value.to_dict(orient="records")
                    self.assertEqual(len(robustness_rows), 6)
                    self.assertEqual(
                        {row["variant"] for row in robustness_rows},
                        {
                            "target_only_gain_0.5",
                            "target_only_gain_1.5",
                            "target_only_resample_44k1_48k_44k1",
                            "reference_only_gain_0.5",
                            "reference_only_gain_1.5",
                            "reference_only_resample_44k1_48k_44k1",
                        },
                    )
                    self.assertEqual(
                        {row["variant"] for row in robustness_rows if row["status"] == "PASS"},
                        {
                            "target_only_resample_44k1_48k_44k1",
                            "reference_only_resample_44k1_48k_44k1",
                        },
                    )


if __name__ == "__main__":
    unittest.main()
