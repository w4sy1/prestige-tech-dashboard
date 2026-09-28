from __future__ import annotations
import json, sys
from pathlib import Path
from PySide6.QtCore import QFileInfo
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileIconProvider
from module_manager import CONFIG_DIR

CONFIG_FILE = CONFIG_DIR / "module_icons.json"

def asset_root():
    base=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent.parent))
    return base/"assets"/"icons"

def icon_path(section,name):
    return asset_root()/section/(name+".svg")

class IconManager:
    def __init__(self,manager):
        self.manager=manager; CONFIG_DIR.mkdir(parents=True,exist_ok=True); self._data=self._load()
    def _load(self):
        try:
            if CONFIG_FILE.is_file():
                d=json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))
                return d if isinstance(d,dict) else {}
        except (OSError,ValueError): pass
        return {}
    def _save(self):
        CONFIG_FILE.write_text(json.dumps(self._data,ensure_ascii=False,indent=2),encoding="utf-8")
    def set_icon(self,module_id,path):
        p=Path(path)
        if not p.is_file(): raise FileNotFoundError("Nie znaleziono wskazanego pliku ikony.")
        self._data[module_id]=str(p); self._save()
    def clear_icon(self,module_id):
        self._data.pop(module_id,None); self._save()
    def custom_path(self,module_id):
        raw=self._data.get(module_id)
        if not raw:return None
        p=Path(raw); return p if p.is_file() else None
    def icon_for(self,module):
        custom=self.custom_path(module.id)
        if custom:
            if custom.suffix.lower()==".exe": return QFileIconProvider().icon(QFileInfo(str(custom)))
            icon=QIcon(str(custom))
            if not icon.isNull(): return icon
        default=icon_path("modules",module.id)
        if default.is_file(): return QIcon(str(default))
        return QIcon(str(icon_path("categories","advanced")))
