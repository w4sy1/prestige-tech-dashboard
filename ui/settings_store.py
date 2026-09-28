from __future__ import annotations
import json
from module_manager import CONFIG_DIR

SETTINGS_FILE = CONFIG_DIR / "dashboard_settings.json"

DEFAULTS = {
    "channel": "Stable",
    "language": "Polski",
    "portable_default": False,
    "confirm_system_changes": True,
    "check_updates_on_start": True,
}

def load_settings():
    data = dict(DEFAULTS)
    try:
        if SETTINGS_FILE.is_file():
            raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8-sig"))
            if isinstance(raw, dict):
                for key in DEFAULTS:
                    if key in raw:
                        data[key] = raw[key]
    except (OSError, ValueError):
        pass
    return data

def save_settings(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    clean = dict(DEFAULTS)
    clean.update({k: data[k] for k in DEFAULTS if k in data})
    SETTINGS_FILE.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")

def reset_settings():
    save_settings(DEFAULTS)
    return dict(DEFAULTS)
