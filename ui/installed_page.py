from pathlib import Path
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QComboBox,
    QLabel, QFrame, QPushButton
)
from module_manager import MODULES_DIR
from .theme import *
from .widgets import ModuleCard, label

class SummaryTile(QFrame):
    def __init__(self, value, title, subtitle, color=BLUE):
        super().__init__()
        self.setFixedHeight(76)
        self.setStyleSheet(f"background:#061522;border:1px solid {LINE};border-radius:11px;")
        root = QVBoxLayout(self)
        root.setContentsMargins(13, 9, 13, 9)
        root.setSpacing(2)
        self.value = label(str(value), 15, color, True)
        root.addWidget(self.value)
        root.addWidget(label(title.upper(), 7, TEXT, True))
        root.addWidget(label(subtitle, 7, "#9fb6c8"))

class InstalledPage(QWidget):
    install_requested = Signal(object)
    run_requested = Signal(object)
    remove_requested = Signal(object)
    help_requested = Signal(object)
    icon_requested = Signal(object)

    def __init__(self, manager):
        super().__init__()
        self.mm = manager

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 22)
        root.setSpacing(11)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(label("Zainstalowane", 22, TEXT, True))
        titles.addWidget(label(
            "Moduły zainstalowane lokalnie i gotowe do uruchomienia.",
            9, "#aac0d1"
        ))
        header.addLayout(titles)
        header.addStretch()

        self.folder_btn = QPushButton("Otwórz folder modułów")
        self.folder_btn.clicked.connect(self.open_folder)
        header.addWidget(self.folder_btn)

        self.refresh_btn = QPushButton("Odśwież")
        self.refresh_btn.clicked.connect(self.render)
        header.addWidget(self.refresh_btn)

        root.addLayout(header)

        stats = QHBoxLayout()
        self.stat_installed = SummaryTile(0, "Zainstalowane", "Gotowe do uruchomienia", GREEN)
        self.stat_size = SummaryTile("0 MB", "Miejsce na dysku", "Folder modułów", CYAN)
        self.stat_categories = SummaryTile(0, "Kategorie", "Aktywne kategorie", BLUE)
        stats.addWidget(self.stat_installed)
        stats.addWidget(self.stat_size)
        stats.addWidget(self.stat_categories)
        root.addLayout(stats)

        info_box = QFrame()
        info_box.setStyleSheet(f"background:#071827;border:1px solid {LINE};border-radius:11px;")
        info = QHBoxLayout(info_box)
        info.setContentsMargins(12, 9, 12, 9)
        info.addWidget(label("Folder:", 8, "#9fb6c8", True))
        path_label = label(str(MODULES_DIR), 8, TEXT)
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info.addWidget(path_label, 1)
        root.addWidget(info_box)

        filter_box = QFrame()
        filter_box.setStyleSheet(f"background:#061522;border:1px solid {LINE};border-radius:11px;")
        filters = QHBoxLayout(filter_box)
        filters.setContentsMargins(11, 8, 11, 8)
        filters.setSpacing(9)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Szukaj w zainstalowanych modułach...")
        self.search.textChanged.connect(self.render)
        filters.addWidget(self.search, 1)

        self.category = QComboBox()
        self.category.addItems(["Wszystkie"] + self.mm.categories())
        self.category.currentTextChanged.connect(self.render)
        filters.addWidget(self.category)

        root.addWidget(filter_box)

        line = QHBoxLayout()
        self.count = QLabel()
        self.count.setStyleSheet("color:#a9bfd0;font-size:9pt;")
        line.addWidget(self.count)
        line.addStretch()
        line.addWidget(label("Uruchamianie odbywa się bez shell=True.", 8, "#7fa1b8"))
        root.addLayout(line)

        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        for col in range(3):
            self.grid.setColumnStretch(col, 1)
        root.addLayout(self.grid)
        root.addStretch()

        self.render()

    def open_folder(self):
        MODULES_DIR.mkdir(parents=True, exist_ok=True)
        import os
        if os.name == "nt":
            os.startfile(MODULES_DIR)

    def _installed_size(self):
        total = 0
        try:
            if MODULES_DIR.exists():
                for p in MODULES_DIR.rglob("*"):
                    if p.is_file():
                        try:
                            total += p.stat().st_size
                        except OSError:
                            pass
        except OSError:
            pass
        mb = total / (1024 * 1024)
        if mb < 1024:
            return f"{mb:.1f} MB"
        return f"{mb/1024:.2f} GB"

    def render(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        installed = [m for m in self.mm.modules if self.mm.is_installed(m)]
        self.stat_installed.value.setText(str(len(installed)))
        self.stat_size.value.setText(self._installed_size())
        self.stat_categories.value.setText(str(len({m.category for m in installed})))

        q = self.search.text().lower().strip()
        cat = self.category.currentText()

        items = []
        for m in installed:
            if cat != "Wszystkie" and m.category != cat:
                continue
            if q and q not in (m.name + " " + m.category + " " + m.description + " " + m.id).lower():
                continue
            items.append(m)

        self.count.setText(f"{len(items)} zainstalowanych modułów")

        if not installed:
            empty = QFrame()
            empty.setStyleSheet(
                f"background:#061522;border:1px dashed {LINE};border-radius:12px;"
            )
            box = QVBoxLayout(empty)
            box.setContentsMargins(28, 34, 28, 34)
            title = label("Brak zainstalowanych modułów", 13, TEXT, True)
            title.setAlignment(Qt.AlignCenter)
            box.addWidget(title)
            text = label(
                "Przejdź do sekcji Moduły i wybierz pojedyncze narzędzie albo użyj opcji Zainstaluj wszystkie.",
                9, "#a9bfd0"
            )
            text.setWordWrap(True)
            text.setAlignment(Qt.AlignCenter)
            box.addWidget(text)
            self.grid.addWidget(empty, 0, 0, 1, 3)
            return

        if not items:
            empty = QLabel("Brak zainstalowanych modułów pasujących do filtrów.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                f"color:#a9bfd0;background:#061522;border:1px dashed {LINE};"
                "border-radius:12px;padding:28px;font-size:10pt;"
            )
            self.grid.addWidget(empty, 0, 0, 1, 3)
            return

        for i, m in enumerate(items):
            card = ModuleCard(
                m,
                self.mm,
                installed=True,
                portable=False,
                portable_available=False,
            )
            card.install_requested.connect(self.install_requested.emit)
            card.run_requested.connect(self.run_requested.emit)
            card.remove_requested.connect(self.remove_requested.emit)
            card.help_requested.connect(self.help_requested.emit)
            card.icon_requested.connect(self.icon_requested.emit)
            self.grid.addWidget(card, i // 3, i % 3)

