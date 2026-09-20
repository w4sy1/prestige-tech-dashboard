from app_version import APP_VERSION, APP_TITLE
from pathlib import Path
import logging
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QScrollArea, QMessageBox, QFileDialog, QLabel
)

from module_manager import LOGS_DIR, MODULES_DIR, ModuleManager
from .theme import *
from .sidebar import Sidebar
from .home_page import HomePage
from .modules_page import ModulesPage
from .installed_page import InstalledPage
from .updates_page import UpdatesPage
from .system_tools_page import SystemToolsPage
from .reports_page import ReportsPage
from .settings_page import SettingsPage
from .settings_store import load_settings
from .guide_page import GuidePage
from .widgets import label
from .icon_manager import IconManager

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QPushButton
from .about_page import AboutPage
from .support_page import SupportPage
from .app_icon import app_icon

LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOGS_DIR / "dashboard.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(app_icon())

        self.mm = ModuleManager()
        self.settings_data = load_settings()
        self.portable_mode = False

        self.setWindowTitle(APP_TITLE)
        self.resize(1536, 1024)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(APP_QSS)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_requested.connect(self.navigate)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        body_layout.addWidget(self.stack, 1)
        outer.addWidget(body, 1)

        footer = QWidget()
        footer.setFixedHeight(58)
        footer.setStyleSheet(
            f"background:{PANEL};border-top:1px solid {LINE};"
        )

        fl = QHBoxLayout(footer)
        fl.setContentsMargins(12, 0, 14, 0)

        ok = QLabel("✓")
        ok.setAlignment(Qt.AlignCenter)
        ok.setFixedSize(34, 34)
        ok.setStyleSheet(
            "background:#2fb86e;color:#062011;border-radius:17px;"
            "font-size:14pt;font-weight:900;"
        )
        fl.addWidget(ok)

        left_text = QVBoxLayout()
        left_text.setSpacing(0)
        left_text.addWidget(label("System gotowy", 9, TEXT, True))
        left_text.addWidget(
            label(
                "Wszystkie funkcje działają poprawnie",
                7,
                MUTED,
            )
        )
        fl.addLayout(left_text)

        fl.addStretch()
        fl.addWidget(
            label(
                "„Wiedza, narzędzia, działanie - realna zmiana.”",
                9,
                TEXT,
            )
        )
        fl.addStretch()
        fl.addWidget(
            label(
                "☼   ◐     PL  🇵🇱     ⚙",
                9,
                TEXT,
            )
        )

        support_btn = QPushButton("Wsparcie")
        support_btn.clicked.connect(lambda: self.navigate("Wsparcie"))
        fl.addWidget(support_btn)

        repo_btn = QPushButton("Repo")
        repo_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/w4sy1/prestige-tech-dashboard")
            )
        )
        fl.addWidget(repo_btn)

        outer.addWidget(footer)

        self.home = HomePage(self.mm)
        self.modules = ModulesPage(self.mm)
        self.installed = InstalledPage(self.mm)
        self.updates = UpdatesPage(self.mm)
        self.system_tools = SystemToolsPage(self.mm)
        self.reports = ReportsPage()
        self.settings = SettingsPage()
        self.guide = GuidePage()
        self.about = AboutPage(len(self.mm.modules))
        self.support = SupportPage()

        self.home_view = self.wrap(self.home)
        self.modules_view = self.wrap(self.modules)
        self.installed_view = self.wrap(self.installed)
        self.updates_view = self.wrap(self.updates)
        self.system_tools_view = self.wrap(self.system_tools)
        self.reports_view = self.wrap(self.reports)
        self.settings_view = self.wrap(self.settings)
        self.guide_view = self.wrap(self.guide)
        self.about_view = self.wrap(self.about)
        self.support_view = self.wrap(self.support)

        for view in (
            self.home_view,
            self.modules_view,
            self.installed_view,
            self.updates_view,
            self.system_tools_view,
            self.reports_view,
            self.settings_view,
            self.guide_view,
        ):
            self.stack.addWidget(view)

        self.placeholders = {}

        for page in (
            self.home,
            self.modules,
            self.installed,
        ):
            self._wire(page)

        self.modules.install_all_requested.connect(
            self.install_all
        )
        self.modules.uninstall_all_requested.connect(
            self.uninstall_all
        )
        self.modules.portable_changed.connect(
            self.set_portable
        )
        self.modules.icon_requested.connect(
            self.choose_icon
        )
        self.installed.icon_requested.connect(
            self.choose_icon
        )

        self.home.modules_requested.connect(
            lambda: self.navigate("Moduły")
        )
        self.home.guide_requested.connect(
            lambda: self.navigate("Poradnik")
        )
        self.home.category_requested.connect(
            self.filter_home
        )

        self.updates.update_requested.connect(
            self.update_module
        )

        self.settings.settings_changed.connect(self.apply_settings)

        self.stack.addWidget(self.about_view)
        self.stack.addWidget(self.support_view)
        self.about.support_requested.connect(lambda: self.navigate("Wsparcie"))
        self.support.guide_requested.connect(lambda: self.navigate("Poradnik"))

        self.navigate("Strona główna")

    def wrap(self, widget):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        area.setWidget(widget)
        return area

    def _wire(self, page):
        page.install_requested.connect(
            self.install
        )
        page.run_requested.connect(
            self.run
        )
        page.remove_requested.connect(
            self.remove
        )
        page.help_requested.connect(
            self.help
        )

    def navigate(self, name):
        self.sidebar.set_active(name)
        if name == "Wsparcie":
            self.stack.setCurrentWidget(self.support_view)
            return

        if name == "O programie":
            self.stack.setCurrentWidget(self.about_view)
            return


        if name == "Strona główna":
            self.stack.setCurrentWidget(
                self.home_view
            )
            return

        if name == "Moduły":
            self.modules.render()
            self.stack.setCurrentWidget(
                self.modules_view
            )
            return

        if name == "Zainstalowane":
            self.installed.render()
            self.stack.setCurrentWidget(
                self.installed_view
            )
            return

        if name == "Aktualizacje":
            self.updates.render()
            self.stack.setCurrentWidget(
                self.updates_view
            )
            return

        if name == "Narzędzia systemowe":
            self.system_tools.render()
            self.stack.setCurrentWidget(
                self.system_tools_view
            )
            return

        if name == "Raporty":
            self.reports.render()
            self.stack.setCurrentWidget(
                self.reports_view
            )
            return

        if name == "Ustawienia":
            self.stack.setCurrentWidget(self.settings_view)
            return

        if name == "Poradnik":
            self.stack.setCurrentWidget(
                self.guide_view
            )
            return

        if name not in self.placeholders:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(
                30,
                30,
                30,
                30,
            )
            layout.addWidget(
                label(
                    name,
                    22,
                    TEXT,
                    True,
                )
            )
            layout.addWidget(
                label(
                    "Sekcja będzie rozwijana w kolejnej iteracji.",
                    9,
                    MUTED,
                )
            )
            layout.addStretch()

            self.placeholders[name] = self.wrap(
                page
            )

            self.stack.addWidget(
                self.placeholders[name]
            )

        self.stack.setCurrentWidget(
            self.placeholders[name]
        )

    def apply_settings(self, data):
        self.settings_data = dict(data)
        self.portable_mode = bool(data.get("portable_default", False))
        self.modules.set_portable(self.portable_mode)

    def filter_home(self, value):
        self.navigate(
            "Moduły"
        )

        if value.startswith(
            "__search__:"
        ):
            self.modules.set_filter(
                "Wszystkie",
                value.split(
                    ":",
                    1,
                )[1],
            )
        else:
            self.modules.set_filter(
                value,
                "",
            )

    def roots(self):
        return [
            Path.cwd(),
            Path.cwd().parent,
        ]

    def set_portable(self, enabled):
        self.portable_mode = bool(
            enabled
        )

    def _save_installed_version(
        self,
        module,
    ):
        try:
            target = (
                MODULES_DIR
                / module.id
            )

            target.mkdir(
                parents=True,
                exist_ok=True,
            )

            (
                target
                / "version.txt"
            ).write_text(
                str(module.version),
                encoding="utf-8",
            )

        except OSError:
            logging.exception(
                "version metadata"
            )

    def choose_icon(
        self,
        module,
    ):
        icons = IconManager(
            self.mm
        )

        if icons.custom_path(
            module.id
        ):
            box = QMessageBox(
                self
            )

            box.setWindowTitle(
                "Ikona | "
                + module.name
            )

            box.setText(
                "Ten moduł ma własną ikonę.\n\nCo chcesz zrobić?"
            )

            change = box.addButton(
                "Zmień ikonę",
                QMessageBox.AcceptRole,
            )

            reset = box.addButton(
                "Przywróć domyślną",
                QMessageBox.DestructiveRole,
            )

            box.addButton(
                "Anuluj",
                QMessageBox.RejectRole,
            )

            box.exec()

            if box.clickedButton() == reset:
                icons.clear_icon(
                    module.id
                )

                self.refresh_modules()

                QMessageBox.information(
                    self,
                    "Ikona",
                    "Przywrócono domyślną ikonę.",
                )

                return

            if box.clickedButton() != change:
                return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz ikonę dla "
            + module.name,
            str(Path.cwd()),
            "Ikony i obrazy (*.ico *.png *.jpg *.jpeg *.svg *.exe);;"
            "Wszystkie pliki (*.*)",
        )

        if not path:
            return

        try:
            icons.set_icon(
                module.id,
                path,
            )

            self.refresh_modules()

            QMessageBox.information(
                self,
                "Ikona",
                "Zapisano własną ikonę dla: "
                + module.name,
            )

        except (
            OSError,
            ValueError,
        ) as exc:
            QMessageBox.critical(
                self,
                "Błąd ikony",
                str(exc),
            )

    def install(
        self,
        module,
    ):
        candidate = self.mm.find_local(
            module,
            self.roots(),
        )

        source = None

        if candidate:
            answer = QMessageBox.question(
                self,
                "Znaleziono moduł",
                f"Znaleziono:\n{candidate}\n\nZainstalować?",
            )

            if answer == QMessageBox.Yes:
                source = candidate

        if not source:
            source, _ = QFileDialog.getOpenFileName(
                self,
                "Wskaż moduł",
                str(Path.cwd()),
                "Program Windows (*.exe)",
            )

        if not source:
            return

        try:
            self.mm.install_file(
                module,
                source,
            )

            self._save_installed_version(
                module
            )

            self.refresh_modules()
            self.updates.render()
            self.system_tools.render()

            QMessageBox.information(
                self,
                "Gotowe",
                "Zainstalowano: "
                + module.name,
            )

        except (
            OSError,
            ValueError,
        ) as exc:
            logging.exception(
                "install"
            )

            QMessageBox.critical(
                self,
                "Błąd instalacji",
                str(exc),
            )

    def install_all(
        self,
    ):
        installed = []
        missing = []
        errors = []

        for module in self.mm.modules:
            if self.mm.is_installed(
                module
            ):
                continue

            candidate = self.mm.find_local(
                module,
                self.roots(),
            )

            if not candidate:
                missing.append(
                    module.name
                )

                continue

            try:
                self.mm.install_file(
                    module,
                    candidate,
                )

                self._save_installed_version(
                    module
                )

                installed.append(
                    module.name
                )

            except (
                OSError,
                ValueError,
            ) as exc:
                errors.append(
                    f"{module.name}: {exc}"
                )

        self.refresh_modules()
        self.updates.render()
        self.system_tools.render()

        message = (
            f"Zainstalowano: {len(installed)}\n"
            f"Brak lokalnego EXE: {len(missing)}\n"
            f"Błędy: {len(errors)}"
        )

        if missing:
            message += (
                "\n\nBrak:\n"
                + "\n".join(
                    "• " + item
                    for item
                    in missing[:12]
                )
            )

        if errors:
            message += (
                "\n\nBłędy:\n"
                + "\n".join(
                    "• " + item
                    for item
                    in errors[:8]
                )
            )

        QMessageBox.information(
            self,
            "Instalacja wszystkich",
            message,
        )

    def uninstall_all(
        self,
    ):
        count = sum(
            1
            for module
            in self.mm.modules
            if self.mm.is_installed(
                module
            )
        )

        if not count:
            QMessageBox.information(
                self,
                "Odinstaluj wszystkie",
                "Nie ma zainstalowanych modułów.",
            )

            return

        answer = QMessageBox.warning(
            self,
            "Odinstaluj wszystkie",
            f"Usunąć wszystkie zainstalowane moduły z Dashboardu?\n\n"
            f"Liczba modułów: {count}\n\n"
            "Oryginalne EXE pozostaną bez zmian.",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        for module in self.mm.modules:
            if self.mm.is_installed(
                module
            ):
                try:
                    self.mm.uninstall(
                        module
                    )

                except OSError:
                    logging.exception(
                        "uninstall all"
                    )

        self.refresh_modules()
        self.updates.render()
        self.system_tools.render()

        QMessageBox.information(
            self,
            "Odinstaluj wszystkie",
            "Gotowe.",
        )

    def update_module(
        self,
        module,
    ):
        candidate = self.mm.find_local(
            module,
            self.roots(),
        )

        if not candidate:
            QMessageBox.information(
                self,
                "Aktualizacja",
                "Nie znaleziono lokalnego EXE nowszej wersji.\n\n"
                "Automatyczne pobieranie z GitHub Releases podłączymy później.",
            )

            return

        answer = QMessageBox.question(
            self,
            "Aktualizacja",
            f"Znaleziono lokalny plik:\n\n{candidate}\n\n"
            f"Zaktualizować {module.name}?",
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.mm.install_file(
                module,
                candidate,
            )

            self._save_installed_version(
                module
            )

            self.refresh_modules()
            self.updates.render()

            QMessageBox.information(
                self,
                "Aktualizacja",
                "Zaktualizowano: "
                + module.name,
            )

        except (
            OSError,
            ValueError,
        ) as exc:
            logging.exception(
                "update"
            )

            QMessageBox.critical(
                self,
                "Błąd aktualizacji",
                str(exc),
            )

    def run(
        self,
        module,
    ):
        if (
            module.risk
            == "changes_system"
        ):
            answer = QMessageBox.warning(
                self,
                "Potwierdzenie",
                module.name
                + " może zmieniać ustawienia systemu.\n\nUruchomić?",
                QMessageBox.Yes
                | QMessageBox.No,
                QMessageBox.No,
            )

            if answer != QMessageBox.Yes:
                return

        try:
            if self.portable_mode:
                candidate = self.mm.find_local(
                    module,
                    self.roots(),
                )

                if candidate:
                    subprocess.Popen(
                        [str(candidate)],
                        cwd=candidate.parent,
                    )

                    return

            self.mm.launch(
                module
            )

        except (
            OSError,
            ValueError,
        ) as exc:
            logging.exception(
                "launch"
            )

            QMessageBox.critical(
                self,
                "Błąd uruchamiania",
                str(exc),
            )

    def remove(
        self,
        module,
    ):
        answer = QMessageBox.question(
            self,
            "Odinstalowanie",
            "Usunąć "
            + module.name
            + "?",
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.mm.uninstall(
                module
            )

            self.refresh_modules()
            self.updates.render()
            self.system_tools.render()

        except OSError as exc:
            logging.exception(
                "remove"
            )

            QMessageBox.critical(
                self,
                "Błąd",
                str(exc),
            )

    def help(self, module):
        self.guide.open_topic_for_module(module)
        self.navigate("Poradnik")



    def refresh_modules(
        self,
    ):
        self.modules.render()
        self.installed.render()

