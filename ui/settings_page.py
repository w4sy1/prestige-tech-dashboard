from pathlib import Path
import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QPushButton, QComboBox, QCheckBox, QMessageBox
from module_manager import APP_DIR, MODULES_DIR, LOGS_DIR, CONFIG_DIR
from .theme import *
from .widgets import label
from .settings_store import load_settings, save_settings, reset_settings, SETTINGS_FILE
from .icon_manager import CONFIG_FILE as ICON_CONFIG_FILE

REPORTS_DIR = APP_DIR / "reports"

class Card(QFrame):
    def __init__(self, title, desc):
        super().__init__()
        self.setStyleSheet(f"QFrame{{background:{CARD};border:1px solid {LINE};border-radius:12px;}}")
        r = QVBoxLayout(self)
        r.setContentsMargins(15,13,15,13)
        r.setSpacing(7)
        r.addWidget(label(title,10,TEXT,True))
        d = label(desc,8,"#a9bfd0")
        d.setWordWrap(True)
        r.addWidget(d)
        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        r.addLayout(self.body)

class SettingsPage(QWidget):
    settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.data = load_settings()

        root = QVBoxLayout(self)
        root.setContentsMargins(26,20,26,22)
        root.setSpacing(11)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("Ustawienia",22,TEXT,True))
        titles.addWidget(label("Konfiguracja Dashboardu i lokalnych danych Prestige Tech.",9,"#aac0d1"))
        header.addLayout(titles)
        header.addStretch()

        save_btn = QPushButton("Zapisz ustawienia")
        save_btn.setProperty("primary", True)
        save_btn.clicked.connect(self.save)
        header.addWidget(save_btn)
        root.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnStretch(0,1)
        grid.setColumnStretch(1,1)

        app = Card("Dashboard","Podstawowe zachowanie aplikacji.")
        row = QHBoxLayout()
        row.addWidget(label("Kanał aktualizacji",8,TEXT,True))
        row.addStretch()
        self.channel = QComboBox()
        self.channel.addItems(["Stable","Beta"])
        self.channel.setCurrentText(self.data["channel"])
        row.addWidget(self.channel)
        app.body.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(label("Język",8,TEXT,True))
        row.addStretch()
        self.language = QComboBox()
        self.language.addItems(["Polski"])
        row.addWidget(self.language)
        app.body.addLayout(row)

        self.check_updates = QCheckBox("Sprawdzaj wersje modułów po uruchomieniu")
        self.check_updates.setChecked(bool(self.data["check_updates_on_start"]))
        app.body.addWidget(self.check_updates)
        grid.addWidget(app,0,0)

        behavior = Card("Moduły","Ustawienia uruchamiania i potwierdzeń bezpieczeństwa.")
        self.portable = QCheckBox("Włączaj Tryb Portable domyślnie")
        self.portable.setChecked(bool(self.data["portable_default"]))
        behavior.body.addWidget(self.portable)

        self.confirm = QCheckBox("Pytaj przed modułami zmieniającymi system")
        self.confirm.setChecked(bool(self.data["confirm_system_changes"]))
        behavior.body.addWidget(self.confirm)
        grid.addWidget(behavior,0,1)

        folders = Card("Foldery Prestige Tech","Szybki dostęp do danych aplikacji.")
        for title,path in (("Aplikacja",APP_DIR),("Moduły",MODULES_DIR),("Raporty",REPORTS_DIR),("Logi",LOGS_DIR),("Konfiguracja",CONFIG_DIR)):
            row = QHBoxLayout()
            txt = QVBoxLayout()
            txt.addWidget(label(title,8,TEXT,True))
            p = label(str(path),7,"#7898ad")
            p.setTextInteractionFlags(Qt.TextSelectableByMouse)
            txt.addWidget(p)
            row.addLayout(txt,1)
            b = QPushButton("Otwórz")
            b.clicked.connect(lambda checked=False,x=path:self.open_folder(x))
            row.addWidget(b)
            folders.body.addLayout(row)
        grid.addWidget(folders,1,0)

        reset = Card("Reset i konfiguracja","Nie usuwa źródłowych EXE ani zainstalowanych modułów.")
        p = label(f"Ustawienia: {SETTINGS_FILE}",7,"#7898ad")
        p.setTextInteractionFlags(Qt.TextSelectableByMouse)
        reset.body.addWidget(p)
        p = label(f"Własne ikony: {ICON_CONFIG_FILE}",7,"#7898ad")
        p.setTextInteractionFlags(Qt.TextSelectableByMouse)
        reset.body.addWidget(p)

        row = QHBoxLayout()
        b = QPushButton("Resetuj własne ikony")
        b.clicked.connect(self.reset_icons)
        row.addWidget(b)
        b = QPushButton("Przywróć ustawienia")
        b.clicked.connect(self.reset_all)
        row.addWidget(b)
        row.addStretch()
        reset.body.addLayout(row)
        grid.addWidget(reset,1,1)

        root.addLayout(grid)
        root.addStretch()

    def collect(self):
        return {
            "channel": self.channel.currentText(),
            "language": self.language.currentText(),
            "portable_default": self.portable.isChecked(),
            "confirm_system_changes": self.confirm.isChecked(),
            "check_updates_on_start": self.check_updates.isChecked(),
        }

    def save(self):
        self.data = self.collect()
        save_settings(self.data)
        self.settings_changed.emit(dict(self.data))
        QMessageBox.information(self,"Ustawienia","Ustawienia zostały zapisane.")

    def open_folder(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(path)

    def reset_icons(self):
        if QMessageBox.warning(self,"Reset ikon","Przywrócić wszystkie domyślne ikony?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No) != QMessageBox.Yes:
            return
        if ICON_CONFIG_FILE.exists():
            ICON_CONFIG_FILE.unlink()
        QMessageBox.information(self,"Reset ikon","Przywrócono domyślne ikony.")

    def reset_all(self):
        if QMessageBox.warning(self,"Reset ustawień","Przywrócić ustawienia domyślne?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No) != QMessageBox.Yes:
            return
        self.data = reset_settings()
        self.channel.setCurrentText(self.data["channel"])
        self.portable.setChecked(self.data["portable_default"])
        self.confirm.setChecked(self.data["confirm_system_changes"])
        self.check_updates.setChecked(self.data["check_updates_on_start"])
        self.settings_changed.emit(dict(self.data))
        QMessageBox.information(self,"Ustawienia","Przywrócono ustawienia domyślne.")
