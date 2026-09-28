from __future__ import annotations

import json
import sys
from pathlib import Path

# Uruchamiany bezpośrednio z folderu tools, więc dodajemy katalog główny repo do sys.path.
REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from module_manager import MODULES_DIR, ModuleManager
from ui.release_client import sha256_file

MANIFEST = REPO_ROOT / "release-manifest.json"


def main():
    if not MANIFEST.is_file():
        raise SystemExit(f"Brak release-manifest.json: {MANIFEST}")

    manifest = json.loads(
        MANIFEST.read_text(encoding="utf-8-sig")
    )

    modules_remote = manifest.get("modules", {})

    if not isinstance(modules_remote, dict):
        raise SystemExit("Nieprawidłowa sekcja modules w manifeście.")

    mm = ModuleManager()

    verified = []
    skipped = []
    mismatched = []

    for module in mm.modules:
        if not mm.is_installed(module):
            skipped.append((module.name, "niezainstalowany"))
            continue

        remote = modules_remote.get(module.id) or {}
        stable = remote.get("stable") if isinstance(remote, dict) else None

        if not isinstance(stable, dict):
            skipped.append((module.name, "brak wpisu stable w manifeście"))
            continue

        expected_hash = str(stable.get("sha256") or "").strip().lower()
        version = str(stable.get("version") or "").strip()

        if len(expected_hash) != 64 or not version:
            skipped.append((module.name, "brak SHA-256 lub wersji"))
            continue

        try:
            exe = Path(mm.executable_path(module))
        except Exception as exc:
            skipped.append((module.name, f"nie można ustalić EXE: {exc}"))
            continue

        if not exe.is_file():
            skipped.append((module.name, f"brak EXE: {exe}"))
            continue

        actual_hash = sha256_file(exe)

        if actual_hash != expected_hash:
            mismatched.append(
                (
                    module.name,
                    actual_hash,
                    expected_hash,
                )
            )
            continue

        target = MODULES_DIR / module.id
        target.mkdir(parents=True, exist_ok=True)

        (target / "version.txt").write_text(
            version,
            encoding="utf-8",
        )

        verified.append((module.name, version))

    print("")
    print("ZWERYFIKOWANE:", len(verified))
    for name, version in verified:
        print(f"  OK  {name} -> v{version}")

    print("")
    print("POMINIĘTE:", len(skipped))
    for name, reason in skipped:
        print(f"  --  {name}: {reason}")

    print("")
    print("NIEZGODNE SHA-256:", len(mismatched))
    for name, actual, expected in mismatched:
        print(f"  !!  {name}")
        print(f"      lokalny:  {actual}")
        print(f"      manifest: {expected}")

    print("")
    print(
        f"PODSUMOWANIE: verified={len(verified)} "
        f"skipped={len(skipped)} mismatched={len(mismatched)}"
    )

    if mismatched:
        print(
            "\nUWAGA: dla plików z niezgodnym SHA-256 NIE zapisano wersji."
        )


if __name__ == "__main__":
    main()
