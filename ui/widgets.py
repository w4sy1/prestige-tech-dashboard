from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QIcon
from .theme import *
from .icon_manager import IconManager, icon_path

DESC = "#b9ccdc"
SUBTLE = "#91adc1"
CHIP_TEXT = "#d5e8f5"

def label(text="", size=9, color=TEXT, bold=False):
    w = QLabel(text)
    w.setStyleSheet(
        f"color:{color};font-size:{size}pt;font-weight:{700 if bold else 400};"
        "border:0;background:transparent;"
    )
    return w

def button(text, callback=None, primary=False):
    b = QPushButton(text)
    b.setProperty("primary", primary)
    b.setMinimumHeight(36)
    if callback:
        b.clicked.connect(callback)
    return b

CATEGORY_STYLE = {
    "Komputer i Windows": ("#082038", "#12a8ff", "windows"),
    "Sieć i Internet": ("#082038", "#1ac8ff", "network"),
    "Android i ADB": ("#0b2b29", "#52db72", "android"),
    "Bezpieczeństwo": ("#1b1740", "#8b68ff", "security"),
    "Pliki i dane": ("#302912", "#f4cc47", "files"),
    "Narzędzia zaawansowane": ("#082038", "#6dc2ff", "advanced"),
}

RISK_STYLE = {
    "safe": ("Bezpieczne", GREEN),
    "changes_system": ("Zmienia system", YELLOW),
    "advanced": ("Zaawansowane", "#ffb44c"),
    "external_service": ("Usługa zewnętrzna", CYAN),
}

class CategoryCard(QFrame):
    clicked = Signal(str)

    def __init__(self, category, count, description):
        super().__init__()
        self.category = category
        bg, accent, asset = CATEGORY_STYLE[category]
        self.setFixedHeight(145)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"QFrame{{background:{bg};border:1px solid {accent};border-radius:12px;}}")
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 14, 16, 14)
        root.setSpacing(14)

        icon = QLabel()
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(68, 68)
        icon.setPixmap(QIcon(str(icon_path("categories", asset))).pixmap(QSize(58, 58)))
        root.addWidget(icon)

        mid = QVBoxLayout()
        mid.addWidget(label(category, 10, TEXT, True))
        d = label(description, 8, DESC)
        d.setWordWrap(True)
        mid.addWidget(d)
        mid.addStretch()
        mid.addWidget(label(f"{count} narzędzi", 8, SUBTLE))
        root.addLayout(mid, 1)
        root.addWidget(label("›", 21, accent, True))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.category)
        super().mousePressEvent(event)

class ModuleIcon(QLabel):
    def __init__(self, module, manager, size=64):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(size, size)
        self.setStyleSheet(f"background:#061522;border:1px solid {LINE};border-radius:10px;")
        self.setPixmap(IconManager(manager).icon_for(module).pixmap(QSize(size-10, size-10)))

class RecentCard(QFrame):
    install_requested = Signal(object)
    run_requested = Signal(object)

    def __init__(self, module, manager, installed=False):
        super().__init__()
        self.setProperty("card", True)
        self.setFixedHeight(125)
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)
        root.addWidget(ModuleIcon(module, manager, 68))

        content = QVBoxLayout()
        top = QHBoxLayout()
        top.addWidget(label(module.name, 9, TEXT, True))
        if module.id in ("prestige-termux-toolkit", "prestige-nmap-profiles"):
            badge = QLabel("Nowość")
            badge.setStyleSheet("background:#63d86f;color:#00170b;border-radius:9px;padding:3px 8px;font-size:8pt;font-weight:700;")
            top.addWidget(badge)
        top.addStretch()
        content.addLayout(top)

        d = label(module.description, 8, DESC)
        d.setWordWrap(True)
        content.addWidget(d)
        content.addStretch()

        row = QHBoxLayout()
        row.addWidget(label("v" + module.version, 8, SUBTLE))
        row.addStretch()
        row.addWidget(button(
            "Uruchom" if installed else "Zainstaluj",
            lambda: self.run_requested.emit(module) if installed else self.install_requested.emit(module),
            True
        ))
        content.addLayout(row)
        root.addLayout(content, 1)

