from __future__ import annotations

import os
import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .system_info import (
    build_summary,
    collect_snapshot,
    format_snapshot_text,
)
from .system_tools_page import SystemToolsPage


class HardwareCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("HardwareCard")
        self.setStyleSheet(
            "QFrame#HardwareCard{"
            "background:#092238;"
            "border:1px solid #18577e;"
            "border-radius:12px;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)

        self.title = QLabel(title)
        self.title.setStyleSheet(
            "font-size:9pt;font-weight:800;color:#34bfff;"
        )
        layout.addWidget(self.title)

        self.value = QLabel("Odczyt danych...")
        self.value.setWordWrap(True)
        self.value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.value.setStyleSheet(
            "font-size:9pt;color:#e7edf5;"
        )
        layout.addWidget(self.value, 1)

        self.setMinimumHeight(120)

    def set_value(self, text):
        self.value.setText(str(text))


class SystemToolsEnhancedPage(QWidget):
    CACHE_SECONDS = 45

    def __init__(self, module_manager):
        super().__init__()

        self.mm = module_manager
        self.legacy = SystemToolsPage(module_manager)

        self.snapshot = {}
        self.display_info = {}
        self.last_refresh = 0.0

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("HardwareHeader")
        header.setStyleSheet(
            "QFrame#HardwareHeader{"
            "background:#071724;"
            "border:1px solid #155078;"
            "border-radius:12px;"
            "}"
        )

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(9)

        top = QHBoxLayout()

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("Sprzęt i środowisko")
        title.setStyleSheet(
            "font-size:17pt;font-weight:900;color:#ffffff;"
        )
        title_box.addWidget(title)

        subtitle = QLabel(
            "Szybki snapshot sprzętu w stylu HWiNFO - bez instalowania dodatkowego programu."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            "font-size:9pt;color:#9bb2c7;"
        )
        title_box.addWidget(subtitle)

        top.addLayout(title_box, 1)

        self.refresh_button = QPushButton("Odśwież dane")
        self.refresh_button.clicked.connect(
            lambda: self.refresh_hardware(force=True)
        )
        top.addWidget(self.refresh_button)

        self.copy_button = QPushButton("Kopiuj specyfikację")
        self.copy_button.clicked.connect(self.copy_specification)
        top.addWidget(self.copy_button)

        header_layout.addLayout(top)

        self.status = QLabel("Dane nie zostały jeszcze odczytane.")
        self.status.setStyleSheet(
            "font-size:8pt;color:#7fa5c0;"
        )
        header_layout.addWidget(self.status)

        root.addWidget(header)

        self.cards = {}
        self.cards_grid = QGridLayout()
        self.cards_grid.setHorizontalSpacing(12)
        self.cards_grid.setVerticalSpacing(12)

        card_titles = [
            "System",
            "CPU",
            "RAM",
            "GPU",
            "Ekran",
            "Dyski",
            "Sieć",
            "Płyta / BIOS",
            "Bateria",
        ]

        for index, title_text in enumerate(card_titles):
            card = HardwareCard(title_text)
            self.cards[title_text] = card
            row = index // 3
            col = index % 3
            self.cards_grid.addWidget(card, row, col)

        for col in range(3):
            self.cards_grid.setColumnStretch(col, 1)

        root.addLayout(self.cards_grid)

        details_title = QLabel("Szczegóły sprzętu")
        details_title.setStyleSheet(
            "font-size:12pt;font-weight:800;color:#ffffff;"
        )
        root.addWidget(details_title)

        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumBlockCount(3000)
        self.details.setMinimumHeight(230)
        self.details.setStyleSheet(
            "QPlainTextEdit{"
            "background:#06131f;"
            "border:1px solid #155078;"
            "border-radius:10px;"
            "padding:10px;"
            "font-family:Consolas;"
            "font-size:9pt;"
            "color:#dbe8f5;"
            "}"
        )
        root.addWidget(self.details)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(
            "color:#155078;background:#155078;max-height:1px;"
        )
        root.addWidget(divider)

        root.addWidget(self.legacy)

    def _current_display_info(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return {}

        geometry = screen.geometry()
        dpi = float(screen.logicalDotsPerInch() or 96.0)

        return {
            "name": screen.name(),
            "width": geometry.width(),
            "height": geometry.height(),
            "refresh_hz": round(float(screen.refreshRate() or 0.0), 1),
            "scale_percent": round((dpi / 96.0) * 100),
        }

    def refresh_hardware(self, force=False):
        if os.environ.get("PRESTIGE_SKIP_SYSTEM_PROBE") == "1":
            force = True

        now = time.monotonic()
        if (
            not force
            and self.snapshot
            and now - self.last_refresh < self.CACHE_SECONDS
        ):
            return

        self.refresh_button.setEnabled(False)
        self.status.setText("Odczyt danych sprzętowych...")
        QApplication.processEvents()

        try:
            self.display_info = self._current_display_info()
            self.snapshot = collect_snapshot()

            summary = build_summary(
                self.snapshot,
                self.display_info,
            )

            for title, card in self.cards.items():
                card.set_value(summary.get(title, "brak danych"))

            text = format_snapshot_text(
                self.snapshot,
                self.display_info,
            )
            self.details.setPlainText(text)

            self.last_refresh = time.monotonic()
            self.status.setText(
                "Snapshot gotowy. Dane są lokalne i nie są nigdzie wysyłane."
            )

        except Exception as exc:
            self.status.setText(
                "Nie udało się pobrać części danych sprzętowych."
            )

            self.details.setPlainText(
                "Błąd odczytu danych sprzętowych:\n"
                + f"{type(exc).__name__}: {exc}\n\n"
                + "Pozostałe narzędzia systemowe poniżej nadal działają."
            )

        finally:
            self.refresh_button.setEnabled(True)

    def copy_specification(self):
        if not self.snapshot:
            self.refresh_hardware(force=True)

        text = format_snapshot_text(
            self.snapshot,
            self.display_info,
        )

        QGuiApplication.clipboard().setText(text)

        QMessageBox.information(
            self,
            "Specyfikacja",
            "Specyfikacja sprzętu została skopiowana do schowka.",
        )

    def render(self):
        self.refresh_hardware(force=False)

        if hasattr(self.legacy, "render"):
            self.legacy.render()