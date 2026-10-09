from PySide6.QtCore import Signal,QSize
from PySide6.QtGui import QIcon,QPainter,QPainterPath,QPen,QColor
from PySide6.QtWidgets import QFrame,QVBoxLayout,QPushButton,QLabel
from .theme import *
from .icon_manager import icon_path
class Sidebar(QFrame):
    page_requested=Signal(str)
    ITEMS=[("home","Strona główna"),("modules","Moduły"),("installed","Zainstalowane"),("updates","Aktualizacje"),("tools","Narzędzia systemowe"),("reports","Raporty"),("settings","Ustawienia"),("guide","Poradnik"),("about","O programie")]
    def __init__(self):
        super().__init__();self.setFixedWidth(234);self.setStyleSheet(f"background:{SIDEBAR};border:0;");self.buttons={}
        self._reference_style=False
        r=QVBoxLayout(self);r.setContentsMargins(10,18,10,14);r.setSpacing(4)
        self.brand=QLabel("⬡  PRESTIGE TECH\n     PROSTY KOMPUTER. WIĘKSZE MOŻLIWOŚCI.")
        self.brand.setStyleSheet("color:#e9b962;font-size:13pt;font-weight:700;padding:16px 9px 22px;")
        self.brand.hide();r.addWidget(self.brand)
        for asset,name in self.ITEMS:
            b=QPushButton(name);b.setIcon(QIcon(str(icon_path("sidebar",asset))));b.setIconSize(QSize(26,26));b.setCheckable(True);b.setFixedHeight(54)
            b.setStyleSheet(f"QPushButton{{text-align:left;background:transparent;color:{TEXT};border:0;border-radius:11px;padding:10px 14px;font-size:10pt;}}QPushButton:hover{{background:#0b2843;}}QPushButton:checked{{background:#1684ea;border:1px solid #39a7ff;}}")
            b.clicked.connect(lambda checked=False,x=name:self.page_requested.emit(x));r.addWidget(b);self.buttons[name]=b
        r.addStretch();q=QLabel("„Technologia\nma sens tylko wtedy,\ngdy realnie pomaga\nludziom.”");q.setStyleSheet(f"color:{TEXT};font-size:9pt;padding:10px;");r.addWidget(q)
        o=QLabel("Dominik Wasilak\nPRESTIGE TECH");o.setStyleSheet(f"color:{MUTED};font-size:7pt;padding:10px;");r.addWidget(o)
        self.quote=q;self.owner=o
        self.prestige_footer=QLabel("⌁  TECHNOLOGIA DLA CIEBIE  ⌁\n\nPrestige Tech · wersja w rozwoju")
        self.prestige_footer.setStyleSheet("color:#c9aa79;font-size:9pt;padding:18px 10px;")
        self.prestige_footer.hide();r.addWidget(self.prestige_footer)
    def set_reference_style(self, enabled):
        self._reference_style=enabled
        self.setStyleSheet(f"background:{'#071014' if enabled else SIDEBAR};border:0;")
        layout=self.layout()
        system_button=self.buttons["Narzędzia systemowe"]
        layout.removeWidget(system_button)
        layout.insertWidget(3 if enabled else 5,system_button)
        self.brand.setVisible(enabled)
        self.prestige_footer.setVisible(enabled)
        self.quote.setVisible(not enabled)
        self.owner.setVisible(not enabled)
        titles={"Strona główna":"Dashboard","Moduły":"Internet",
                "Zainstalowane":"Protection","Narzędzia systemowe":"System",
                "Raporty":"Reports","Ustawienia":"Settings","Poradnik":"Guide"}
        for name,button in self.buttons.items():
            button.setText(titles.get(name,name) if enabled else name)
            button.setVisible(name not in ("Aktualizacje","O programie") if enabled else name!="Zainstalowane")
            button.setEnabled(button.isVisible())
            if enabled:
                button.setStyleSheet(
                    "QPushButton{text-align:left;background:transparent;color:#f5f3ec;"
                    "border:0;border-radius:9px;padding:10px 14px;font-size:11pt;}"
                    "QPushButton:hover{background:#24231f;}"
                    "QPushButton:checked{background:#292820;border-left:4px solid #e9b962;color:#fff;}"
                )
            else:
                button.setStyleSheet(
                    f"QPushButton{{text-align:left;background:transparent;color:{TEXT};border:0;"
                    "border-radius:11px;padding:10px 14px;font-size:10pt;}"
                    "QPushButton:hover{background:#0b2843;}"
                    "QPushButton:checked{background:#1684ea;border:1px solid #39a7ff;}"
                )
        self.update()
    def paintEvent(self,event):
        super().paintEvent(event)
        if not self._reference_style:
            return
        painter=QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for offset in range(0,9):
            path=QPainterPath()
            y=self.height()-255+offset*7
            path.moveTo(-8,y)
            path.cubicTo(48,y-58,118,y+50,242,y-20)
            painter.setPen(QPen(QColor(216,165,84,max(25,125-offset*11)),1))
            painter.drawPath(path)
        painter.end()
    def set_active(self,name):
        for n,b in self.buttons.items():b.setChecked(n==name)
