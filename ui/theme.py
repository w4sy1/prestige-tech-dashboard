BG="#020812"; SIDEBAR="#061321"; PANEL="#071827"; CARD="#092138"; LINE="#154767"
BLUE="#078cff"; CYAN="#28c8ff"; TEXT="#f4f8fc"; MUTED="#a2b5c7"; GREEN="#45d99a"; YELLOW="#ffd04a"

# Kolory drugiego stylu są nakładane tylko na istniejące arkusze widoków.
# Niebieski styl zachowuje swoje oryginalne wartości.
REFERENCE_COLORS = {
    "#020812": "#050b0e", "#061321": "#071014", "#071827": "#10181b",
    "#092138": "#151c1e", "#154767": "#685437", "#078cff": "#d5a65b",
    "#28c8ff": "#e9b962", "#0b2237": "#24231f", "#103653": "#3c3326",
    "#087df0": "#8c6837", "#159bff": "#e9b962", "#235b84": "#846b46",
    "#0b2843": "#292820", "#1684ea": "#5f4930", "#39a7ff": "#e9b962",
    "#061522": "#11191b", "#071724": "#11191b", "#092238": "#1d2423",
    "#155078": "#8a6b41", "#18577e": "#8a6b41", "#315774": "#736046",
    "#31516b": "#736046", "#7fa5c0": "#c2b59f", "#9bb2c7": "#c4b9a7",
    "#7898ad": "#c2b59f", "#7694aa": "#c2b59f", "#a9bfd0": "#c9c0b2",
    "#aac0d1": "#c9c0b2", "#b7c7d9": "#d4cbbd",
}


def reference_stylesheet(style):
    """Zamienia tylko kolory dekoracyjne; stany ostrzegawcze pozostają bez zmian."""
    import re
    return re.sub(r"#[0-9a-fA-F]{6}",
                  lambda match: REFERENCE_COLORS.get(match.group().lower(), match.group()),
                  style)
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
"Sieć":("#082038","#0aa9ff"),
"Android i ADB":("#092b29","#49dd72"),"Bezpieczeństwo":("#1b1740","#8264ff"),
"Android":("#092b29","#49dd72"),"AI i raporty":("#082038","#3cb9ff"),
"Pliki i dane":("#302a12","#f5c83c"),"Narzędzia zaawansowane":("#082038","#3cb9ff")}

