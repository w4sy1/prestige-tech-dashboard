from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QPushButton, QMessageBox, QProgressBar
)

from module_manager import APP_DIR, MODULES_DIR
from .theme import *
from .widgets import label
from .widgets import ModuleIcon
from .release_client import (
    ReleaseClient,
    ReleaseError,
    compare_versions,
)
from .settings_store import load_settings


DOWNLOAD_DIR = APP_DIR / "downloads"


def installed_version(module):
    folder = MODULES_DIR / module.id

    candidates = (
        folder / "version.txt",
        folder / "VERSION",
    )

    for path in candidates:
        if not path.is_file():
            continue

        try:
            value = path.read_text(encoding="utf-8-sig").strip()

            if value:
                return value
        except OSError:
            pass

    return None


class ManifestThread(QThread):
    success = Signal(object)
    failed = Signal(str)

    def run(self):
        try:
            manifest = ReleaseClient().fetch_manifest()
            self.success.emit(manifest)
        except Exception as exc:
            self.failed.emit(str(exc))


class InstallThread(QThread):
    progress_changed = Signal(int)
    success = Signal(object, str)
    failed = Signal(object, str)

    def __init__(self, manager, module, entry):
        super().__init__()
        self.manager = manager
        self.module = module
        self.entry = dict(entry)

    def run(self):
        version = str(self.entry.get("version") or "").strip()

        if not version:
            self.failed.emit(
                self.module,
                "Manifest nie zawiera numeru wersji.",
            )
            return

        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        target = DOWNLOAD_DIR / self.module.executable

        try:
            ReleaseClient().download_verified(
                self.entry,
                target,
                progress=self.progress_changed.emit,
            )

            self.manager.install_file(
                self.module,
                target,
            )

            module_dir = MODULES_DIR / self.module.id
            module_dir.mkdir(parents=True, exist_ok=True)

            (module_dir / "version.txt").write_text(
                version,
                encoding="utf-8",
            )

            try:
                target.unlink()
            except OSError:
                pass

            self.success.emit(
                self.module,
                version,
            )

        except Exception as exc:
            self.failed.emit(
                self.module,
                str(exc),
            )


