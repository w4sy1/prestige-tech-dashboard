BG="#020812"; SIDEBAR="#061321"; PANEL="#071827"; CARD="#092138"; LINE="#154767"
BLUE="#078cff"; CYAN="#28c8ff"; TEXT="#f4f8fc"; MUTED="#a2b5c7"; GREEN="#45d99a"; YELLOW="#ffd04a"
APP_QSS=f"""
QMainWindow,QWidget#Root{{background:{BG};color:{TEXT};font-family:"Segoe UI";}}
QScrollArea{{border:0;background:{BG};}} QScrollArea>QWidget>QWidget{{background:{BG};}}
QPushButton{{background:#0b2237;color:{TEXT};border:1px solid {LINE};border-radius:9px;padding:8px 13px;font-weight:600;}}
QPushButton:hover{{background:#103653;border-color:{BLUE};}}
QPushButton[primary="true"]{{background:#087df0;color:white;border-color:#159bff;}}
QLineEdit{{background:#071827;color:{TEXT};border:1px solid #235b84;border-radius:9px;padding:10px 13px;font-size:12px;}}
QFrame[card="true"],QFrame[panel="true"]{{background:{CARD};border:1px solid {LINE};border-radius:11px;}}
QToolTip{{background:{PANEL};color:{TEXT};border:1px solid {LINE};padding:6px;}}
"""
CATEGORY_STYLE={
"Komputer i Windows":("#082038","#0aa9ff"),"Sieć i Internet":("#082038","#0aa9ff"),
"Android i ADB":("#092b29","#49dd72"),"Bezpieczeństwo":("#1b1740","#8264ff"),
"Pliki i dane":("#302a12","#f5c83c"),"Narzędzia zaawansowane":("#082038","#3cb9ff")}

