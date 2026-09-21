from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, urllib.request

APP_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "PrestigeTech"
MODULES_DIR = APP_DIR / "modules"
REPORTS_DIR = APP_DIR / "reports"
LOGS_DIR = APP_DIR / "logs"
CONFIG_DIR = APP_DIR / "config"

@dataclass(frozen=True)
class Module:
    id: str
    name: str
    category: str
    version: str
    description: str
    executable: str
    requirements: tuple[str, ...]
    risk: str
    help: str
    download_url: str | None = None
    sha256: str | None = None

    @classmethod
    def from_dict(cls, d):
        return cls(d["id"], d["name"], d["category"], d["version"], d["description"],
                   d["executable"], tuple(d.get("requirements", [])), d.get("risk","safe"),
                   d.get("help",""), d.get("download_url"), d.get("sha256"))

def manifest_path():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "modules.json"

class ModuleManager:
    def __init__(self):
        for p in (APP_DIR, MODULES_DIR, REPORTS_DIR, LOGS_DIR, CONFIG_DIR):
            p.mkdir(parents=True, exist_ok=True)
        data=json.loads(manifest_path().read_text(encoding="utf-8-sig"))
        if data.get("schema_version") != 1:
            raise ValueError("Nieobsługiwana wersja manifestu.")
        self.modules=[Module.from_dict(x) for x in data["modules"]]

    def categories(self):
        return sorted({m.category for m in self.modules})

    def module_dir(self,m): return MODULES_DIR / m.id
    def executable_path(self,m): return self.module_dir(m) / m.executable
    def is_installed(self,m): return self.executable_path(m).is_file()

    @staticmethod
    def sha256(path):
        h=hashlib.sha256()
        with Path(path).open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
        return h.hexdigest()

    def install_file(self,m,source):
        source=Path(source)
        if not source.is_file(): raise FileNotFoundError("Nie znaleziono pliku modułu.")
        if m.sha256 and self.sha256(source).lower()!=m.sha256.lower():
            raise ValueError("Suma SHA-256 nie zgadza się z manifestem.")
        target_dir=self.module_dir(m); target_dir.mkdir(parents=True,exist_ok=True)
        target=target_dir/m.executable
        shutil.copy2(source,target)
        (target_dir/"module.json").write_text(json.dumps({"id":m.id,"version":m.version},indent=2),encoding="utf-8")
        return target

    def download_install(self,m):
        if not m.download_url: raise ValueError("Brak skonfigurowanego GitHub Release dla tego modułu.")
        if not m.download_url.lower().startswith("https://"):
            raise ValueError("Moduł można pobrać wyłącznie przez HTTPS.")
        tmp=APP_DIR/(m.id+".download")
        try:
            req=urllib.request.Request(m.download_url,headers={"User-Agent":"PrestigeTech-Dashboard/1.0"})
            with urllib.request.urlopen(req,timeout=90) as src,tmp.open("wb") as dst:
                shutil.copyfileobj(src,dst)
            return self.install_file(m,tmp)
        finally:
            tmp.unlink(missing_ok=True)

    def uninstall(self,m):
        p=self.module_dir(m)
        if p.exists(): shutil.rmtree(p)

    def launch(self,m):
        exe=self.executable_path(m)
        if not exe.is_file(): raise FileNotFoundError("Moduł nie jest zainstalowany.")
        return subprocess.Popen([str(exe)],cwd=exe.parent)

    def find_local(self,m,roots):
        for root in map(Path,roots):
            for p in (root/m.executable, root/"PRESTIGE-TECH-EXE"/m.executable, root.parent/"PRESTIGE-TECH-EXE"/m.executable):
                if p.is_file(): return p
        return None


