import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ui import settings_store


class DashboardStyleSettingsTest(unittest.TestCase):
    def test_style_persists_and_invalid_style_falls_back_to_blue(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            with patch.object(settings_store, "SETTINGS_FILE", path):
                settings_store.save_settings({"dashboard_style": "simple"})
                self.assertEqual(settings_store.load_settings()["dashboard_style"], "simple")
                path.write_text('{"dashboard_style":"unknown"}', encoding="utf-8")
                self.assertEqual(settings_store.load_settings()["dashboard_style"], "blue")
                with self.assertRaises(ValueError):
                    settings_store.save_settings({"dashboard_style": "unknown"})


if __name__ == "__main__":
    unittest.main()
