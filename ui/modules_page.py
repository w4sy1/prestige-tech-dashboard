from pathlib import Path
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QComboBox,
    QLabel, QFrame
)
from .theme import *
from .widgets import ModuleCard, label

class ActionTile(QFrame):
    clicked = Signal()

    def __init__(self, title, subtitle, symbol, accent=BLUE, checkable=False):
        super().__init__()
        self.checkable = checkable
        self.checked = False
        self.accent = accent
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(76)
        self.setStyleSheet(
            f"QFrame{{background:#071827;border:1px solid {LINE};border-radius:11px;}}"
            f"QFrame:hover{{border:1px solid {accent};background:#0a2135;}}"
        )
        root = QHBoxLayout(self)
        root.setContentsMargins(14, 9, 14, 9)

        icon = QLabel(symbol)
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(42, 42)
        icon.setStyleSheet(
            f"background:#0b2237;color:{accent};border:1px solid {accent};"
            "border-radius:10px;font-size:15pt;font-weight:800;"
        )
        root.addWidget(icon)

        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(label(title, 9, TEXT, True))
        self.subtitle = label(subtitle, 8, "#a9bfd0")
        text.addWidget(self.subtitle)
        root.addLayout(text, 1)

    def set_checked(self, checked):
        self.checked = bool(checked)
        if self.checkable:
            self.subtitle.setText("Tryb włączony" if checked else "Tryb wyłączony")
            self.setStyleSheet(
                f"QFrame{{background:{'#0a2a2d' if checked else '#071827'};"
                f"border:1px solid {GREEN if checked else LINE};border-radius:11px;}}"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class StatTile(QFrame):
    def __init__(self, number, title, color=BLUE):
        super().__init__()
        self.setFixedHeight(58)
        self.setStyleSheet(f"background:#061522;border:1px solid {LINE};border-radius:10px;")
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 7, 12, 7)
        self.number = label(str(number), 15, color, True)
        root.addWidget(self.number)
        root.addWidget(label(title.upper(), 7, "#a9bfd0", True))
        root.addStretch()

