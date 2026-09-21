from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QIcon

APP_ID = "PrestigeTech.Dashboard.1.0"
ROOT = Path(__file__).resolve().parent.parent
ICON_PATH = ROOT / "assets" / "prestige_tech_app.svg"


def apply_windows_app_id():
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def app_icon():
    if ICON_PATH.is_file():
        return QIcon(str(ICON_PATH))
    return QIcon()
