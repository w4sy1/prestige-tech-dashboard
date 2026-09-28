from app_version import APP_VERSION, APP_TITLE
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.app_icon import apply_windows_app_id, app_icon

def main():
    apply_windows_app_id()
    app = QApplication(sys.argv)
    app.setWindowIcon(app_icon())
    app.setApplicationName("Prestige Tech Dashboard")
    win = MainWindow()
    win.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())

