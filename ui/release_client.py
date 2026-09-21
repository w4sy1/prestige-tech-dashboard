from __future__ import annotations

import hashlib
import json
import socket
import urllib.error
import urllib.request
from pathlib import Path

MANIFEST_URL = (
    "https://raw.githubusercontent.com/"
    "w4sy1/prestige-tech/master/release-manifest.json"
)

USER_AGENT = "Prestige-Tech-Dashboard/1.0"


class ReleaseError(RuntimeError):
    pass


def _request(url: str, timeout: float = 4.0):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, application/octet-stream;q=0.9, */*;q=0.8",
            "Cache-Control": "no-cache",
        },
    )
    return urllib.request.urlopen(req, timeout=timeout)


def internet_probe(timeout: float = 1.2):
    """
    Lekki test Internetu na TCP/443. Nie opiera się na porcie DNS 53,
    który bywa blokowany mimo działającego Internetu.
    """
    targets = (
        ("github.com", 443),
        ("www.microsoft.com", 443),
    )

    dns_ok = False
    errors = []

    for host, port in targets:
        try:
            socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            dns_ok = True
        except OSError as exc:
            errors.append(f"DNS {host}: {exc}")
            continue

        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True, f"Połączenie TCP/443: {host}"
        except OSError as exc:
            errors.append(f"TCP {host}: {exc}")

    if not dns_ok:
        return False, "Nie działa rozwiązywanie DNS."

    return False, "DNS działa, ale test HTTPS/TCP 443 nie uzyskał połączenia."


def normalize_channel(value: str):
    return "beta" if str(value).strip().lower() == "beta" else "stable"


def version_key(value: str):
    """
    Prosty parser wersji 1.2.3, v1.2.3, 1.2.3-beta.1.
    Stable > prerelease dla tego samego numeru bazowego.
    """
    import re

    raw = str(value or "").strip().lower()
    if raw.startswith("v"):
        raw = raw[1:]

    match = re.match(r"^(\d+(?:\.\d+)*)(?:[-+](.*))?$", raw)

    if not match:
        return (0, (), -1, raw)

    nums = tuple(int(x) for x in match.group(1).split("."))
    suffix = match.group(2)

    stable_rank = 1 if not suffix else 0
    return (1, nums, stable_rank, suffix or "")


def compare_versions(local: str, remote: str):
    a = version_key(local)
    b = version_key(remote)

    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def sha256_file(path: Path):
    digest = hashlib.sha256()

    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


class ReleaseClient:
    def __init__(self, manifest_url: str = MANIFEST_URL):
        self.manifest_url = manifest_url

    def fetch_manifest(self):
        try:
            with _request(self.manifest_url, timeout=4.0) as response:
                data = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise ReleaseError(
                    "Manifest aktualizacji nie został jeszcze opublikowany w repozytorium prestige-tech."
                ) from exc
            raise ReleaseError(f"GitHub zwrócił HTTP {exc.code}.") from exc
        except urllib.error.URLError as exc:
            raise ReleaseError(f"Brak połączenia z GitHub: {exc.reason}") from exc
        except OSError as exc:
            raise ReleaseError(f"Błąd połączenia: {exc}") from exc

        try:
            manifest = json.loads(data.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReleaseError("Manifest aktualizacji ma nieprawidłowy format JSON.") from exc

        self.validate_manifest(manifest)
        return manifest

    def validate_manifest(self, manifest):
        if not isinstance(manifest, dict):
            raise ReleaseError("Manifest musi być obiektem JSON.")

        if int(manifest.get("schema", 0)) != 1:
            raise ReleaseError("Nieobsługiwana wersja schematu manifestu.")

        modules = manifest.get("modules")

        if not isinstance(modules, dict):
            raise ReleaseError("Manifest nie zawiera sekcji modules.")

    def module_entry(self, manifest, module_id: str, channel: str):
        modules = manifest.get("modules", {})
        raw = modules.get(module_id)

        if not isinstance(raw, dict):
            return None

        channel_key = normalize_channel(channel)
        entry = raw.get(channel_key)

        if not isinstance(entry, dict):
            if channel_key == "beta":
                entry = raw.get("stable")
            else:
                return None

        if not isinstance(entry, dict):
            return None

        return dict(entry)

    def download_verified(self, entry, destination: Path, progress=None):
        url = str(entry.get("asset_url") or "").strip()
        expected_hash = str(entry.get("sha256") or "").strip().lower()
        expected_size = entry.get("size")

        if not url.startswith("https://"):
            raise ReleaseError("Adres aktualizacji musi używać HTTPS.")

        if len(expected_hash) != 64 or any(
            char not in "0123456789abcdef"
            for char in expected_hash
        ):
            raise ReleaseError("Manifest nie zawiera poprawnego SHA-256.")

        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        temp = destination.with_suffix(destination.suffix + ".part")

        if temp.exists():
            temp.unlink()

        digest = hashlib.sha256()
        downloaded = 0

        try:
            with _request(url, timeout=10.0) as response, temp.open("wb") as output:
                header_size = response.headers.get("Content-Length")

                try:
                    total = int(header_size) if header_size else int(expected_size or 0)
                except (TypeError, ValueError):
                    total = 0

                while True:
                    chunk = response.read(1024 * 256)

                    if not chunk:
                        break

                    output.write(chunk)
                    digest.update(chunk)
                    downloaded += len(chunk)

                    if progress:
                        if total > 0:
                            progress(min(100, int(downloaded * 100 / total)))
                        else:
                            progress(-1)

            actual_hash = digest.hexdigest()

            if actual_hash != expected_hash:
                raise ReleaseError(
                    "SHA-256 pobranego pliku nie zgadza się z manifestem. "
                    "Plik nie zostanie zainstalowany."
                )

            if expected_size:
                try:
                    expected_int = int(expected_size)
                except (TypeError, ValueError):
                    expected_int = 0

                if expected_int > 0 and downloaded != expected_int:
                    raise ReleaseError(
                        f"Rozmiar pliku jest inny niż w manifeście "
                        f"({downloaded} != {expected_int})."
                    )

            temp.replace(destination)

            if progress:
                progress(100)

            return destination

        except Exception:
            try:
                if temp.exists():
                    temp.unlink()
            except OSError:
                pass
            raise
