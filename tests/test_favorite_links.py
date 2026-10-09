import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox
from ui import favorite_links
from ui.favorite_links import FavoriteLinksWidget, load_links, save_links, validate_link


class FavoriteLinksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_persistence_and_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "links.json"
            save_links([{"name": "Bank", "url": "https://bank.example/"}], path)
            self.assertEqual(load_links(path)[0]["domain"], "bank.example")
            for url in ("http://bank.example", "https://bank.example/?token=secret",
                        "https://user@bank.example", "https://bad.example\\@bank.example"):
                with self.subTest(url=url), self.assertRaises(ValueError):
                    validate_link("Bank", url)

    def test_widget_shows_full_address_before_opening(self):
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(favorite_links, "FAVORITES_FILE", Path(folder) / "links.json"):
            save_links([{"name": "Wyniki badań", "url": "https://results.example/"}])
            widget = FavoriteLinksWidget()
            try:
                with patch("ui.favorite_links.QMessageBox.question", return_value=QMessageBox.No) as question, \
                        patch("ui.favorite_links.QDesktopServices.openUrl") as open_url:
                    widget.open_link(0)
                    self.assertIn("https://results.example/", question.call_args.args[2])
                    open_url.assert_not_called()
            finally:
                widget.close()


if __name__ == "__main__":
    unittest.main()
