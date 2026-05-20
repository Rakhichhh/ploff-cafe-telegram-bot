"""Safe JSON read/write helpers.

The project uses JSON files as local persistent storage. All functions handle
file-system and JSON errors so the bot does not crash during a live demo.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: str | Path, default: Any) -> Any:
    """Read JSON safely and return default on errors."""
    file_path = Path(path)
    try:
        if not file_path.exists():
            write_json(file_path, default)
            return default

        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        backup_path = file_path.with_suffix(file_path.suffix + ".broken")
        try:
            file_path.rename(backup_path)
        except OSError:
            pass
        write_json(file_path, default)
        return default

    except (OSError, TypeError):
        return default


def write_json(path: str | Path, data: Any) -> bool:
    """Write JSON safely. Return True if writing was successful."""
    file_path = Path(path)
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return True
    except (OSError, TypeError):
        return False


def append_json_record(path: str | Path, record: dict) -> bool:
    """Append one dictionary record to a JSON list file."""
    records = read_json(path, default=[])
    if not isinstance(records, list):
        records = []
    records.append(record)
    return write_json(path, records)
