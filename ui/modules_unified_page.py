from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from module_manager import MODULES_DIR
from .modules_page import ModulesPage


def _folder_size(path: Path) -> int:
    total = 0
    try:
        if not path.exists():
            return 0

        for item in path.rglob("*"):
            try:
                if item.is_file():
                    total += item.stat().st_size
            except OSError:
                pass
    except OSError:
        pass
    return total


def _human_size(value: int) -> str:
    size = float(value)
    units = ("B", "KB", "MB", "GB", "TB")

    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit in ("B", "KB"):
                return f"{size:.0f} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0

    return f"{value} B"


class ModulesUnifiedPage(QWidget):
    install_requested = Signal(object)
    run_requested = Signal(object)
    remove_requested = Signal(object)
    help_requested = Signal(object)

    install_all_requested = Signal()
    uninstall_all_requested = Signal()
    portable_changed = Signal(bool)
    icon_requested = Signal(object)

    def __init__(self, module_manager):
        super().__init__()

        self.mm = module_manager
        self.inner = ModulesPage(module_manager)

        self.inner.install_requested.connect(self.install_requested.emit)
        self.inner.run_requested.connect(self.run_requested.emit)
        self.inner.remove_requested.connect(self.remove_requested.emit)
        self.inner.help_requested.connect(self.help_requested.emit)

        self.inner.install_all_requested.connect(self.install_all_requested.emit)
        self.inner.uninstall_all_requested.connect(self.uninstall_all_requested.emit)
        self.inner.portable_changed.connect(self.portable_changed.emit)
        self.inner.icon_requested.connect(self.icon_requested.emit)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        tools = QFrame()
        tools.setObjectName("ModulesUnifiedTools")
        tools.setStyleSheet(
            "QFrame#ModulesUnifiedTools{"
            "background:#071724;"
            "border:1px solid #155078;"
            "border-radius:10px;"
            "}"
        )

        tools_layout = QVBoxLayout(tools)
        tools_layout.setContentsMargins(14, 10, 14, 10)
        tools_layout.setSpacing(7)

        top = QHBoxLayout()
        top.setSpacing(10)

        self.summary = QLabel()
        self.summary.setStyleSheet(
            "font-size:9pt;color:#b7c7d9;font-weight:600;"
        )
        top.addWidget(self.summary, 1)

        self.open_button = QPushButton("Otwórz folder modułów")
        self.open_button.clicked.connect(self.open_modules_folder)
        top.addWidget(self.open_button)

        self.refresh_button = QPushButton("Odśwież")
        self.refresh_button.clicked.connect(self.render)
        top.addWidget(self.refresh_button)

        tools_layout.addLayout(top)

        self.path_label = QLabel()
        self.path_label.setTextInteractionFlags(
            self.path_label.textInteractionFlags()
        )
        self.path_label.setStyleSheet(
            "font-size:8pt;color:#7fa5c0;"
        )
        tools_layout.addWidget(self.path_label)

        root.addWidget(tools)
        root.addWidget(self.inner, 1)

        self.refresh_summary()

    def refresh_summary(self):
        modules = list(getattr(self.mm, "modules", []) or [])

        installed = [
            module
            for module in modules
            if self.mm.is_installed(module)
        ]

        categories = {
            str(getattr(module, "category", "")).strip()
            for module in installed
            if str(getattr(module, "category", "")).strip()
        }

        size = _folder_size(Path(MODULES_DIR))

        self.summary.setText(
            f"Zainstalowane: {len(installed)}   |   "
            f"Miejsce: {_human_size(size)}   |   "
            f"Aktywne kategorie: {len(categories)}"
        )

        self.path_label.setText(
            "Folder: " + str(MODULES_DIR)
        )

    def open_modules_folder(self):
        path = Path(MODULES_DIR)
        path.mkdir(parents=True, exist_ok=True)

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(path.resolve()))
        )

    def render(self):
        self.inner.render()
        self.refresh_summary()

    def set_portable(self, enabled):
        return self.inner.set_portable(enabled)

    def set_filter(self, category, query=""):
        return self.inner.set_filter(category, query)