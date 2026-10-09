"""Lokalne skróty do ważnych stron; pełny adres przed każdym otwarciem."""

import json
from pathlib import Path
import uuid
from urllib.parse import urlsplit

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QInputDialog, QLabel,
                               QMessageBox, QPushButton, QVBoxLayout)

from module_manager import CONFIG_DIR


FAVORITES_FILE = CONFIG_DIR / "favorite_links.json"
MAX_LINKS = 6
NAMES = ("Bank", "Poczta", "Wyniki badań", "Rodzina", "Zdjęcia", "Inna strona")


def validate_link(name, address):
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 40:
        raise ValueError("Podaj krótką nazwę skrótu.")
    if not isinstance(address, str) or not 1 <= len(address.strip()) <= 2048:
        raise ValueError("Podaj pełny adres strony HTTPS.")
    address = address.strip()
    if any(ord(char) < 32 for char in address) or "\\" in address:
        raise ValueError("Adres zawiera niedozwolone znaki.")
    try:
        parsed = urlsplit(address)
        host = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("Nieprawidłowy adres strony.") from error
    if (parsed.scheme != "https" or not host or "." not in host
            or any(char.isspace() for char in host)
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment):
        raise ValueError("Użyj adresu HTTPS bez hasła, parametrów i fragmentu.")
    if port not in (None, 443):
        raise ValueError("Niestandardowy port wymaga ręcznego otwarcia w przeglądarce.")
    return {"name": name.strip(), "url": address, "domain": host.lower()}


def load_links(path=None):
    source = Path(path or FAVORITES_FILE)
    try:
        with source.open("rb") as stream:
            raw = stream.read(32 * 1024 + 1)
        if len(raw) > 32 * 1024:
            return []
        data = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            return []
        rows = []
        for item in data.get("links", [])[:MAX_LINKS]:
            try:
                rows.append(validate_link(item["name"], item["url"]))
            except (ValueError, KeyError, TypeError):
                continue
        return rows
    except (OSError, ValueError, TypeError, UnicodeError):
        return []


def save_links(links, path=None):
    if not isinstance(links, list) or len(links) > MAX_LINKS:
        raise ValueError("Można zapisać maksymalnie sześć skrótów.")
    cleaned = [validate_link(row["name"], row["url"]) for row in links]
    destination = Path(path or FAVORITES_FILE)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(json.dumps({"schema_version": 1, "links": cleaned},
                                        ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


class FavoriteLinksWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("panel", True)
        self.links = load_links()
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        title = QHBoxLayout()
        title.addWidget(QLabel("Ważne strony"))
        title.addStretch()
        add = QPushButton("Dodaj skrót")
        add.clicked.connect(self.add_link)
        title.addWidget(add)
        self.remove_choice = QComboBox()
        title.addWidget(self.remove_choice)
        remove = QPushButton("Usuń")
        remove.clicked.connect(self.remove_link)
        title.addWidget(remove)
        root.addLayout(title)
        self.links_row = QHBoxLayout()
        root.addLayout(self.links_row)
        self.refresh()

    def refresh(self):
        while self.links_row.count():
            item = self.links_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.remove_choice.clear()
        for index, link in enumerate(self.links):
            button = QPushButton(link["name"])
            button.setToolTip(link["url"])
            button.clicked.connect(lambda checked=False, i=index: self.open_link(i))
            self.links_row.addWidget(button)
            self.remove_choice.addItem(link["name"], index)
        self.links_row.addStretch()

    def add_link(self):
        if len(self.links) >= MAX_LINKS:
            QMessageBox.information(self, "Ważne strony", "Można dodać maksymalnie sześć skrótów.")
            return
        name, accepted = QInputDialog.getItem(self, "Nowy skrót", "Rodzaj strony:", NAMES, 0, False)
        if not accepted:
            return
        if name == "Inna strona":
            name, accepted = QInputDialog.getText(self, "Nowy skrót", "Nazwa:")
            if not accepted:
                return
        address, accepted = QInputDialog.getText(self, "Nowy skrót", "Pełny adres HTTPS:")
        if not accepted:
            return
        try:
            candidate = validate_link(name, address)
            save_links([*self.links, candidate])
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.warning(self, "Nie dodano skrótu", str(error))
            return
        self.links.append(candidate)
        self.refresh()

    def remove_link(self):
        index = self.remove_choice.currentData()
        if index is None:
            return
        updated = [row for number, row in enumerate(self.links) if number != index]
        try:
            save_links(updated)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Nie usunięto skrótu", str(error))
            return
        self.links = updated
        self.refresh()

    def open_link(self, index):
        link = self.links[index]
        if QMessageBox.question(self, "Otworzyć stronę?",
                                f"Nazwa: {link['name']}\nDomena: {link['domain']}\nPełny adres: {link['url']}\n\nOtworzyć w przeglądarce?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl(link["url"]))
