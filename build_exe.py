"""Zbuduj aktualny Dashboard PySide6 z oboma stylami."""

from pathlib import Path
import os
import subprocess
import sys

from app_version import APP_VERSION

root = Path(__file__).resolve().parent
if os.name != "nt":
    raise SystemExit("Windows EXE musi być budowany na Windows.")

name = f"Prestige-Tech-Dashboard-{APP_VERSION}"
resources = [(str(root / "modules.json"), ".")]
for resource in ("LICENSE", "THIRD_PARTY_NOTICES.txt", "config", "assets"):
    path = root / resource
    if path.exists():
        resources.append((str(path), resource if path.is_dir() else "."))

# PyInstaller wykrywa obcą wersję ICU; na Windows Qt używa systemowego icuuc.dll.
# Dołączona kopia 78.x powoduje ImportError przy ładowaniu QtWidgets.
spec = root / f"{name}.spec"
spec.write_text(
    "# -*- mode: python ; coding: utf-8 -*-\n"
    f"a = Analysis(['gui_pyside.py'], pathex={[str(root)]!r}, binaries=[], "
    f"datas={resources!r}, hiddenimports=[], hookspath=[], hooksconfig={{}}, "
    "runtime_hooks=[], excludes=[], noarchive=False, optimize=0)\n"
    "a.binaries = [item for item in a.binaries if item[0].lower() != 'icuuc.dll']\n"
    "pyz = PYZ(a.pure)\n"
    f"exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name={name!r}, "
    "debug=False, bootloader_ignore_signals=False, strip=False, upx=True, "
    "runtime_tmpdir=None, console=False, disable_windowed_traceback=False, "
    "argv_emulation=False, target_arch=None, codesign_identity=None, "
    f"entitlements_file=None, icon={[str(root / 'assets' / 'prestige_tech_app.ico')]!r})\n",
    encoding="utf-8",
)
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec)], cwd=root, check=True)
print(root / "dist" / f"{name}.exe")
