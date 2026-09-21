from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QComboBox, QMessageBox
)

from module_manager import APP_DIR
from .theme import *
from .widgets import label

REPORTS_DIR = APP_DIR / "reports"

REPORT_EXTENSIONS = {
    ".pdf": "PDF",
    ".txt": "Tekst",
    ".json": "JSON",
    ".csv": "CSV",
    ".html": "HTML",
    ".htm": "HTML",
    ".log": "Log",
    ".md": "Markdown",
}


def _format_size(value):
    if value < 1024:
        return f"{value} B"
    kb = value / 1024
    if kb < 1024:
        return f"{kb:.1f} KB"
    mb = kb / 1024
    if mb < 1024:
        return f"{mb:.1f} MB"
    return f"{mb / 1024:.2f} GB"


def _format_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y  %H:%M")


class StatTile(QFrame):
    def __init__(self, value, title, color=BLUE):
        super().__init__()
        self.setFixedHeight(64)
        self.setStyleSheet(
            f"background:#061522;border:1px solid {LINE};border-radius:10px;"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)

        self.value = label(str(value), 15, color, True)
        row.addWidget(self.value)
        row.addWidget(label(title.upper(), 7, "#a9bfd0", True))
        row.addStretch()


class ReportCard(QFrame):
    def __init__(self, page, path):
        super().__init__()
        self.page = page
        self.path = path

        self.setStyleSheet(
            f"QFrame{{background:{CARD};border:1px solid {LINE};border-radius:12px;}}"
            f"QFrame:hover{{border:1px solid {BLUE};}}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(15, 13, 15, 13)
        root.setSpacing(7)

        ext = path.suffix.lower()
        kind = REPORT_EXTENSIONS.get(ext, ext.lstrip(".").upper() or "Plik")

        top = QHBoxLayout()
        top.addWidget(label(path.name, 10, TEXT, True))
        top.addStretch()

        badge = QLabel(kind)
        badge.setStyleSheet(
            f"color:{CYAN};background:#071827;border:1px solid {LINE};"
            "border-radius:8px;padding:4px 7px;font-size:7pt;font-weight:700;"
        )
        top.addWidget(badge)
        root.addLayout(top)

        try:
            stat = path.stat()
            size = _format_size(stat.st_size)
            modified = _format_time(stat.st_mtime)
        except OSError:
            size = "?"
            modified = "?"

        root.addWidget(label(f"Zmodyfikowano: {modified}", 8, "#a9bfd0"))
        root.addWidget(label(f"Rozmiar: {size}", 8, "#a9bfd0"))

        location = label(str(path.parent), 7, "#7694aa")
        location.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(location)

        root.addStretch()

        actions = QHBoxLayout()

        open_btn = QPushButton("Otwórz")
        open_btn.setProperty("primary", True)
        open_btn.clicked.connect(lambda: page.open_file(path))
        actions.addWidget(open_btn)

        folder_btn = QPushButton("Pokaż w folderze")
        folder_btn.clicked.connect(lambda: page.show_in_folder(path))
        actions.addWidget(folder_btn)

        actions.addStretch()

        delete_btn = QPushButton("Usuń")
        delete_btn.clicked.connect(lambda: page.delete_file(path))
        actions.addWidget(delete_btn)

        root.addLayout(actions)


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 22)
        root.setSpacing(11)

        header = QHBoxLayout()

        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(label("Raporty", 22, TEXT, True))
        titles.addWidget(
            label(
                "Raporty, wyniki diagnostyki i pliki wygenerowane przez narzędzia Prestige Tech.",
                9,
                "#aac0d1",
            )
        )
        header.addLayout(titles)
        header.addStretch()

        folder_btn = QPushButton("Otwórz folder raportów")
        folder_btn.clicked.connect(lambda: self.open_folder(REPORTS_DIR))
        header.addWidget(folder_btn)

        refresh_btn = QPushButton("Odśwież")
        refresh_btn.clicked.connect(self.render)
        header.addWidget(refresh_btn)

        root.addLayout(header)

        stats = QHBoxLayout()
        self.stat_count = StatTile(0, "Raporty", BLUE)
        self.stat_size = StatTile("0 MB", "Łączny rozmiar", CYAN)
        self.stat_newest = StatTile("-", "Najnowszy", GREEN)

        stats.addWidget(self.stat_count)
        stats.addWidget(self.stat_size)
        stats.addWidget(self.stat_newest)
        root.addLayout(stats)

        info_box = QFrame()
        info_box.setStyleSheet(
            f"background:#071827;border:1px solid {LINE};border-radius:11px;"
        )

        info = QHBoxLayout(info_box)
        info.setContentsMargins(12, 9, 12, 9)
        info.addWidget(label("Folder:", 8, "#9fb6c8", True))

        path_label = label(str(REPORTS_DIR), 8, TEXT)
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info.addWidget(path_label, 1)

        root.addWidget(info_box)

        filter_box = QFrame()
        filter_box.setStyleSheet(
            f"background:#061522;border:1px solid {LINE};border-radius:11px;"
        )

        filters = QHBoxLayout(filter_box)
        filters.setContentsMargins(11, 8, 11, 8)
        filters.setSpacing(9)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Szukaj raportu po nazwie...")
        self.search.textChanged.connect(self.render)
        filters.addWidget(self.search, 1)

        self.type_filter = QComboBox()
        self.type_filter.addItems(
            [
                "Wszystkie typy",
                "PDF",
                "Tekst",
                "JSON",
                "CSV",
                "HTML",
                "Log",
                "Markdown",
                "Inne",
            ]
        )
        self.type_filter.currentTextChanged.connect(self.render)
        filters.addWidget(self.type_filter)

        self.sort_filter = QComboBox()
        self.sort_filter.addItems(
            [
                "Najnowsze najpierw",
                "Najstarsze najpierw",
                "Nazwa A-Z",
                "Nazwa Z-A",
                "Największe najpierw",
            ]
        )
        self.sort_filter.currentTextChanged.connect(self.render)
        filters.addWidget(self.sort_filter)

        root.addWidget(filter_box)

        line = QHBoxLayout()
        self.count_label = QLabel()
        self.count_label.setStyleSheet("color:#a9bfd0;font-size:9pt;")
        line.addWidget(self.count_label)
        line.addStretch()
        root.addLayout(line)

        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        root.addLayout(self.grid)

        root.addStretch()

        self.render()

    def _all_files(self):
        try:
            files = [p for p in REPORTS_DIR.rglob("*") if p.is_file()]
        except OSError:
            files = []
        return files

    def _type_name(self, path):
        return REPORT_EXTENSIONS.get(
            path.suffix.lower(),
            "Inne",
        )

    def _total_size(self, files):
        total = 0
        for path in files:
            try:
                total += path.stat().st_size
            except OSError:
                pass
        return total

    def open_folder(self, path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(path))
        )

    def open_file(self, path):
        if not Path(path).is_file():
            QMessageBox.warning(
                self,
                "Brak pliku",
                "Ten raport już nie istnieje.",
            )
            self.render()
            return

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(path))
        )

    def show_in_folder(self, path):
        path = Path(path)

        if not path.exists():
            QMessageBox.warning(
                self,
                "Brak pliku",
                "Ten raport już nie istnieje.",
            )
            self.render()
            return

        self.open_folder(path.parent)

    def delete_file(self, path):
        path = Path(path)

        answer = QMessageBox.warning(
            self,
            "Usuń raport",
            f"Usunąć raport?\n\n{path.name}\n\nTej operacji nie można cofnąć.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            path.unlink()
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Błąd usuwania",
                str(exc),
            )
            return

        self.render()

    def render(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        all_files = self._all_files()

        self.stat_count.value.setText(
            str(len(all_files))
        )

        self.stat_size.value.setText(
            _format_size(
                self._total_size(all_files)
            )
        )

        if all_files:
            try:
                newest = max(
                    all_files,
                    key=lambda p: p.stat().st_mtime,
                )
                self.stat_newest.value.setText(
                    datetime.fromtimestamp(
                        newest.stat().st_mtime
                    ).strftime("%d.%m %H:%M")
                )
            except OSError:
                self.stat_newest.value.setText("?")
        else:
            self.stat_newest.value.setText("-")

        query = self.search.text().lower().strip()
        type_filter = self.type_filter.currentText()

        files = []

        for path in all_files:
            if query and query not in path.name.lower():
                continue

            if (
                type_filter != "Wszystkie typy"
                and self._type_name(path) != type_filter
            ):
                continue

            files.append(path)

        sort_mode = self.sort_filter.currentText()

        def stat_value(path, attr, default=0):
            try:
                return getattr(path.stat(), attr)
            except OSError:
                return default

        if sort_mode == "Najnowsze najpierw":
            files.sort(
                key=lambda p: stat_value(p, "st_mtime"),
                reverse=True,
            )
        elif sort_mode == "Najstarsze najpierw":
            files.sort(
                key=lambda p: stat_value(p, "st_mtime"),
            )
        elif sort_mode == "Nazwa A-Z":
            files.sort(
                key=lambda p: p.name.lower(),
            )
        elif sort_mode == "Nazwa Z-A":
            files.sort(
                key=lambda p: p.name.lower(),
                reverse=True,
            )
        elif sort_mode == "Największe najpierw":
            files.sort(
                key=lambda p: stat_value(p, "st_size"),
                reverse=True,
            )

        self.count_label.setText(
            f"{len(files)} raportów"
        )

        if not all_files:
            empty = QFrame()
            empty.setStyleSheet(
                f"background:#061522;border:1px dashed {LINE};border-radius:12px;"
            )

            box = QVBoxLayout(empty)
            box.setContentsMargins(28, 34, 28, 34)

            title = label(
                "Brak raportów",
                13,
                TEXT,
                True,
            )
            title.setAlignment(Qt.AlignCenter)
            box.addWidget(title)

            text = label(
                "Gdy moduły Prestige Tech zaczną zapisywać raporty, pojawią się tutaj automatycznie.",
                9,
                "#a9bfd0",
            )
            text.setWordWrap(True)
            text.setAlignment(Qt.AlignCenter)
            box.addWidget(text)

            self.grid.addWidget(
                empty,
                0,
                0,
                1,
                2,
            )
            return

        if not files:
            empty = QLabel(
                "Brak raportów pasujących do wybranych filtrów."
            )
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                f"color:#a9bfd0;background:#061522;border:1px dashed {LINE};"
                "border-radius:12px;padding:28px;font-size:10pt;"
            )
            self.grid.addWidget(
                empty,
                0,
                0,
                1,
                2,
            )
            return

        for index, path in enumerate(files):
            self.grid.addWidget(
                ReportCard(
                    self,
                    path,
                ),
                index // 2,
                index % 2,
            )

