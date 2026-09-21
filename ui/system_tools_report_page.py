from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
)

from .report_store import update_system_snapshot
from .system_info import format_snapshot_text
from .system_tools_enhanced_page import SystemToolsEnhancedPage


class SystemToolsReportPage(SystemToolsEnhancedPage):
    def __init__(self, module_manager):
        super().__init__(module_manager)

        bridge = QFrame()
        bridge.setObjectName("ReportBridge")
        bridge.setStyleSheet(
            "QFrame#ReportBridge{"
            "background:#101a14;"
            "border:1px solid #2a6040;"
            "border-radius:10px;"
            "}"
        )

        layout = QHBoxLayout(bridge)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(10)

        label = QLabel(
            "Snapshot sprzętu możesz jednym kliknięciem dołączyć do szkicu raportu klienta."
        )
        label.setWordWrap(True)
        label.setStyleSheet(
            "font-size:9pt;color:#cce9d5;"
        )
        layout.addWidget(label, 1)

        self.add_report_button = QPushButton("Dodaj do raportu")
        self.add_report_button.clicked.connect(self.add_to_report)
        layout.addWidget(self.add_report_button)

        self.layout().insertWidget(1, bridge)

    def add_to_report(self):
        if not self.snapshot:
            self.refresh_hardware(force=True)

        if not self.snapshot:
            QMessageBox.warning(
                self,
                "Raport",
                "Nie ma danych sprzętowych do dodania.",
            )
            return

        text = format_snapshot_text(
            self.snapshot,
            self.display_info,
        )

        update_system_snapshot(
            self.snapshot,
            self.display_info,
            text,
        )

        QMessageBox.information(
            self,
            "Raport",
            "Snapshot sprzętu dodany do szkicu Raportów 2.0.",
        )