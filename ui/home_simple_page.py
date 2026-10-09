"""Drugi styl Dashboardu: czarne panele, złoto i górskie tło.

Kafle korzystają z tego samego katalogu Centrów co widok niebieski. Ekran
nie pokazuje zmyślonych procentów zdrowia, historii ani stanu ochrony.
"""

from pathlib import Path

from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QVBoxLayout, QWidget)
from .favorite_links import FavoriteLinksWidget


GOLD = "#e9b962"
TEXT = "#f6f4ef"
MUTED = "#bdc4ca"
ASSET = Path(__file__).resolve().parent.parent / "assets" / "dashboard_mountains.png"
CARD_ART = Path(__file__).resolve().parent.parent / "assets" / "dashboard_card_art.png"
PROMO_ART = Path(__file__).resolve().parent.parent / "assets" / "dashboard_promo.png"


def copy(text, size=10, *, color=TEXT, bold=False, wrap=False):
    widget = QLabel(text)
    widget.setWordWrap(wrap)
    widget.setStyleSheet(
        f"color:{color};font-size:{size}pt;font-weight:{700 if bold else 400};"
        "background:transparent;border:0;"
    )
    return widget


class MountainHeader(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(116)
        self.background = QPixmap(str(ASSET))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#050b0e"))
        if not self.background.isNull():
            source_height = min(self.background.height(),
                                max(1, self.background.width() * self.height() // max(1, self.width())))
            source_top = max(0, (self.background.height() - source_height) // 2)
            painter.drawPixmap(self.rect(), self.background,
                               QRect(0, source_top, self.background.width(), source_height))
            painter.fillRect(self.rect(), QColor(0, 0, 0, 105))
        painter.end()
        super().paintEvent(event)


class ActionTile(QFrame):
    def __init__(self, icon, title, detail, callback, art_index):
        super().__init__()
        self.art = QPixmap(str(CARD_ART))
        self.art_index = art_index
        self.setObjectName("PrestigeActionTile")
        self.setMinimumHeight(168)
        self.setStyleSheet(
            "QFrame#PrestigeActionTile{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #142029,stop:0.55 #071017,stop:1 #040a0e);"
            "border:1px solid #43505a;border-radius:12px;}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 13, 17, 13)
        root.setSpacing(6)
        root.addWidget(copy(icon, 26, color=GOLD))
        root.addWidget(copy(title, 13, bold=True))
        root.addWidget(copy(detail, 9, color=MUTED, wrap=True), 1)
        button = QPushButton("Otwórz  →")
        button.setStyleSheet(
            "QPushButton{color:#fff;background:#24221e;border:1px solid #ac7f42;"
            "border-radius:12px;padding:5px 10px;font-weight:600;}"
            "QPushButton:hover{background:#59452b;border-color:#f0c879;}"
        )
        button.clicked.connect(callback)
        root.addWidget(button, 0, Qt.AlignRight)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.art.isNull():
            return
        painter = QPainter(self)
        panel_width = self.art.width() // 5
        source = QRect(self.art_index * panel_width, self.art.height() // 3,
                       panel_width, self.art.height() // 2)
        painter.drawPixmap(self.rect(), self.art, source)
        painter.fillRect(self.rect(), QColor(0, 4, 9, 145))
        painter.setPen(QPen(QColor("#765e3d"), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 11, 11)
        painter.end()


class StatusTile(QFrame):
    def __init__(self, icon, title, detail, callback):
        super().__init__()
        self.setObjectName("PrestigeStatusTile")
        self.setMinimumHeight(155)
        self.setStyleSheet(
            "QFrame#PrestigeStatusTile{background:#0c151b;"
            "border:1px solid #36434a;border-radius:12px;}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(17, 14, 17, 14)
        heading = QHBoxLayout()
        heading.addWidget(copy(icon, 20, color=GOLD))
        heading.addWidget(copy(title, 11, bold=True), 1)
        root.addLayout(heading)
        middle = QHBoxLayout()
        marker = QLabel("?")
        marker.setAlignment(Qt.AlignCenter)
        marker.setFixedSize(54, 54)
        marker.setStyleSheet("color:#e9b962;border:4px solid #b78b49;"
                             "border-radius:27px;background:#112018;font-size:19pt;font-weight:700;")
        middle.addWidget(marker)
        details = QVBoxLayout()
        details.addWidget(copy("Do sprawdzenia", 11, color=GOLD, bold=True))
        details.addWidget(copy(detail, 9, color=MUTED, wrap=True))
        middle.addLayout(details, 1)
        root.addLayout(middle, 1)
        button = QPushButton("Sprawdź szczegóły  →")
        button.setStyleSheet(
            "QPushButton{color:#f7f1e6;background:#182126;border:1px solid #715c3e;"
            "border-radius:8px;padding:6px 9px;}"
            "QPushButton:hover{background:#3d3529;border-color:#e9b962;}"
        )
        button.clicked.connect(callback)
        root.addWidget(button, 0, Qt.AlignRight)


class PromoBanner(QFrame):
    def __init__(self):
        super().__init__()
        self.art = QPixmap(str(PROMO_ART))
        self.setMinimumHeight(200)

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.art.isNull():
            painter.drawPixmap(self.rect(), self.art, self.art.rect())
        else:
            painter.fillRect(self.rect(), QColor("#17130e"))
        painter.fillRect(QRect(0, 0, self.width() * 2 // 3, self.height()),
                         QColor(0, 0, 0, 110))
        painter.setPen(QPen(QColor(GOLD), 2))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 12, 12)
        painter.end()
        super().paintEvent(event)


class SimpleHomePage(QWidget):
    category_requested = Signal(str)
    modules_requested = Signal()
    guide_requested = Signal()
    install_requested = Signal(object)
    run_requested = Signal(object)
    remove_requested = Signal(object)
    help_requested = Signal(object)

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setStyleSheet("background:#050b0e;")
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 0, 20, 22)
        root.setSpacing(16)

        hero = MountainHeader()
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(14, 15, 16, 14)
        title = QVBoxLayout()
        title.addWidget(copy("Prestige Tech  Dashboard", 27, bold=True))
        title.addWidget(copy(
            "Wszystko, czego potrzebujesz, aby Twój komputer działał lepiej i bezpieczniej.",
            10, color="#e0e4e7", wrap=True))
        hero_layout.addLayout(title, 1)
        hero_layout.addWidget(copy("Szybciej.\nBezpieczniej.\nProściej.", 11, color=GOLD))
        root.addWidget(hero)

        actions = QGridLayout()
        actions.setSpacing(11)
        items = (
            ("◎", "Internet Tools", "Diagnostyka i ustawienia sieci.", "Sieć"),
            ("▣", "System Tools", "Kontrola i naprawy Windows.", "Komputer i Windows"),
            ("⬡", "Protection Tools", "Bezpieczeństwo plików i systemu.", "Bezpieczeństwo"),
            ("▤", "Reports", "Wyniki i raporty serwisowe.", "AI i raporty"),
            ("⚡", "Quick Actions", "Wybierz potrzebne Centrum.", None),
        )
        for column, (icon, title, detail, category) in enumerate(items):
            callback = (lambda checked=False, value=category:
                        self.category_requested.emit(value) if value else self.modules_requested.emit())
            actions.addWidget(ActionTile(icon, title, detail, callback, column), 0, column)
            actions.setColumnStretch(column, 1)
        root.addLayout(actions)

        status = QGridLayout()
        status.setSpacing(11)
        sections = (
            ("▣", "Stan komputera", "Uruchom System Center, aby sprawdzić stan urządzenia.", "Komputer i Windows"),
            ("◎", "Połączenie z Internetem", "Sprawdź połączenie i DNS w Network Center.", "Sieć"),
            ("⬡", "Bezpieczeństwo", "Uruchom audyt; stan ochrony nie został jeszcze sprawdzony.", "Bezpieczeństwo"),
            ("◷", "Ostatnie działania", "Otwórz raporty i zapisane wyniki Centrów.", "AI i raporty"),
        )
        for column, (icon, title, detail, category) in enumerate(sections):
            callback = (lambda checked=False, value=category:
                        self.category_requested.emit(value))
            status.addWidget(StatusTile(icon, title, detail, callback), 0, column)
            status.setColumnStretch(column, 1)
        root.addLayout(status)

        banner = PromoBanner()
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(25, 16, 25, 16)
        banner_layout.addWidget(copy("★", 27, color=GOLD))
        banner_text = QVBoxLayout()
        headline = copy("Już niedługo: Prestige Tech dla każdego", 20, color=GOLD, bold=True, wrap=True)
        headline.setMaximumWidth(570)
        banner_text.addWidget(headline)
        summary = copy(
            "Naprawa systemu, diagnostyka Internetu i ochrona danych w jednym miejscu."
            " Rozwijamy aplikację z myślą o osobach nietechnicznych.",
            11, wrap=True)
        summary.setMaximumWidth(550)
        banner_text.addWidget(summary)
        banner_text.addStretch()
        banner_text.addWidget(copy("PROSTY KOMPUTER. WIĘKSZE MOŻLIWOŚCI.", 9, color=GOLD, bold=True))
        banner_layout.addLayout(banner_text, 1)
        root.addWidget(banner)
        self.favorites = FavoriteLinksWidget()
        root.addWidget(self.favorites)
        root.addStretch()
