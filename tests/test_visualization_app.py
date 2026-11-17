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


if __name__ == "__main__":
    unittest.main()
