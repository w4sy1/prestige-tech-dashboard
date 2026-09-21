import base64
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
import tkinter as tk
from tkinter import ttk

# Prestige Tech: do not leak PyInstaller private runtime variables to child processes.
for _prestige_key in list(os.environ):
    if _prestige_key.startswith("_PYI_"):
        os.environ.pop(_prestige_key, None)
os.environ["PYINSTALLER_RESET_ENVIRONMENT"] = "1"


CURRENT_VERSION = "1.1.2"
MANIFEST_URL = "https://raw.githubusercontent.com/w4sy1/prestige-tech/master/dashboard-manifest.json"
DASHBOARD_EXE = "Prestige-Tech-Dashboard.exe"
LAUNCHER_EXE = "Prestige-Tech-Launcher.exe"

MB_OK = 0
MB_ICONINFORMATION = 0x40
MB_ICONWARNING = 0x30
MB_YESNO = 0x04
MB_ICONQUESTION = 0x20
IDYES = 6
CREATE_NO_WINDOW = 0x08000000


def msg(text, title="Prestige Tech", flags=MB_OK | MB_ICONINFORMATION):
    return ctypes.windll.user32.MessageBoxW(None, text, title, flags)


def version_key(value):
    parts = []
    for token in str(value).strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in token if ch.isdigit())
        parts.append(int(digits or 0))
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def start_dashboard():
    dashboard = app_dir() / DASHBOARD_EXE
    if not dashboard.is_file():
        msg(f"Nie znaleziono pliku:\n{dashboard}",
            "Prestige Tech - blad uruchomienia",
            MB_OK | MB_ICONWARNING)
        return 2
    subprocess.Popen([str(dashboard)], cwd=str(app_dir()))
    return 0