class ModuleCard(QFrame):
    install_requested = Signal(object)
    run_requested = Signal(object)
    remove_requested = Signal(object)
    help_requested = Signal(object)
    icon_requested = Signal(object)

    def __init__(self, module, manager, installed=False, portable=False, portable_available=False):
        super().__init__()
        self.module = module
        self.setProperty("card", True)
        self.setMinimumHeight(220)
        self.setMaximumHeight(235)

        accent = CATEGORY_STYLE.get(module.category, ("", BLUE, ""))[1]
        self.setStyleSheet(
            f"QFrame{{background:{CARD};border:1px solid {LINE};border-radius:12px;}}"
            f"QFrame:hover{{border:1px solid {accent};background:#0b2740;}}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(15, 13, 15, 13)
        root.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(ModuleIcon(module, manager, 50))

        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(label(module.name, 11, TEXT, True))
        titles.addWidget(label(module.category.upper(), 7, accent, True))
        top.addLayout(titles, 1)

        risk_name, risk_color = RISK_STYLE.get(module.risk, ("Informacja", SUBTLE))
        risk = QLabel("● " + risk_name)
        risk.setStyleSheet(
            f"color:{risk_color};background:#071725;border:1px solid {risk_color};"
            "border-radius:8px;padding:5px 8px;font-size:8pt;font-weight:700;"
        )
        top.addWidget(risk)
        root.addLayout(top)

        desc = label(module.description, 9, DESC)
        desc.setWordWrap(True)
        desc.setMaximumHeight(42)
        root.addWidget(desc)

        meta = QHBoxLayout()
        reqs = list(module.requirements)[:2]
        if reqs:
            for req in reqs:
                chip = QLabel(req)
                chip.setStyleSheet(
                    f"color:{CHIP_TEXT};background:#071827;border:1px solid #24516f;"
                    "border-radius:7px;padding:4px 7px;font-size:8pt;"
                )
                meta.addWidget(chip)
        else:
            meta.addWidget(label("Bez dodatkowych wymagań", 8, SUBTLE))
        meta.addStretch()

        if installed:
            status, color = "● Zainstalowano", GREEN
        elif portable and portable_available:
            status, color = "● Portable", CYAN
        elif portable and not portable_available:
            status, color = "○ Brak EXE", "#ff8e8e"
        else:
            status, color = "○ Niezainstalowany", SUBTLE

        meta.addWidget(label(status, 8, color, True))
        meta.addWidget(label("v" + module.version, 8, SUBTLE))
        root.addLayout(meta)

        root.addStretch()

        actions = QHBoxLayout()
        actions.setSpacing(7)

        if installed or (portable and portable_available):
            actions.addWidget(button(
                "Uruchom portable" if portable and portable_available and not installed else "Uruchom",
                lambda: self.run_requested.emit(module),
                True
            ))
            if installed:
                actions.addWidget(button("Odinstaluj", lambda: self.remove_requested.emit(module)))
        else:
            actions.addWidget(button("Zainstaluj", lambda: self.install_requested.emit(module), True))

        actions.addStretch()

        icon_btn = QPushButton("Ikona")
        icon_btn.setMinimumHeight(36)
        icon_btn.setToolTip("Wybierz własną ikonę dla tego modułu")
        icon_btn.clicked.connect(lambda: self.icon_requested.emit(module))
        actions.addWidget(icon_btn)

        help_btn = QPushButton("?")
        help_btn.setFixedSize(38, 36)
        help_btn.setToolTip("Jak użyć tego modułu?")
        help_btn.clicked.connect(lambda: self.help_requested.emit(module))
        actions.addWidget(help_btn)

        root.addLayout(actions)