class StatTile(QFrame):
    def __init__(self, value, title, color):
        super().__init__()
        self.setFixedHeight(76)
        self.setStyleSheet(
            f"background:#061522;border:1px solid {LINE};border-radius:10px;"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(13, 9, 13, 9)

        self.value = label(
            str(value),
            16,
            color,
            True,
        )
        row.addWidget(self.value)
        row.addWidget(
            label(
                title.upper(),
                7,
                "#a9bfd0",
                True,
            )
        )
        row.addStretch()


class UpdateCard(QFrame):
    update_clicked = Signal(object)

    def __init__(self, module, manager):
        super().__init__()
        self.module = module
        self.manager = manager
        self.entry = None

        self.setStyleSheet(
            f"QFrame{{background:{CARD};border:1px solid {LINE};border-radius:12px;}}"
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(14, 11, 14, 11)
        root.setSpacing(12)

        root.addWidget(
            ModuleIcon(
                module,
                manager,
                54,
            )
        )

        text = QVBoxLayout()
        text.setSpacing(3)

        text.addWidget(
            label(
                module.name,
                10,
                TEXT,
                True,
            )
        )

        text.addWidget(
            label(
                module.category.upper(),
                7,
                CYAN,
                True,
            )
        )

        self.state = label(
            "Oczekiwanie na manifest...",
            9,
            "#a9bfd0",
            True,
        )
        text.addWidget(self.state)

        self.versions = label(
            "",
            8,
            "#a9bfd0",
        )
        text.addWidget(self.versions)

        self.changelog = label(
            "",
            7,
            "#7694aa",
        )
        self.changelog.setWordWrap(True)
        text.addWidget(self.changelog)

        root.addLayout(
            text,
            1,
        )

        self.update_btn = QPushButton(
            "Aktualizuj"
        )
        self.update_btn.setProperty(
            "primary",
            True,
        )
        self.update_btn.setVisible(False)
        self.update_btn.clicked.connect(
            lambda: self.update_clicked.emit(self.module)
        )
        root.addWidget(self.update_btn)

    def set_status(self, local, entry, remote_available):
        self.entry = entry

        if not local:
            self.state.setText("Nieznana wersja lokalna")
            self.state.setStyleSheet(
                f"color:{YELLOW};font-weight:700;"
            )
            self.versions.setText(
                "Brak version.txt"
            )
            self.update_btn.setVisible(False)
            return "unknown"

        if not remote_available or not entry:
            self.state.setText("Stan lokalny")
            self.state.setStyleSheet(
                f"color:{CYAN};font-weight:700;"
            )
            self.versions.setText(
                f"Zainstalowana: v{local}"
            )
            self.update_btn.setVisible(False)
            return "local"

        remote = str(
            entry.get("version") or ""
        ).strip()

        if not remote:
            self.state.setText("Brak wersji w manifeście")
            self.state.setStyleSheet(
                f"color:{YELLOW};font-weight:700;"
            )
            self.versions.setText(
                f"Zainstalowana: v{local}"
            )
            self.update_btn.setVisible(False)
            return "unknown"

        result = compare_versions(
            local,
            remote,
        )

        self.versions.setText(
            f"Zainstalowana: v{local}   GitHub: v{remote}"
        )

        changelog = str(
            entry.get("changelog") or ""
        ).strip()

        self.changelog.setText(
            changelog[:180]
        )

        if result < 0:
            self.state.setText(
                "Dostępna aktualizacja"
            )
            self.state.setStyleSheet(
                f"color:{YELLOW};font-weight:700;"
            )
            self.update_btn.setVisible(True)
            return "update"

        if result == 0:
            self.state.setText(
                "Aktualna wersja"
            )
            self.state.setStyleSheet(
                f"color:{GREEN};font-weight:700;"
            )
            self.update_btn.setVisible(False)
            return "current"

        self.state.setText(
            "Wersja lokalna jest nowsza"
        )
        self.state.setStyleSheet(
            f"color:{CYAN};font-weight:700;"
        )
        self.update_btn.setVisible(False)
        return "ahead"


class UpdatesPage(QWidget):
    update_requested = Signal(object)

    def __init__(self, manager):
        super().__init__()
        self.mm = manager
        self.manifest = None
        self.cards = {}
        self.manifest_thread = None
        self.install_thread = None
        self.current_channel = "Stable"

        root = QVBoxLayout(self)
        root.setContentsMargins(
            26,
            20,
            26,
            22,
        )
        root.setSpacing(11)

        header = QHBoxLayout()

        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(
            label(
                "Aktualizacje",
                22,
                TEXT,
                True,
            )
        )

        self.subtitle = label(
            "GitHub Releases + manifest + SHA-256. Bez fikcyjnych liczników.",
            9,
            "#aac0d1",
        )
        titles.addWidget(
            self.subtitle
        )

        header.addLayout(
            titles
        )
        header.addStretch()

        self.channel_badge = QLabel()
        self.channel_badge.setStyleSheet(
            f"color:{CYAN};background:#071827;border:1px solid {LINE};"
            "border-radius:8px;padding:7px 9px;font-size:8pt;font-weight:700;"
        )
        header.addWidget(
            self.channel_badge
        )

        self.refresh_btn = QPushButton(
            "Sprawdź GitHub"
        )
        self.refresh_btn.clicked.connect(
            self.check_remote
        )
        header.addWidget(
            self.refresh_btn
        )

        root.addLayout(
            header
        )

        stats = QHBoxLayout()

        self.stat_updates = StatTile(
            0,
            "Dostępne",
            YELLOW,
        )
        self.stat_current = StatTile(
            0,
            "Aktualne",
            GREEN,
        )
        self.stat_unknown = StatTile(
            0,
            "Nieznana wersja",
            "#ff9e59",
        )

        stats.addWidget(
            self.stat_updates
        )
        stats.addWidget(
            self.stat_current
        )
        stats.addWidget(
            self.stat_unknown
        )

        root.addLayout(
            stats
        )

        self.remote_box = QFrame()
        self.remote_box.setStyleSheet(
            f"background:#071827;border:1px solid {LINE};border-radius:11px;"
        )

        rb = QHBoxLayout(
            self.remote_box
        )
        rb.setContentsMargins(
            13,
            10,
            13,
            10,
        )

        self.remote_status = label(
            "Jeszcze nie sprawdzono GitHub.",
            9,
            "#a9bfd0",
            True,
        )
        rb.addWidget(
            self.remote_status,
            1,
        )

        self.progress = QProgressBar()
        self.progress.setFixedWidth(220)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        rb.addWidget(
            self.progress
        )

        root.addWidget(
            self.remote_box
        )

        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)

        root.addLayout(
            self.grid
        )
        root.addStretch()

        self.render()

    def render(self):
        self.current_channel = load_settings().get(
            "channel",
            "Stable",
        )

        self.channel_badge.setText(
            "Kanał: " + self.current_channel
        )

        while self.grid.count():
            item = self.grid.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

        self.cards = {}

        installed = [
            module
            for module in self.mm.modules
            if self.mm.is_installed(module)
        ]

        counts = {
            "update": 0,
            "current": 0,
            "unknown": 0,
            "local": 0,
            "ahead": 0,
        }

        client = ReleaseClient()

        for index, module in enumerate(installed):
            card = UpdateCard(
                module,
                self.mm,
            )
            card.update_clicked.connect(
                self.start_update
            )

            self.cards[module.id] = card

            local = installed_version(
                module
            )

            entry = None

            if self.manifest:
                entry = client.module_entry(
                    self.manifest,
                    module.id,
                    self.current_channel,
                )

            state = card.set_status(
                local,
                entry,
                self.manifest is not None,
            )

            counts[state] = (
                counts.get(state, 0) + 1
            )

            self.grid.addWidget(
                card,
                index // 2,
                index % 2,
            )

        self.stat_updates.value.setText(
            str(counts["update"])
        )

        self.stat_current.value.setText(
            str(counts["current"])
        )

        self.stat_unknown.value.setText(
            str(counts["unknown"])
        )

    def check_remote(self):
        if self.manifest_thread and self.manifest_thread.isRunning():
            return

        self.refresh_btn.setEnabled(False)
        self.remote_status.setText(
            "Łączenie z repozytorium w4sy1/prestige-tech..."
        )
        self.remote_status.setStyleSheet(
            f"color:{CYAN};font-weight:700;"
        )

        self.manifest_thread = ManifestThread()
        self.manifest_thread.success.connect(
            self.manifest_ok
        )
        self.manifest_thread.failed.connect(
            self.manifest_failed
        )
        self.manifest_thread.finished.connect(
            lambda: self.refresh_btn.setEnabled(True)
        )
        self.manifest_thread.start()

    def manifest_ok(self, manifest):
        self.manifest = manifest

        generated = str(
            manifest.get("generated_at") or ""
        ).strip()

        suffix = (
            f" | Manifest: {generated}"
            if generated
            else ""
        )

        self.remote_status.setText(
            "GitHub dostępny. Manifest został zweryfikowany"
            + suffix
        )
        self.remote_status.setStyleSheet(
            f"color:{GREEN};font-weight:700;"
        )

        self.render()

    def manifest_failed(self, message):
        self.manifest = None

        self.remote_status.setText(
            "Aktualizacje online niedostępne: "
            + message
        )
        self.remote_status.setStyleSheet(
            f"color:{YELLOW};font-weight:700;"
        )

        self.render()

    def start_update(self, module):
        card = self.cards.get(
            module.id
        )

        if not card or not card.entry:
            return

        entry = dict(
            card.entry
        )

        remote = str(
            entry.get("version") or "?"
        )

        answer = QMessageBox.question(
            self,
            "Aktualizacja modułu",
            f"Zaktualizować {module.name} do wersji {remote}?\n\n"
            "Plik zostanie pobrany przez HTTPS, sprawdzony SHA-256 "
            "i dopiero wtedy zainstalowany.",
        )

        if answer != QMessageBox.Yes:
            return

        if self.install_thread and self.install_thread.isRunning():
            QMessageBox.information(
                self,
                "Aktualizacja",
                "Inna aktualizacja jest już w toku.",
            )
            return

        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.refresh_btn.setEnabled(False)

        self.remote_status.setText(
            "Pobieranie i weryfikacja: "
            + module.name
        )
        self.remote_status.setStyleSheet(
            f"color:{CYAN};font-weight:700;"
        )

        self.install_thread = InstallThread(
            self.mm,
            module,
            entry,
        )

        self.install_thread.progress_changed.connect(
            self.update_progress
        )
        self.install_thread.success.connect(
            self.install_ok
        )
        self.install_thread.failed.connect(
            self.install_failed
        )
        self.install_thread.finished.connect(
            lambda: self.refresh_btn.setEnabled(True)
        )

        self.install_thread.start()

    def update_progress(self, value):
        if value < 0:
            self.progress.setRange(0, 0)
            return

        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)

        self.progress.setValue(
            value
        )

    def install_ok(self, module, version):
        self.progress.setVisible(False)

        self.remote_status.setText(
            f"Zaktualizowano {module.name} do v{version}. SHA-256 zgodny."
        )
        self.remote_status.setStyleSheet(
            f"color:{GREEN};font-weight:700;"
        )

        self.render()

        QMessageBox.information(
            self,
            "Aktualizacja zakończona",
            f"{module.name}\n\n"
            f"Nowa wersja: {version}\n"
            "Weryfikacja SHA-256: OK",
        )

    def install_failed(self, module, message):
        self.progress.setVisible(False)

        self.remote_status.setText(
            f"Nie zaktualizowano {module.name}: {message}"
        )
        self.remote_status.setStyleSheet(
            f"color:{YELLOW};font-weight:700;"
        )

        QMessageBox.critical(
            self,
            "Aktualizacja przerwana",
            message,
        )
