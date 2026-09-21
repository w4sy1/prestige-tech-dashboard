from __future__ import annotations

import ctypes
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QPushButton,
    QMessageBox
)

from module_manager import APP_DIR, MODULES_DIR, LOGS_DIR
from .theme import *
from .widgets import label


def _is_admin():
    if os.name != "nt":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _find_executable(names, extras=()):
    for name in names:
        p = shutil.which(name)
        if p:
            return Path(p)

    for raw in extras:
        p = Path(os.path.expandvars(str(raw)))
        if p.is_file():
            return p

    return None


def _internet_ok():
    from .release_client import internet_probe
    ok, _detail = internet_probe()
    return ok



def _folder_size(path):
    total = 0
    try:
        if Path(path).exists():
            for p in Path(path).rglob("*"):
                if p.is_file():
                    try:
                        total += p.stat().st_size
                    except OSError:
                        pass
    except OSError:
        pass
    return total


def _format_size(value):
    mb = value / (1024 * 1024)
    if mb < 1024:
        return f"{mb:.1f} MB"
    return f"{mb / 1024:.2f} GB"


class StatusCard(QFrame):
    def __init__(self, title, value, status="ok", detail="", action_text=None, action=None):
        super().__init__()

        colors = {
            "ok": GREEN,
            "warn": YELLOW,
            "bad": "#ff7b88",
            "info": CYAN,
        }
        color = colors.get(status, MUTED)

        self.setStyleSheet(
            f"QFrame{{background:{CARD};border:1px solid {LINE};border-radius:12px;}}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(15, 13, 15, 13)
        root.setSpacing(6)

        head = QHBoxLayout()
        head.addWidget(label(title, 10, TEXT, True))
        head.addStretch()

        badge = QLabel("● " + value)
        badge.setStyleSheet(
            f"color:{color};background:#071827;border:1px solid {color};"
            "border-radius:8px;padding:5px 8px;font-size:8pt;font-weight:700;"
        )
        head.addWidget(badge)
        root.addLayout(head)

        if detail:
            d = label(detail, 8, "#a9bfd0")
            d.setWordWrap(True)
            root.addWidget(d)

        if action_text and action:
            row = QHBoxLayout()
            row.addStretch()
            b = QPushButton(action_text)
            b.clicked.connect(action)
            row.addWidget(b)
            root.addLayout(row)


class SystemToolsPage(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.mm = manager

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 22)
        root.setSpacing(11)

        header = QHBoxLayout()

        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(label("Narzędzia systemowe", 22, TEXT, True))
        titles.addWidget(
            label(
                "Stan Windows, uprawnienia i zależności wymagane przez moduły Prestige Tech.",
                9,
                "#aac0d1",
            )
        )
        header.addLayout(titles)
        header.addStretch()

        refresh = QPushButton("Sprawdź ponownie")
        refresh.clicked.connect(self.render)
        header.addWidget(refresh)

        root.addLayout(header)

        self.summary = QFrame()
        self.summary.setStyleSheet(
            f"background:#071827;border:1px solid {LINE};border-radius:11px;"
        )
        sv = QHBoxLayout(self.summary)
        sv.setContentsMargins(13, 10, 13, 10)

        self.summary_icon = QLabel("●")
        self.summary_icon.setStyleSheet(
            f"color:{GREEN};font-size:16pt;font-weight:800;"
        )
        sv.addWidget(self.summary_icon)

        self.summary_text = label("", 9, TEXT, True)
        sv.addWidget(self.summary_text)

        sv.addStretch()

        open_app = QPushButton("Folder aplikacji")
        open_app.clicked.connect(lambda: self.open_folder(APP_DIR))
        sv.addWidget(open_app)

        open_logs = QPushButton("Logi")
        open_logs.clicked.connect(lambda: self.open_folder(LOGS_DIR))
        sv.addWidget(open_logs)

        root.addWidget(self.summary)

        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        self.grid.setColumnStretch(2, 1)
        root.addLayout(self.grid)

        note = QFrame()
        note.setStyleSheet(
            f"background:#061522;border:1px solid {LINE};border-radius:11px;"
        )
        nv = QVBoxLayout(note)
        nv.setContentsMargins(13, 10, 13, 10)
        nv.addWidget(label("Co oznaczają statusy?", 9, TEXT, True))

        tx = label(
            "Zielony oznacza gotowość. Żółty oznacza, że część funkcji może wymagać dodatkowego programu "
            "lub uruchomienia jako administrator. Czerwony oznacza brak wymaganej zależności dla części modułów.",
            8,
            "#a9bfd0",
        )
        tx.setWordWrap(True)
        nv.addWidget(tx)
        root.addWidget(note)

        root.addStretch()

        self.render()

    def open_folder(self, path):
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)

        try:
            if os.name == "nt":
                os.startfile(p)
            else:
                subprocess.Popen(["xdg-open", str(p)])
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Błąd",
                f"Nie udało się otworzyć folderu:\n{p}\n\n{exc}",
            )

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def render(self):
        self._clear_grid()

        windows_ok = os.name == "nt"
        admin = _is_admin()
        internet = _internet_ok()

        adb = _find_executable(
            ("adb.exe", "adb"),
            (
                r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe",
                r"%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe",
            ),
        )

        nmap = _find_executable(
            ("nmap.exe", "nmap"),
            (
                r"%ProgramFiles(x86)%\Nmap\nmap.exe",
                r"%ProgramFiles%\Nmap\nmap.exe",
            ),
        )

        git = _find_executable(("git.exe", "git"))
        powershell = _find_executable(("pwsh.exe", "powershell.exe", "powershell"))

        installed_count = sum(
            1 for m in self.mm.modules if self.mm.is_installed(m)
        )

        rows = [
            (
                "Windows",
                "Gotowy" if windows_ok else "Nieobsługiwany",
                "ok" if windows_ok else "bad",
                f"{platform.system()} {platform.release()} | {platform.version()}",
            ),
            (
                "Uprawnienia administratora",
                "Administrator" if admin else "Tryb standardowy",
                "ok" if admin else "warn",
                "Większość funkcji działa bez administratora. Operacje systemowe mogą wymagać podniesienia uprawnień.",
            ),
            (
                "Internet",
                "Połączono" if internet else "Brak połączenia",
                "ok" if internet else "warn",
                "Test DNS i połączenia TCP/443. Nie używa portu DNS 53 jako jedynego kryterium.",
            ),
            (
                "ADB",
                "Wykryto" if adb else "Brak",
                "ok" if adb else "warn",
                str(adb) if adb else "Wymagane przez moduły Android i ADB.",
            ),
            (
                "Nmap",
                "Wykryto" if nmap else "Brak",
                "ok" if nmap else "warn",
                str(nmap) if nmap else "Wymagany przez profile Nmap i część diagnostyki sieci.",
            ),
            (
                "Git",
                "Wykryto" if git else "Brak",
                "ok" if git else "info",
                str(git) if git else "Nie jest wymagany do zwykłego używania Dashboardu.",
            ),
            (
                "PowerShell",
                "Wykryto" if powershell else "Brak",
                "ok" if powershell else "warn",
                str(powershell) if powershell else "Część narzędzi Windows może go wymagać.",
            ),
            (
                "Python",
                "Aktywny",
                "ok",
                f"{platform.python_version()} | {sys.executable}",
            ),
            (
                "Moduły Prestige Tech",
                f"{installed_count}/{len(self.mm.modules)}",
                "ok" if installed_count == len(self.mm.modules) else "info",
                f"Folder: {MODULES_DIR} | Rozmiar: {_format_size(_folder_size(MODULES_DIR))}",
            ),
        ]

        issues = 0

        for index, row in enumerate(rows):
            title, value, status, detail = row

            if status in ("warn", "bad"):
                issues += 1

            action_text = None
            action = None

            if title == "Moduły Prestige Tech":
                action_text = "Otwórz folder"
                action = lambda p=MODULES_DIR: self.open_folder(p)

            card = StatusCard(
                title,
                value,
                status=status,
                detail=detail,
                action_text=action_text,
                action=action,
            )
            self.grid.addWidget(card, index // 3, index % 3)

        if issues == 0:
            self.summary_icon.setStyleSheet(
                f"color:{GREEN};font-size:16pt;font-weight:800;"
            )
            self.summary_text.setText(
                "System gotowy. Nie wykryto problemów z podstawowymi zależnościami."
            )
        else:
            self.summary_icon.setStyleSheet(
                f"color:{YELLOW};font-size:16pt;font-weight:800;"
            )
            self.summary_text.setText(
                f"System działa. Wykryto {issues} elementów wymagających uwagi."
            )

