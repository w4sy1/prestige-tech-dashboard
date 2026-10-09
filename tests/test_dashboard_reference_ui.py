import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui.home_simple_page import ActionTile
from ui.main_window import MainWindow


class ReferenceDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_second_style_navigation_and_blue_restore(self):
        window = MainWindow()
        try:
            window.settings_data["dashboard_style"] = "simple"
            window.apply_dashboard_style()
            window.navigate("Strona główna")
            self.assertIs(window.stack.currentWidget(), window.simple_home_view)
            self.assertFalse(window.footer.isVisibleTo(window))
            self.assertEqual(window.sidebar.buttons["Strona główna"].text(), "Dashboard")
            self.assertEqual(len(window.simple_home.findChildren(ActionTile)), 5)
            window.navigate("Moduły")
            self.assertIs(window.stack.currentWidget(), window.modules_view)
            self.app.processEvents()
            self.assertIn("#d5a65b", window.styleSheet())
            window.navigate("Raporty")
            self.app.processEvents()
            self.assertIs(window.stack.currentWidget(), window.reports_view)
            self.assertIn("#d5a65b", window.styleSheet())
            window.settings_data["dashboard_style"] = "blue"
            window.apply_dashboard_style()
            self.assertIn("#078cff", window.styleSheet())
            window.navigate("Strona główna")
            self.assertIs(window.stack.currentWidget(), window.home_view)
            self.assertEqual(window.sidebar.buttons["Strona główna"].text(), "Strona główna")
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
