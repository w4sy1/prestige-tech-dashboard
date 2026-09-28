from __future__ import annotations

from app_version import APP_VERSION, APP_TITLE
import platform
import sys

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QPushButton, QApplication
)

from .theme import *
from .widgets import label


GITHUB = "https://github.com/w4sy1"
REPO = "https://github.com/w4sy1/prestige-tech-dashboard"
INSTAGRAM = "https://www.instagram.com/projekt.ocalenie/"
FACEBOOK = "https://www.facebook.com/profile.php?viewas=100000686899395&id=61572604231491"


class InfoCard(QFrame):
    def __init__(self, title, value, description=""):
        super().__init__()
        self.setStyleSheet(
            f"QFrame{{background:{CARD};border:1px solid {LINE};border-radius:12px;}}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(4)
        root.addWidget(label(title, 8, "#8fb0c7", True))
        root.addWidget(label(value, 12, TEXT, True))
        if description:
            d = label(description, 8, "#9db6c8")
            d.setWordWrap(True)
            root.addWidget(d)


class AboutPage(QWidget):
    support_requested = Signal()

    def __init__(self, module_count=24):
        super().__init__()
        self.module_count = module_count

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 22)
        root.setSpacing(12)

        hero = QFrame()
        hero.setStyleSheet(
            f"background:#061522;border:1px solid {BLUE};border-radius:14px;"
        )
        hv = QVBoxLayout(hero)
        hv.setContentsMargins(22, 20, 22, 20)
        hv.setSpacing(6)

        hv.addWidget(label("PRESTIGE TECH", 24, CYAN, True))
        hv.addWidget(label("WIĘCEJ NIŻ TECHNOLOGIA", 13, TEXT, True))
        hv.addWidget(label("TECH SOLUTIONS  •  PEOPLE IMPACT", 9, "#72cfff", True))

        desc = label(
            "Prestige Tech Dashboard to jedno centrum do diagnostyki Windows, sieci, "
            "Androida, bezpieczeństwa, plików, raportów i narzędzi serwisowych.",
            10,
            "#b4c9d8",
        )
        desc.setWordWrap(True)
        hv.addWidget(desc)

        signature = QLabel("By Dominik Wasilak")
        signature.setAlignment(Qt.AlignRight)
        signature.setStyleSheet(
            "color:#c9d9e6;font-size:11pt;font-style:italic;padding-top:8px;"
        )
        hv.addWidget(signature)

        root.addWidget(hero)

        stats = QGridLayout()
        stats.setSpacing(10)
        stats.addWidget(InfoCard("WERSJA", APP_VERSION, "Aktualna wersja interfejsu Dashboardu."), 0, 0)
        stats.addWidget(InfoCard("MODUŁY", str(module_count), "Niezależne narzędzia Prestige Tech."), 0, 1)
        stats.addWidget(InfoCard("PYTHON", platform.python_version(), sys.executable), 0, 2)
        stats.addWidget(InfoCard("PYSIDE6", PYSIDE_VERSION, "Silnik graficzny interfejsu."), 0, 3)
        root.addLayout(stats)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        project = QFrame()
        project.setStyleSheet(
            f"background:{CARD};border:1px solid {LINE};border-radius:12px;"
        )
        pv = QVBoxLayout(project)
        pv.setContentsMargins(15, 13, 15, 13)
        pv.setSpacing(8)
        pv.addWidget(label("Projekt", 11, TEXT, True))

        text = label(
            "Dashboard został zaprojektowany jako modularna aplikacja. "
            "Każde narzędzie może być rozwijane i aktualizowane niezależnie, "
            "a użytkownik instaluje tylko to, czego potrzebuje.",
            9,
            "#a9bfd0",
        )
        text.setWordWrap(True)
        pv.addWidget(text)

        repo_btn = QPushButton("Repozytorium Dashboardu")
        repo_btn.clicked.connect(lambda: self.open_url(REPO))
        pv.addWidget(repo_btn)

        github_btn = QPushButton("Profil GitHub w4sy1")
        github_btn.clicked.connect(lambda: self.open_url(GITHUB))
        pv.addWidget(github_btn)

        grid.addWidget(project, 0, 0)

        social = QFrame()
        social.setStyleSheet(
            f"background:{CARD};border:1px solid {LINE};border-radius:12px;"
        )
        sv = QVBoxLayout(social)
        sv.setContentsMargins(15, 13, 15, 13)
        sv.setSpacing(8)
        sv.addWidget(label("Social i kontakt", 11, TEXT, True))

        instagram = QPushButton("Instagram  |  projekt.ocalenie")
        instagram.clicked.connect(lambda: self.open_url(INSTAGRAM))
        sv.addWidget(instagram)

        facebook = QPushButton("Facebook")
        facebook.clicked.connect(lambda: self.open_url(FACEBOOK))
        sv.addWidget(facebook)

        support = QPushButton("Wsparcie i kontakt")
        support.setProperty("primary", True)
        support.clicked.connect(self.support_requested.emit)
        sv.addWidget(support)

        grid.addWidget(social, 0, 1)

        root.addLayout(grid)

        system = QFrame()
        system.setStyleSheet(
            f"background:#071827;border:1px solid {LINE};border-radius:12px;"
        )
        sh = QHBoxLayout(system)
        sh.setContentsMargins(14, 11, 14, 11)

        system_text = (
            f"{platform.system()} {platform.release()} | "
            f"{platform.machine()} | Python {platform.python_version()} | "
            f"PySide6 {PYSIDE_VERSION}"
        )

        info = label(system_text, 8, "#a9bfd0")
        info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        sh.addWidget(info, 1)

        copy_btn = QPushButton("Kopiuj informacje")
        copy_btn.clicked.connect(self.copy_info)
        sh.addWidget(copy_btn)

        root.addWidget(system)
        root.addStretch()

    def open_url(self, url):
        QDesktopServices.openUrl(QUrl(url))

    def copy_info(self):
        text = (
            f"Prestige Tech Dashboard v{APP_VERSION}\n"
            f"System: {platform.system()} {platform.release()} {platform.version()}\n"
            f"Architektura: {platform.machine()}\n"
            f"Python: {platform.python_version()}\n"
            f"PySide6: {PYSIDE_VERSION}\n"
            f"Moduły: {self.module_count}"
        )
        QApplication.clipboard().setText(text)
