from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app_version import APP_VERSION
from pdf_export import export_pdf
from .report_store import (
    clear_draft,
    load_draft,
    save_draft,
)
from .reports_page import ReportsPage


class ReportsEnhancedPage(QWidget):
    MODES = (
        "Raport techniczny",
        "Raport dla klienta",
        "Skrócony protokół",
    )

    def __init__(self):
        super().__init__()

        self.legacy = ReportsPage()
        self._loading = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("ReportHeader")
        header.setStyleSheet(
            "QFrame#ReportHeader{"
            "background:#071724;"
            "border:1px solid #155078;"
            "border-radius:12px;"
            "}"
        )

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(8)

        title = QLabel("Raporty 2.0")
        title.setStyleSheet(
            "font-size:18pt;font-weight:900;color:#ffffff;"
        )
        header_layout.addWidget(title)

        subtitle = QLabel(
            "Raport techniczny, wersja dla klienta albo krótki protokół. "
            "Snapshot sprzętu może zostać dodany bezpośrednio z Narzędzi systemowych."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            "font-size:9pt;color:#9bb2c7;"
        )
        header_layout.addWidget(subtitle)

        root.addWidget(header)

        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(12)
        top_grid.setVerticalSpacing(12)

        general = self._card("Raport / klient")
        general_form = QFormLayout(general)
        general_form.setContentsMargins(14, 14, 14, 14)
        general_form.setSpacing(8)

        self.mode = QComboBox()
        self.mode.addItems(self.MODES)
        general_form.addRow("Tryb:", self.mode)

        self.client = QLineEdit()
        self.client.setPlaceholderText("np. Jan Kowalski")
        general_form.addRow("Klient:", self.client)

        self.contact = QLineEdit()
        self.contact.setPlaceholderText("opcjonalnie")
        general_form.addRow("Kontakt:", self.contact)

        self.device = QLineEdit()
        self.device.setPlaceholderText("np. Lenovo ThinkPad / PC gamingowy")
        general_form.addRow("Urządzenie:", self.device)

        self.serial = QLineEdit()
        self.serial.setPlaceholderText("opcjonalnie")
        general_form.addRow("S/N:", self.serial)

        self.status = QComboBox()
        self.status.addItems(
            (
                "W trakcie",
                "Zakończono",
                "Wymaga dalszej diagnostyki",
                "Oczekiwanie na klienta",
                "Nie naprawiono",
            )
        )
        general_form.addRow("Status:", self.status)

        billing = self._card("Czas i rozliczenie")
        billing_form = QFormLayout(billing)
        billing_form.setContentsMargins(14, 14, 14, 14)
        billing_form.setSpacing(8)

        self.work_minutes = QSpinBox()
        self.work_minutes.setRange(0, 100000)
        self.work_minutes.setSuffix(" min")
        billing_form.addRow("Czas pracy:", self.work_minutes)

        self.price = QDoubleSpinBox()
        self.price.setRange(0.0, 1000000.0)
        self.price.setDecimals(2)
        self.price.setSuffix(" zł")
        billing_form.addRow("Cena:", self.price)

        self.report_date = QLabel(
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        billing_form.addRow("Data:", self.report_date)

        author = QLabel("Dominik Wasilak / Prestige Tech")
        author.setTextInteractionFlags(Qt.TextSelectableByMouse)
        billing_form.addRow("Technik:", author)

        top_grid.addWidget(general, 0, 0)
        top_grid.addWidget(billing, 0, 1)
        top_grid.setColumnStretch(0, 2)
        top_grid.setColumnStretch(1, 1)

        root.addLayout(top_grid)

        self.problem = self._text_area(
            "Problem zgłoszony przez klienta",
            "Co dokładnie zgłosił klient? Objawy, kiedy występują, od kiedy.",
            110,
        )
        root.addWidget(self.problem["frame"])

        self.diagnosis = self._text_area(
            "Diagnostyka / ustalenia techniczne",
            "Pomiary, obserwacje, wyniki testów i wnioski.",
            150,
        )
        root.addWidget(self.diagnosis["frame"])

        priorities = self._card("Znalezione problemy według priorytetu")
        priority_layout = QGridLayout(priorities)
        priority_layout.setContentsMargins(14, 14, 14, 14)
        priority_layout.setSpacing(10)

        self.issues_critical = self._plain("Krytyczne")
        self.issues_important = self._plain("Ważne")
        self.issues_info = self._plain("Informacyjne")

        priority_layout.addWidget(QLabel("Krytyczne"), 0, 0)
        priority_layout.addWidget(QLabel("Ważne"), 0, 1)
        priority_layout.addWidget(QLabel("Informacyjne"), 0, 2)
        priority_layout.addWidget(self.issues_critical, 1, 0)
        priority_layout.addWidget(self.issues_important, 1, 1)
        priority_layout.addWidget(self.issues_info, 1, 2)

        root.addWidget(priorities)

        actions_grid = QGridLayout()
        actions_grid.setSpacing(12)

        self.actions_done = self._text_area(
            "Wykonane czynności",
            "Co zostało wykonane podczas serwisu.",
            130,
        )
        self.actions_not_done = self._text_area(
            "Niewykonane / ograniczenia",
            "Czego nie wykonano i dlaczego.",
            130,
        )

        actions_grid.addWidget(self.actions_done["frame"], 0, 0)
        actions_grid.addWidget(self.actions_not_done["frame"], 0, 1)
        root.addLayout(actions_grid)

        self.recommendations = self._text_area(
            "Zalecenia",
            "Co klient powinien zrobić dalej, co obserwować, co wymienić lub zaktualizować.",
            130,
        )
        root.addWidget(self.recommendations["frame"])

        snapshot_card = self._card("Snapshot sprzętu z Narzędzi systemowych")
        snapshot_layout = QVBoxLayout(snapshot_card)
        snapshot_layout.setContentsMargins(14, 14, 14, 14)
        snapshot_layout.setSpacing(8)

        self.snapshot_status = QLabel("Brak snapshotu w szkicu.")
        self.snapshot_status.setStyleSheet(
            "color:#7fa5c0;font-size:8pt;"
        )
        snapshot_layout.addWidget(self.snapshot_status)

        self.snapshot_text = QPlainTextEdit()
        self.snapshot_text.setReadOnly(True)
        self.snapshot_text.setMinimumHeight(180)
        self.snapshot_text.setStyleSheet(
            "QPlainTextEdit{"
            "background:#06131f;"
            "border:1px solid #155078;"
            "border-radius:8px;"
            "padding:8px;"
            "font-family:Consolas;"
            "font-size:8.5pt;"
            "color:#dbe8f5;"
            "}"
        )
        snapshot_layout.addWidget(self.snapshot_text)

        snapshot_buttons = QHBoxLayout()

        reload_snapshot = QPushButton("Wczytaj snapshot ze szkicu")
        reload_snapshot.clicked.connect(self.load_snapshot)
        snapshot_buttons.addWidget(reload_snapshot)

        snapshot_buttons.addStretch()
        snapshot_layout.addLayout(snapshot_buttons)

        root.addWidget(snapshot_card)

        self.notes = self._text_area(
            "Notatki technika",
            "Dodatkowe informacje wewnętrzne.",
            110,
        )
        root.addWidget(self.notes["frame"])

        actions = QFrame()
        actions.setObjectName("ReportActions")
        actions.setStyleSheet(
            "QFrame#ReportActions{"
            "background:#071724;"
            "border:1px solid #155078;"
            "border-radius:10px;"
            "}"
        )

        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(12, 10, 12, 10)
        actions_layout.setSpacing(8)

        save_btn = QPushButton("Zapisz szkic")
        save_btn.clicked.connect(self.save)
        actions_layout.addWidget(save_btn)

        copy_btn = QPushButton("Kopiuj raport")
        copy_btn.clicked.connect(self.copy_report)
        actions_layout.addWidget(copy_btn)

        json_btn = QPushButton("Eksport JSON")
        json_btn.clicked.connect(self.export_json)
        actions_layout.addWidget(json_btn)

        txt_btn = QPushButton("Eksport TXT")
        txt_btn.clicked.connect(self.export_txt)
        actions_layout.addWidget(txt_btn)

        pdf_btn = QPushButton("Eksport PDF")
        pdf_btn.clicked.connect(self.export_pdf)
        actions_layout.addWidget(pdf_btn)

        actions_layout.addStretch()

        clear_btn = QPushButton("Wyczyść formularz")
        clear_btn.clicked.connect(self.clear)
        actions_layout.addWidget(clear_btn)

        root.addWidget(actions)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(
            "color:#155078;background:#155078;max-height:1px;"
        )
        root.addWidget(divider)

        legacy_title = QLabel("Dotychczasowe raporty / historia")
        legacy_title.setStyleSheet(
            "font-size:12pt;font-weight:800;color:#ffffff;"
        )
        root.addWidget(legacy_title)

        root.addWidget(self.legacy)

        self.load()

    def _card(self, title):
        frame = QFrame()
        frame.setObjectName("ReportCard")
        frame.setStyleSheet(
            "QFrame#ReportCard{"
            "background:#092238;"
            "border:1px solid #18577e;"
            "border-radius:10px;"
            "}"
        )
        frame.setProperty("title", title)
        return frame

    def _plain(self, placeholder):
        edit = QPlainTextEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(110)
        return edit

    def _text_area(self, title, placeholder, height):
        frame = self._card(title)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)

        label = QLabel(title)
        label.setStyleSheet(
            "font-size:10pt;font-weight:800;color:#ffffff;"
        )
        layout.addWidget(label)

        edit = QPlainTextEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(height)
        layout.addWidget(edit)

        return {"frame": frame, "edit": edit}

    def _draft_from_form(self):
        current = load_draft()

        current.update(
            {
                "mode": self.mode.currentText(),
                "client": self.client.text().strip(),
                "contact": self.contact.text().strip(),
                "device": self.device.text().strip(),
                "serial": self.serial.text().strip(),
                "status": self.status.currentText(),
                "problem": self.problem["edit"].toPlainText().strip(),
                "diagnosis": self.diagnosis["edit"].toPlainText().strip(),
                "issues_critical": self.issues_critical.toPlainText().strip(),
                "issues_important": self.issues_important.toPlainText().strip(),
                "issues_info": self.issues_info.toPlainText().strip(),
                "actions_done": self.actions_done["edit"].toPlainText().strip(),
                "actions_not_done": self.actions_not_done["edit"].toPlainText().strip(),
                "recommendations": self.recommendations["edit"].toPlainText().strip(),
                "notes": self.notes["edit"].toPlainText().strip(),
                "work_minutes": self.work_minutes.value(),
                "price": float(self.price.value()),
            }
        )

        return current

    def _set_combo(self, combo, value):
        index = combo.findText(str(value))
        if index >= 0:
            combo.setCurrentIndex(index)

    def load(self):
        self._loading = True
        try:
            draft = load_draft()

            self._set_combo(self.mode, draft.get("mode", self.MODES[0]))
            self.client.setText(str(draft.get("client") or ""))
            self.contact.setText(str(draft.get("contact") or ""))
            self.device.setText(str(draft.get("device") or ""))
            self.serial.setText(str(draft.get("serial") or ""))
            self._set_combo(self.status, draft.get("status", "W trakcie"))

            self.problem["edit"].setPlainText(str(draft.get("problem") or ""))
            self.diagnosis["edit"].setPlainText(str(draft.get("diagnosis") or ""))
            self.issues_critical.setPlainText(str(draft.get("issues_critical") or ""))
            self.issues_important.setPlainText(str(draft.get("issues_important") or ""))
            self.issues_info.setPlainText(str(draft.get("issues_info") or ""))
            self.actions_done["edit"].setPlainText(str(draft.get("actions_done") or ""))
            self.actions_not_done["edit"].setPlainText(str(draft.get("actions_not_done") or ""))
            self.recommendations["edit"].setPlainText(str(draft.get("recommendations") or ""))
            self.notes["edit"].setPlainText(str(draft.get("notes") or ""))

            self.work_minutes.setValue(int(draft.get("work_minutes") or 0))
            self.price.setValue(float(draft.get("price") or 0.0))

            self.load_snapshot(draft=draft)

        finally:
            self._loading = False

    def load_snapshot(self, draft=None):
        data = draft or load_draft()
        snapshot = data.get("system_snapshot") or {}
        text = str(snapshot.get("text") or "")

        self.snapshot_text.setPlainText(text)

        added_at = str(snapshot.get("added_at") or "")
        if text:
            self.snapshot_status.setText(
                "Snapshot w szkicu"
                + (f" | dodano {added_at}" if added_at else "")
            )
        else:
            self.snapshot_status.setText(
                "Brak snapshotu. Użyj 'Dodaj do raportu' w Narzędziach systemowych."
            )

    def save(self):
        save_draft(self._draft_from_form())

        QMessageBox.information(
            self,
            "Raporty",
            "Szkic raportu zapisany lokalnie.",
        )

    def _lines(self, text):
        return [
            line.strip()
            for line in str(text or "").splitlines()
            if line.strip()
        ]

    def _payload(self):
        draft = self._draft_from_form()
        mode = draft["mode"]

        base = {
            "raport": {
                "typ": mode,
                "data": datetime.now().isoformat(timespec="seconds"),
                "dashboard_version": APP_VERSION,
                "technik": "Dominik Wasilak / Prestige Tech",
            },
            "klient": {
                "nazwa": draft["client"] or "Nie podano",
                "kontakt": draft["contact"] or "Nie podano",
            },
            "urzadzenie": {
                "opis": draft["device"] or "Nie podano",
                "numer_seryjny": draft["serial"] or "Nie podano",
            },
            "status": draft["status"],
            "problem_zgloszony": draft["problem"] or "Nie podano",
            "wykonane_czynnosci": self._lines(draft["actions_done"]),
            "zalecenia": self._lines(draft["recommendations"]),
            "czas_pracy_min": draft["work_minutes"],
            "cena_pln": draft["price"],
            "podpis_technika": "Dominik Wasilak",
            "podpis_klienta": "____________________________",
        }

        system_snapshot = draft.get("system_snapshot") or {}
        snapshot_text = system_snapshot.get("text") or ""

        if mode == "Raport techniczny":
            base["diagnostyka_techniczna"] = draft["diagnosis"] or "Brak"
            base["problemy"] = {
                "krytyczne": self._lines(draft["issues_critical"]),
                "wazne": self._lines(draft["issues_important"]),
                "informacyjne": self._lines(draft["issues_info"]),
            }
            base["niewykonane_lub_ograniczenia"] = self._lines(
                draft["actions_not_done"]
            )
            base["snapshot_sprzetu"] = snapshot_text or "Brak snapshotu"
            base["wyniki_modulow"] = draft.get("module_results") or []
            base["notatki_technika"] = draft["notes"] or "Brak"

        elif mode == "Raport dla klienta":
            base["co_ustalono"] = draft["diagnosis"] or "Brak dodatkowych ustaleń"
            base["najwazniejsze_problemy"] = (
                self._lines(draft["issues_critical"])
                + self._lines(draft["issues_important"])
            )
            if snapshot_text:
                base["specyfikacja_urzadzenia"] = snapshot_text
            base["uwagi"] = draft["notes"] or "Brak"

        else:
            base = {
                "raport": base["raport"],
                "klient": base["klient"],
                "urzadzenie": base["urzadzenie"],
                "status": base["status"],
                "problem": base["problem_zgloszony"],
                "wykonano": base["wykonane_czynnosci"],
                "zalecenia": base["zalecenia"],
                "czas_pracy_min": base["czas_pracy_min"],
                "cena_pln": base["cena_pln"],
                "podpis_technika": base["podpis_technika"],
                "podpis_klienta": base["podpis_klienta"],
            }

        return base

    def _text_report(self):
        payload = self._payload()

        def walk(value, depth=0):
            lines = []
            indent = "  " * depth

            if isinstance(value, dict):
                for key, item in value.items():
                    label = str(key).replace("_", " ").upper()
                    lines.append(indent + label)
                    lines.extend(walk(item, depth + 1))
                return lines

            if isinstance(value, list):
                if not value:
                    return [indent + "- brak"]
                for item in value:
                    if isinstance(item, (dict, list)):
                        lines.extend(walk(item, depth + 1))
                    else:
                        lines.append(indent + "- " + str(item))
                return lines

            text = str(value)
            if "\n" in text:
                return [indent + line for line in text.splitlines()]
            return [indent + text]

        lines = [
            "PRESTIGE TECH",
            "By Dominik Wasilak",
            "",
        ]
        lines.extend(walk(payload))
        return "\n".join(lines).rstrip() + "\n"

    def copy_report(self):
        save_draft(self._draft_from_form())
        QGuiApplication.clipboard().setText(self._text_report())

        QMessageBox.information(
            self,
            "Raporty",
            "Raport skopiowany do schowka.",
        )

    def export_json(self):
        save_draft(self._draft_from_form())

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Eksport JSON",
            "Prestige-Tech-Raport.json",
            "JSON (*.json)",
        )

        if not path:
            return

        if not path.lower().endswith(".json"):
            path += ".json"

        Path(path).write_text(
            json.dumps(
                self._payload(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        QMessageBox.information(
            self,
            "Raporty",
            "Zapisano JSON.",
        )

    def export_txt(self):
        save_draft(self._draft_from_form())

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Eksport TXT",
            "Prestige-Tech-Raport.txt",
            "TXT (*.txt)",
        )

        if not path:
            return

        if not path.lower().endswith(".txt"):
            path += ".txt"

        Path(path).write_text(
            self._text_report(),
            encoding="utf-8",
        )

        QMessageBox.information(
            self,
            "Raporty",
            "Zapisano TXT.",
        )

    def export_pdf(self):
        save_draft(self._draft_from_form())

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Eksport PDF",
            "Prestige-Tech-Raport.pdf",
            "PDF (*.pdf)",
        )

        if not path:
            return

        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            export_pdf(
                self._payload(),
                path,
                title=self.mode.currentText(),
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Raport PDF",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Raporty",
            "Zapisano PDF.",
        )

    def clear(self):
        answer = QMessageBox.question(
            self,
            "Raporty",
            "Wyczyścić cały szkic raportu?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        clear_draft()
        self.load()

    def render(self):
        self.load_snapshot()

        if hasattr(self.legacy, "render"):
            self.legacy.render()