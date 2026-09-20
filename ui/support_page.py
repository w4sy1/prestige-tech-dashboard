from __future__ import annotations

from app_version import APP_VERSION
import os
import platform
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QPushButton, QApplication
)

from module_manager import LOGS_DIR, APP_DIR
from .theme import *
from .widgets import label


GITHUB_PROFILE = "https://github.com/w4sy1"
REPO = "https://github.com/w4sy1/prestige-tech-dashboard"
ISSUES = "https://github.com/w4sy1/prestige-tech-dashboard/issues"
INSTAGRAM = "https://www.instagram.com/projekt.ocalenie/"
FACEBOOK = "https://www.facebook.com/profile.php?viewas=100000686899395&id=61572604231491"


class SupportCard(QFrame):
    def __init__(self, title, description):
        super().__init__()
        self.setStyleSheet(
            f"QFrame{{background:{CARD};border:1px solid {LINE};border-radius:12px;}}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(15, 13, 15, 13)
        root.setSpacing(8)
        root.addWidget(label(title, 11, TEXT, True))

        d = label(description, 8, "#a9bfd0")
        d.setWordWrap(True)
        root.addWidget(d)

        self.body = QVBoxLayout()
        self.body.setSpacing(7)
        root.addLayout(self.body)


class SupportPage(QWidget):
    guide_requested = Signal()

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 22)
        root.setSpacing(12)

        header = QVBoxLayout()
        header.addWidget(label("Wsparcie", 22, TEXT, True))
        header.addWidget(
            label(
                "Pomoc techniczna, zgłaszanie problemów, kontakt i wsparcie rozwoju Prestige Tech.",
                9,
                "#aac0d1",
            )
        )
        root.addLayout(header)

        info = QFrame()
        info.setStyleSheet(
            f"background:#071827;border:1px solid {BLUE};border-radius:12px;"
        )
        iv = QVBoxLayout(info)
        iv.setContentsMargins(15, 12, 15, 12)
        iv.addWidget(label("Najpierw diagnoza", 10, TEXT, True))

        t = label(
            "Jeśli problem dotyczy konkretnego modułu, najpierw użyj przycisku ? przy jego karcie. "
            "Poradnik otworzy odpowiedni temat. Jeśli błąd nadal występuje, zgłoszenie z logami będzie znacznie łatwiejsze do rozwiązania.",
            9,
            "#b8ccd9",
        )
        t.setWordWrap(True)
        iv.addWidget(t)

        root.addWidget(info)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        help_card = SupportCard(
            "Pomoc techniczna",
            "Szybkie ścieżki, gdy coś nie działa.",
        )

        guide = QPushButton("Otwórz Poradnik")
        guide.setProperty("primary", True)
        guide.clicked.connect(self.guide_requested.emit)
        help_card.body.addWidget(guide)

        logs = QPushButton("Otwórz logi Dashboardu")
        logs.clicked.connect(self.open_logs)
        help_card.body.addWidget(logs)

        copy = QPushButton("Kopiuj dane diagnostyczne")
        copy.clicked.connect(self.copy_diagnostics)
        help_card.body.addWidget(copy)

        grid.addWidget(help_card, 0, 0)

        issue_card = SupportCard(
            "Zgłoś problem lub pomysł",
            "Repozytorium może służyć do zgłaszania błędów i propozycji rozwoju.",
        )

        issue = QPushButton("GitHub Issues")
        issue.clicked.connect(lambda: self.open_url(ISSUES))
        issue_card.body.addWidget(issue)

        repo = QPushButton("Otwórz repozytorium")
        repo.clicked.connect(lambda: self.open_url(REPO))
        issue_card.body.addWidget(repo)

        profile = QPushButton("Profil GitHub w4sy1")
        profile.clicked.connect(lambda: self.open_url(GITHUB_PROFILE))
        issue_card.body.addWidget(profile)

        grid.addWidget(issue_card, 0, 1)

        contact_card = SupportCard(
            "Kontakt",
            "Kanały, które zostały podłączone do projektu.",
        )

        instagram = QPushButton("Instagram  |  projekt.ocalenie")
        instagram.clicked.connect(lambda: self.open_url(INSTAGRAM))
        contact_card.body.addWidget(instagram)

        facebook = QPushButton("Facebook")
        facebook.clicked.connect(lambda: self.open_url(FACEBOOK))
        contact_card.body.addWidget(facebook)

        grid.addWidget(contact_card, 1, 0)

        support_card = SupportCard(
            "Wesprzyj rozwój",
            "Ta sekcja jest już przygotowana pod dobrowolne wsparcie projektu. "
            "Nie podpinam przypadkowego serwisu ani numeru rachunku bez Twojej decyzji.",
        )

        status = QLabel("Link wsparcia finansowego: jeszcze nie skonfigurowany")
        status.setWordWrap(True)
        status.setStyleSheet(
            f"color:{YELLOW};background:#071827;border:1px solid {YELLOW};"
            "border-radius:8px;padding:8px;font-size:8pt;font-weight:700;"
        )
        support_card.body.addWidget(status)

        later = QPushButton("Wesprzyj autora")
        later.setEnabled(False)
        later.setToolTip(
            "Przycisk włączymy po podaniu docelowego linku wsparcia, np. BuyCoffee, Patronite, GitHub Sponsors lub innego wybranego kanału."
        )
        support_card.body.addWidget(later)

        grid.addWidget(support_card, 1, 1)

        root.addLayout(grid)

        footer = QFrame()
        footer.setStyleSheet(
            f"background:#061522;border:1px solid {LINE};border-radius:11px;"
        )
        fv = QVBoxLayout(footer)
        fv.setContentsMargins(13, 10, 13, 10)
        fv.addWidget(label("Przydatne przy zgłoszeniu problemu", 9, TEXT, True))

        tips = label(
            "Napisz: co próbowałeś zrobić, nazwa modułu, co dokładnie się stało, "
            "czy problem da się powtórzyć oraz dołącz odpowiedni fragment logu. "
            "Nie wysyłaj haseł, tokenów ani prywatnych danych klienta.",
            8,
            "#a9bfd0",
        )
        tips.setWordWrap(True)
        fv.addWidget(tips)

        root.addWidget(footer)
        root.addStretch()

    def open_url(self, url):
        QDesktopServices.openUrl(QUrl(url))

    def open_logs(self):
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(LOGS_DIR)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(LOGS_DIR)))

    def copy_diagnostics(self):
        log_file = LOGS_DIR / "dashboard.log"

        text = (
            f"Prestige Tech Dashboard v{APP_VERSION}\n"
            f"System: {platform.system()} {platform.release()} {platform.version()}\n"
            f"Architektura: {platform.machine()}\n"
            f"Folder aplikacji: {APP_DIR}\n"
            f"Log: {log_file}\n"
            "\nOpis problemu:\n"
            "- Co próbowałem zrobić:\n"
            "- Moduł:\n"
            "- Co się stało:\n"
            "- Czy problem występuje ponownie:\n"
        )

        QApplication.clipboard().setText(text)
