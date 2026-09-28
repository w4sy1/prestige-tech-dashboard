from PySide6.QtCore import Signal,QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame,QVBoxLayout,QPushButton,QLabel
from .theme import *
from .icon_manager import icon_path
class Sidebar(QFrame):
    page_requested=Signal(str)
    ITEMS=[("home","Strona główna"),("modules","Moduły"),("installed","Zainstalowane"),("updates","Aktualizacje"),("tools","Narzędzia systemowe"),("reports","Raporty"),("settings","Ustawienia"),("guide","Poradnik"),("about","O programie")]
    def __init__(self):
        super().__init__();self.setFixedWidth(234);self.setStyleSheet(f"background:{SIDEBAR};border:0;");self.buttons={}
        r=QVBoxLayout(self);r.setContentsMargins(10,18,10,14);r.setSpacing(4)
        for asset,name in self.ITEMS:
            b=QPushButton(name);b.setIcon(QIcon(str(icon_path("sidebar",asset))));b.setIconSize(QSize(26,26));b.setCheckable(True);b.setFixedHeight(54)
            b.setStyleSheet(f"QPushButton{{text-align:left;background:transparent;color:{TEXT};border:0;border-radius:11px;padding:10px 14px;font-size:10pt;}}QPushButton:hover{{background:#0b2843;}}QPushButton:checked{{background:#1684ea;border:1px solid #39a7ff;}}")
            b.clicked.connect(lambda checked=False,x=name:self.page_requested.emit(x));r.addWidget(b);self.buttons[name]=b
        r.addStretch();q=QLabel("„Technologia\nma sens tylko wtedy,\ngdy realnie pomaga\nludziom.”");q.setStyleSheet(f"color:{TEXT};font-size:9pt;padding:10px;");r.addWidget(q)
        o=QLabel("Dominik Wasilak\nPRESTIGE TECH");o.setStyleSheet(f"color:{MUTED};font-size:7pt;padding:10px;");r.addWidget(o)
    def set_active(self,name):
        for n,b in self.buttons.items():b.setChecked(n==name)