def fetch_manifest():
    req = urllib.request.Request(
        MANIFEST_URL,
        headers={
            "User-Agent": f"Prestige-Tech-Launcher/{CURRENT_VERSION}",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        raw = response.read()

    obj = json.loads(raw.decode("utf-8-sig"))
    if obj.get("schema") != 1:
        raise ValueError("Nieobslugiwany schema manifestu.")
    stable = obj.get("stable")
    if not isinstance(stable, dict):
        raise ValueError("Brak wpisu stable.")
    return stable


class ProgressWindow:
    def __init__(self, version):
        self.cancelled = False
        self.root = tk.Tk()
        self.root.title("Prestige Tech - aktualizacja")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)

        width, height = 650, 285
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        frame = ttk.Frame(self.root, padding=26)
        frame.pack(fill="both", expand=True)

        self.title_label = ttk.Label(
            frame,
            text=f"Pobieranie Prestige Tech Dashboard v{version}",
            font=("Segoe UI", 13, "bold"),
        )
        self.title_label.pack(anchor="w")

        self.status = ttk.Label(frame, text="Laczenie z GitHub...", font=("Segoe UI", 9))
        self.status.pack(anchor="w", pady=(10, 11))

        self.progress = ttk.Progressbar(
            frame, orient="horizontal", mode="determinate",
            maximum=100, length=580
        )
        self.progress.pack(fill="x")

        self.detail = ttk.Label(frame, text="0%", font=("Segoe UI", 9))
        self.detail.pack(anchor="w", pady=(8, 0))

        self.security = ttk.Label(
            frame,
            text="Po pobraniu instalator zostanie sprawdzony SHA-256.",
            font=("Segoe UI", 8),
        )
        self.security.pack(anchor="w", pady=(14, 0))

        self.cancel_button = ttk.Button(frame, text="Anuluj", command=self.cancel)
        self.cancel_button.pack(anchor="e", pady=(14, 0))

        self.pump()

    def cancel(self):
        self.cancelled = True

    def pump(self):
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            self.cancelled = True

    def update_download(self, total, expected):
        pct = 0 if expected <= 0 else min(100, int(total * 100 / expected))
        self.progress["value"] = pct
        self.status.config(text="Pobieranie aktualizacji...")
        self.detail.config(
            text=f"{pct}%   |   {total/(1024*1024):.1f} MB / {expected/(1024*1024):.1f} MB"
        )
        self.pump()

    def verifying(self):
        self.progress["value"] = 100
        self.title_label.config(text="Weryfikacja aktualizacji")
        self.status.config(text="Sprawdzanie SHA-256 i rozmiaru pliku...")
        self.detail.config(text="Chronimy instalacje przed uszkodzonym lub podmienionym plikiem.")
        self.cancel_button.config(state="disabled")
        self.pump()

    def verified(self):
        self.title_label.config(text="Aktualizacja zweryfikowana")
        self.status.config(text="SHA-256 zgodny.")
        self.detail.config(text="Launcher zostanie zamkniety, potem pojawi sie UAC i instalator Windows.")
        self.pump()

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass


def download_verified(entry, ui):
    url = str(entry["installer_url"])
    expected_hash = str(entry["sha256"]).lower()
    expected_size = int(entry["size"])
    version = str(entry["version"])

    update_dir = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "PrestigeTech" / "updates"
    update_dir.mkdir(parents=True, exist_ok=True)

    final_path = update_dir / f"Prestige-Tech-Setup-{version}.exe"
    part_path = final_path.with_suffix(".exe.part")
    part_path.unlink(missing_ok=True)

    req = urllib.request.Request(url, headers={"User-Agent": f"Prestige-Tech-Launcher/{CURRENT_VERSION}"})

    sha = hashlib.sha256()
    total = 0

    with urllib.request.urlopen(req, timeout=30) as response, open(part_path, "wb") as out:
        while True:
            if ui.cancelled:
                part_path.unlink(missing_ok=True)
                raise InterruptedError("Aktualizacja anulowana.")
            chunk = response.read(512 * 1024)
            if not chunk:
                break
            out.write(chunk)
            sha.update(chunk)
            total += len(chunk)
            ui.update_download(total, expected_size)

    ui.verifying()

    if total != expected_size:
        part_path.unlink(missing_ok=True)
        raise ValueError(f"Nieprawidlowy rozmiar instalatora: {total} zamiast {expected_size}.")

    if sha.hexdigest().lower() != expected_hash:
        part_path.unlink(missing_ok=True)
        raise ValueError("SHA-256 pobranego instalatora jest niezgodny.")

    os.replace(part_path, final_path)
    ui.verified()
    return final_path


def handoff_to_installer(installer):
    pid = os.getpid()
    new_launcher = app_dir() / LAUNCHER_EXE

    def q(value):
        return str(value).replace("'", "''")

    ps = f"""
$ErrorActionPreference = 'Stop'
$launcherPid = {pid}
$installer = '{q(installer)}'
$newLauncher = '{q(new_launcher)}'

Wait-Process -Id $launcherPid -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 900

$process = Start-Process -FilePath $installer -Verb RunAs -ArgumentList '/SILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS' -Wait -PassThru

if ($process.ExitCode -eq 0) {{
    Start-Sleep -Milliseconds 700
    if (Test-Path -LiteralPath $newLauncher) {{
        Start-Process -FilePath $newLauncher
    }}
}}
"""
    encoded = base64.b64encode(ps.encode("utf-16le")).decode("ascii")

    subprocess.Popen(
        [
            "powershell.exe", "-NoProfile", "-WindowStyle", "Hidden",
            "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded
        ],
        creationflags=CREATE_NO_WINDOW,
        close_fds=True,
    )


def main():
    try:
        stable = fetch_manifest()
        remote_version = str(stable["version"])
    except Exception:
        return start_dashboard()

    if version_key(remote_version) <= version_key(CURRENT_VERSION):
        return start_dashboard()

    answer = msg(
        f"Dostepna jest nowa wersja Prestige Tech Dashboard.\n\n"
        f"Zainstalowana: v{CURRENT_VERSION}\n"
        f"Dostepna: v{remote_version}\n\n"
        f"Pobrac, sprawdzic SHA-256 i zainstalowac teraz?",
        "Prestige Tech - aktualizacja",
        MB_YESNO | MB_ICONQUESTION,
    )

    if answer != IDYES:
        return start_dashboard()

    ui = ProgressWindow(remote_version)

    try:
        installer = download_verified(stable, ui)
        if ui.cancelled:
            ui.close()
            return start_dashboard()

        ui.root.after(500)
        ui.pump()
        ui.close()

        handoff_to_installer(installer)
        return 0

    except InterruptedError:
        ui.close()
        return start_dashboard()

    except Exception as exc:
        ui.close()
        msg(
            f"Nie udalo sie wykonac aktualizacji.\n\n{exc}\n\n"
            f"Dashboard zostanie uruchomiony w obecnej wersji.",
            "Prestige Tech - aktualizacja",
            MB_OK | MB_ICONWARNING,
        )
        return start_dashboard()


if __name__ == "__main__":
    raise SystemExit(main())

