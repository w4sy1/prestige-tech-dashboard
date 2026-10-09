"""Złóż Dashboard i 10 Centrów w sprawdzaną paczkę Windows."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

from app_version import APP_VERSION

ROOT = Path(__file__).resolve().parent
CENTERS_ROOT = ROOT.parent / "prestige-tech" / "dist" / "centers"
DIST = ROOT / "dist"
DASHBOARD = DIST / f"Prestige-Tech-Dashboard-{APP_VERSION}.exe"
BUNDLE_NAME = f"Prestige-Tech-{APP_VERSION}-Windows"
BUNDLE = DIST / "bundles" / BUNDLE_NAME
ZIP = DIST / f"{BUNDLE_NAME}.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if os.name != "nt":
        raise SystemExit("Paczka EXE wymaga Windows.")
    modules = json.loads((ROOT / "modules.json").read_text(encoding="utf-8-sig"))["modules"]
    executables = [(DASHBOARD, DASHBOARD.name)] + [
        (CENTERS_ROOT / module["executable"], f"centers/{module['executable']}")
        for module in modules
    ]
    files = executables + [
        (ROOT / "LICENSE", "LICENSE"),
        (ROOT / "THIRD_PARTY_NOTICES.txt", "THIRD_PARTY_NOTICES-Dashboard.txt"),
        (ROOT.parent / "prestige-tech" / "THIRD_PARTY_NOTICES.txt", "THIRD_PARTY_NOTICES-Centers.txt"),
    ]
    missing = [str(source) for source, _ in files if not source.is_file()]
    if missing:
        raise SystemExit("Brak EXE:\n" + "\n".join(missing))
    if BUNDLE.exists() or ZIP.exists():
        raise SystemExit(f"Paczka {BUNDLE_NAME} już istnieje. Zachowano ją bez nadpisania.")

    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    for source, label in executables:
        completed = subprocess.run([str(source), "--smoke"], env=env, timeout=45, check=False)
        if completed.returncode:
            raise SystemExit(f"Test uruchomienia nie przeszedł: {label} (kod {completed.returncode})")
        print(f"PASS: {label}", flush=True)

    BUNDLE.mkdir(parents=True)
    sums = []
    for source, label in files:
        target = BUNDLE / label
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        sums.append(f"{sha256(target)}  {label}")
    (BUNDLE / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    (BUNDLE / "START.txt").write_text(
        f"PRESTIGE TECH {APP_VERSION}\n"
        f"Uruchom {DASHBOARD.name}.\n"
        "Centra znajdują się w folderze centers i są wykrywane przez Dashboard.\n"
        "Każdy EXE przeszedł test uruchomienia --smoke na komputerze budującym.\n"
        "Operacje administracyjne, urządzenia fizyczne i funkcje sieciowe wymagają osobnych testów.\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(BUNDLE.rglob("*")):
            if path.is_file():
                archive.write(path, f"{BUNDLE_NAME}/{path.relative_to(BUNDLE).as_posix()}")
    print(ZIP)


if __name__ == "__main__":
    main()
