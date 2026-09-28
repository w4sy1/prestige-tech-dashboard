from __future__ import annotations

import copy
import json
import os
from datetime import datetime
from pathlib import Path


DATA_DIR = (
    Path(os.environ.get("LOCALAPPDATA") or Path.home())
    / "Prestige Tech"
    / "Dashboard"
)

DRAFT_PATH = DATA_DIR / "report-draft.json"


def _now():
    return datetime.now().isoformat(timespec="seconds")


def empty_draft():
    return {
        "schema": 2,
        "updated_at": _now(),
        "mode": "Raport techniczny",
        "client": "",
        "contact": "",
        "device": "",
        "serial": "",
        "status": "W trakcie",
        "problem": "",
        "diagnosis": "",
        "issues_critical": "",
        "issues_important": "",
        "issues_info": "",
        "actions_done": "",
        "actions_not_done": "",
        "recommendations": "",
        "notes": "",
        "work_minutes": 0,
        "price": 0.0,
        "system_snapshot": {
            "raw": {},
            "display": {},
            "text": "",
            "added_at": "",
        },
        "module_results": [],
    }


def save_draft(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    payload = copy.deepcopy(data)
    payload["schema"] = 2
    payload["updated_at"] = _now()

    temporary = DRAFT_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary, DRAFT_PATH)

    return payload


def load_draft():
    if not DRAFT_PATH.exists():
        return empty_draft()

    try:
        data = json.loads(
            DRAFT_PATH.read_text(encoding="utf-8-sig")
        )
    except (OSError, ValueError, TypeError):
        return empty_draft()

    result = empty_draft()
    result.update(data if isinstance(data, dict) else {})
    return result


def clear_draft():
    result = empty_draft()
    save_draft(result)
    return result


def update_system_snapshot(snapshot, display, text):
    draft = load_draft()

    draft["system_snapshot"] = {
        "raw": snapshot or {},
        "display": display or {},
        "text": text or "",
        "added_at": _now(),
    }

    return save_draft(draft)


def add_module_result(module_name, text, data=None):
    draft = load_draft()

    items = list(draft.get("module_results") or [])

    items.append(
        {
            "module": str(module_name),
            "text": str(text),
            "data": data,
            "added_at": _now(),
        }
    )

    draft["module_results"] = items[-100:]
    return save_draft(draft)