class ModulesPage(QWidget):
    install_requested = Signal(object)
    run_requested = Signal(object)
    remove_requested = Signal(object)
    help_requested = Signal(object)
    icon_requested = Signal(object)
    install_all_requested = Signal()
    uninstall_all_requested = Signal()
    portable_changed = Signal(bool)

    def __init__(self, manager, installed_only=False):
        super().__init__()
        self.mm = manager
        self.installed_only = installed_only
        self.portable = False

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 22)
        root.setSpacing(10)

        head = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(label("Zainstalowane" if installed_only else "Moduły", 22, TEXT, True))
        titles.addWidget(label(
            "Gotowe do uruchomienia narzędzia Prestige Tech."
            if installed_only else
            "Wyszukaj narzędzie, sprawdź wymagania i uruchom je bez zgadywania.",
            9, "#aac0d1"
        ))
        head.addLayout(titles)
        head.addStretch()
        root.addLayout(head)

        stats = QHBoxLayout()
        self.stat_all = StatTile(len(self.mm.modules), "Wszystkie", BLUE)
        self.stat_installed = StatTile(0, "Zainstalowane", GREEN)
        self.stat_portable = StatTile(0, "Portable EXE", CYAN)
        stats.addWidget(self.stat_all)
        stats.addWidget(self.stat_installed)
        stats.addWidget(self.stat_portable)
        root.addLayout(stats)

        if not installed_only:
            actions = QGridLayout()
            actions.setSpacing(9)

            self.install_all_tile = ActionTile(
                "Zainstaluj wszystkie",
                "Instaluje znalezione lokalnie moduły",
                "↓", BLUE
            )
            self.install_all_tile.clicked.connect(self.install_all_requested.emit)
            actions.addWidget(self.install_all_tile, 0, 0)

            self.portable_tile = ActionTile(
                "Tryb Portable",
                "Tryb wyłączony",
                "▶", CYAN, True
            )
            self.portable_tile.clicked.connect(self._toggle_portable)
            actions.addWidget(self.portable_tile, 0, 1)

            self.uninstall_all_tile = ActionTile(
                "Odinstaluj wszystkie",
                "Usuwa tylko kopie z Dashboardu",
                "×", "#ff7784"
            )
            self.uninstall_all_tile.clicked.connect(self.uninstall_all_requested.emit)
            actions.addWidget(self.uninstall_all_tile, 0, 2)

            root.addLayout(actions)

        filter_box = QFrame()
        filter_box.setStyleSheet(f"background:#061522;border:1px solid {LINE};border-radius:11px;")
        filters = QHBoxLayout(filter_box)
        filters.setContentsMargins(11, 8, 11, 8)
        filters.setSpacing(9)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Szukaj po nazwie, opisie lub ID...")
        self.search.textChanged.connect(self.render)
        filters.addWidget(self.search, 1)

        self.category = QComboBox()
        self.category.addItems(["Wszystkie"] + self.mm.categories())
        self.category.currentTextChanged.connect(self.render)
        filters.addWidget(self.category)

        self.state = QComboBox()
        self.state.addItems(["Wszystkie statusy", "Zainstalowane", "Niezainstalowane", "Dostępne portable"])
        self.state.currentTextChanged.connect(self.render)
        if not installed_only:
            filters.addWidget(self.state)
        root.addWidget(filter_box)

        info = QHBoxLayout()
        self.count = QLabel()
        self.count.setStyleSheet("color:#a9bfd0;font-size:9pt;")
        info.addWidget(self.count)
        info.addStretch()
        root.addLayout(info)

        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        for col in range(3):
            self.grid.setColumnStretch(col, 1)
        root.addLayout(self.grid)
        root.addStretch()

        self.render()

    def _toggle_portable(self):
        self.portable = not self.portable
        self.portable_tile.set_checked(self.portable)
        self.portable_changed.emit(self.portable)
        self.render()

    def set_portable(self, enabled):
        if self.installed_only:
            return
        self.portable = bool(enabled)
        self.portable_tile.set_checked(self.portable)
        self.render()

    def set_filter(self, category=None, search=None):
        if category and category in [self.category.itemText(i) for i in range(self.category.count())]:
            self.category.setCurrentText(category)
        if search is not None:
            self.search.setText(search)
        self.render()

    def _portable_candidate(self, module):
        return self.mm.find_local(module, [Path.cwd(), Path.cwd().parent])

    def render(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        installed_count = sum(1 for m in self.mm.modules if self.mm.is_installed(m))
        portable_count = sum(1 for m in self.mm.modules if self._portable_candidate(m))
        self.stat_installed.number.setText(str(installed_count))
        self.stat_portable.number.setText(str(portable_count))

        q = self.search.text().lower().strip()
        cat = self.category.currentText()
        state = self.state.currentText()

        items = []
        for m in self.mm.modules:
            installed = self.mm.is_installed(m)
            portable_available = bool(self._portable_candidate(m))

            if self.installed_only and not installed:
                continue
            if cat != "Wszystkie" and m.category != cat:
                continue
            if q and q not in (m.name + " " + m.category + " " + m.description + " " + m.id).lower():
                continue
            if not self.installed_only:
                if state == "Zainstalowane" and not installed:
                    continue
                if state == "Niezainstalowane" and installed:
                    continue
                if state == "Dostępne portable" and not portable_available:
                    continue
            items.append(m)

        self.count.setText(f"{len(items)} modułów")

        if not items:
            empty = QLabel(
                "Brak modułów pasujących do filtrów."
                if not self.installed_only else
                "Nie masz jeszcze zainstalowanych modułów."
            )
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
                installed=self.mm.is_installed(m),
                portable=self.portable,
                portable_available=bool(self._portable_candidate(m)),
            )
            card.install_requested.connect(self.install_requested.emit)
            card.run_requested.connect(self.run_requested.emit)
            card.remove_requested.connect(self.remove_requested.emit)
            card.help_requested.connect(self.help_requested.emit)
            card.icon_requested.connect(self.icon_requested.emit)
            self.grid.addWidget(card, i // 3, i % 3)

