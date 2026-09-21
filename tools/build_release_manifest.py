from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = "w4sy1/prestige-tech"


def sha256(path: Path):
    h = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


def load_modules(path: Path):
    data = json.loads(
        path.read_text(
            encoding="utf-8-sig",
        )
    )

    if isinstance(data, dict):
        modules = data.get("modules", [])
    else:
        modules = data

    if not isinstance(modules, list):
        raise SystemExit("Nieprawidłowe modules.json")

    return modules


def main():
    parser = argparse.ArgumentParser(
        description="Buduje release-manifest.json dla Prestige Tech."
    )

    parser.add_argument(
        "--exe-dir",
        required=True,
        help="Folder z gotowymi EXE.",
    )

    parser.add_argument(
        "--tag",
        required=True,
        help="Tag GitHub Release, np. modules-v0.3.1.",
    )

    parser.add_argument(
        "--channel",
        choices=("stable", "beta"),
        default="stable",
    )

    parser.add_argument(
        "--modules",
        default="modules.json",
    )

    parser.add_argument(
        "--out",
        default="release-manifest.json",
    )

    args = parser.parse_args()

    exe_dir = Path(args.exe_dir)
    modules_path = Path(args.modules)
    out = Path(args.out)

    modules = load_modules(
        modules_path
    )

    manifest = {
        "schema": 1,
        "repository": REPO,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "modules": {},
    }

    missing = []

    for module in modules:
        module_id = str(
            module.get("id") or ""
        ).strip()

        executable = str(
            module.get("executable") or ""
        ).strip()

        version = str(
            module.get("version") or ""
        ).strip()

        name = str(
            module.get("name") or module_id
        ).strip()

        if not module_id or not executable or not version:
            continue

        exe = exe_dir / executable

        record = manifest["modules"].setdefault(
            module_id,
            {
                "name": name,
                "stable": None,
                "beta": None,
            },
        )

        if not exe.is_file():
            missing.append(
                executable
            )
            continue

        record[args.channel] = {
            "version": version,
            "asset_url": (
                f"https://github.com/{REPO}/releases/download/"
                f"{args.tag}/{executable}"
            ),
            "sha256": sha256(exe),
            "size": exe.stat().st_size,
            "changelog": "",
        }

    out.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "Manifest:",
        out.resolve(),
    )

    print(
        "Moduły:",
        len(manifest["modules"]),
    )

    if missing:
        print(
            "\nBrakujące EXE:"
        )

        for item in missing:
            print(
                " -",
                item,
            )


if __name__ == "__main__":
    main()
