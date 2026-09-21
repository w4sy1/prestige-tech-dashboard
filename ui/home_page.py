from pathlib import Path
from PySide6.QtCore import Signal, Qt, QUrl, QSize
from PySide6.QtGui import QPixmap, QDesktopServices, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLineEdit, QLabel, QMessageBox, QPushButton
from .theme import *
from .widgets import *

MAIN = [
    ("Komputer i Windows","Diagnostyka, naprawa,\nczyszczenie, optymalizacja"),
    ("Sieć i Internet","Diagnostyka sieci, skanowanie,\nDNS, monitoring"),
    ("Android i ADB","Zarządzanie urządzeniami,\nTermux, diagnostyka"),
    ("Bezpieczeństwo","Skanowanie, analiza plików,\nmalware, integralność"),
    ("Pliki i dane","Odzysk danych, hashe,\nanaliza plików, monitoring"),
    ("Narzędzia zaawansowane","Nmap, snapshoty, raporty,\nnarzędzia systemowe")
]

SOCIALS = {
    "GitHub": "https://github.com/w4sy1",
    "YouTube": "",
    "Instagram": "https://www.instagram.com/projekt.ocalenie/",
    "Facebook": "https://www.facebook.com/profile.php?viewas=100000686899395&id=61572604231491",
}

class HomePage(QWidget):
    category_requested = Signal(str)
    modules_requested = Signal()
    guide_requested = Signal()
    install_requested = Signal(object)
    run_requested = Signal(object)
    remove_requested = Signal(object)
    help_requested = Signal(object)

    def __init__(self, mm):
        super().__init__()
        self.mm = mm

        root = QVBoxLayout(self)
        root.setContentsMargins(13, 13, 13, 13)
        root.setSpacing(11)

        top = QHBoxLayout()
        top.setSpacing(14)

        hero = QFrame()
        hero.setFixedHeight(294)
        hero.setStyleSheet("QFrame{background:#020914;border:1px solid #154767;border-radius:12px;}")
        hv = QVBoxLayout(hero)
        hv.setContentsMargins(0, 0, 0, 0)

        banner = QLabel()
        banner.setAlignment(Qt.AlignCenter)
        banner.setStyleSheet("background:#020914;border:0;border-radius:12px;")
        asset = Path(__file__).resolve().parent.parent / "assets" / "dashboard_banner.png"
        pix = QPixmap(str(asset))
        if not pix.isNull():
            banner.setPixmap(pix.scaledToHeight(294, Qt.SmoothTransformation))
        hv.addWidget(banner)
        top.addWidget(hero, 1)

        social = QFrame()
        social.setProperty("panel", True)
        social.setFixedSize(285, 294)
        sv = QVBoxLayout(social)
        sv.setContentsMargins(22, 20, 22, 16)
        sv.setSpacing(12)

        t = label("Kompleksowe narzędzia\ndo codziennych wyzwań.\nBezpieczeństwo. Kontrola.\nWiedza. Wolność.", 11, TEXT)
        t.setWordWrap(True)
        sv.addWidget(t)
        sv.addWidget(label("━━━━", 8, BLUE, True))
        sv.addStretch()

        icons_row = QHBoxLayout()
        icons_row.setSpacing(10)
        icon_dir = Path(__file__).resolve().parent.parent / "assets" / "icons"
        for name in ("GitHub", "YouTube", "Instagram", "Facebook"):
            b = QPushButton()
            b.setFixedSize(52, 44)
            b.setIcon(QIcon(str(icon_dir / f"{name.lower()}.svg")))
            b.setIconSize(QSize(28, 28))
            b.clicked.connect(lambda checked=False, x=name: self.open_social(x))
            icons_row.addWidget(b)
        sv.addLayout(icons_row)

        sv.addWidget(button("Odwiedź moje linki  ↗", lambda: self.open_social("GitHub")))
        top.addWidget(social)
        root.addLayout(top)

        main = QHBoxLayout()
        main.setSpacing(12)
        center = QVBoxLayout()
        center.setSpacing(10)

        hd = QHBoxLayout()
        hd.addWidget(label("KATEGORIE NARZĘDZI", 13, TEXT, True))
        hd.addWidget(label("────", 8, BLUE, True))
        hd.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("⌕  Szukaj narzędzia, np. nmap, backup, android...")
        self.search.setFixedWidth(450)
        self.search.returnPressed.connect(self.search_now)
        hd.addWidget(self.search)
        center.addLayout(hd)

        grid = QGridLayout()
        grid.setSpacing(10)
        for i, (c, d) in enumerate(MAIN):
            card = CategoryCard(c, sum(1 for m in mm.modules if m.category == c), d)
            card.clicked.connect(self.category_requested.emit)
            grid.addWidget(card, i // 3, i % 3)
        center.addLayout(grid)

        rh = QHBoxLayout()
        rh.addWidget(label("OSTATNIO DODANE", 12, TEXT, True))
        rh.addWidget(label("────", 8, BLUE, True))
        rh.addStretch()
        center.addLayout(rh)

        rg = QGridLayout()
        rg.setSpacing(10)
        for i, module_id in enumerate(["prestige-termux-toolkit", "prestige-nmap-profiles", "prestige-windows-toolkit"]):
            m = next((m for m in mm.modules if m.id == module_id), None)
            if m:
                card = RecentCard(m, mm, mm.is_installed(m))
                card.install_requested.connect(self.install_requested.emit)
                card.run_requested.connect(self.run_requested.emit)
                rg.addWidget(card, 0, i)
        center.addLayout(rg)
        main.addLayout(center, 1)

        side = QVBoxLayout()
        side.setSpacing(12)

        q = QFrame()
        q.setProperty("panel", True)
        q.setFixedWidth(285)
        qv = QVBoxLayout(q)
        qv.addWidget(label("SZYBKI START", 10, TEXT, True))
        for i, text in enumerate(("Wybierz kategorię\nnarzędzi", "Zainstaluj wybrane\nmoduły", "Uruchom narzędzie", "Postępuj zgodnie\nz instrukcjami"), 1):
            row = QHBoxLayout()
            num = QLabel(str(i))
            num.setAlignment(Qt.AlignCenter)
            num.setFixedSize(36, 36)
            num.setStyleSheet("background:#0b2237;color:white;border:1px solid #2a6d9a;border-radius:18px;font-size:15pt;font-weight:800;")
            row.addWidget(num)
            row.addWidget(label(text, 8, MUTED), 1)
            qv.addLayout(row)
        qv.addWidget(button("▱  Zobacz pełny poradnik", self.guide_requested.emit, True))
        side.addWidget(q)

        h = QFrame()
        h.setProperty("panel", True)
        h.setFixedWidth(285)
        hv2 = QVBoxLayout(h)
        hv2.addWidget(label("POTRZEBUJESZ POMOCY?", 10, TEXT, True))
        for text in ("?   Najczęstsze pytania (FAQ)   ›", "⚙   Zgłoś problem   ›", "◎   Wsparcie i kontakt   ›"):
            hv2.addWidget(label(text, 8, TEXT))
        side.addWidget(h)
        side.addStretch()
        main.addLayout(side)

        root.addLayout(main)

    def search_now(self):
        q = self.search.text().strip()
        if q:
            self.category_requested.emit("__search__:" + q)

    def open_social(self, name):
        url = SOCIALS.get(name, "")
        if url:
            QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.information(self, name, "Link nie został jeszcze skonfigurowany.")

