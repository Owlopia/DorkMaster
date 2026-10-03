"""Small, dependency-light helpers shared by DorkMaster modules."""

from __future__ import annotations

import csv
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

USER_AGENTS = ("DorkMaster/0.1 (+https://github.com/Owlopia/DorkMaster)",
               "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36")


class PathManager:
    """Resolve XDG locations on Linux and usable per-user paths elsewhere."""
    @staticmethod
    def get_data_dir() -> Path:
        if os.name == "posix":
            return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "dorkmaster"
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "DorkMaster"

    @staticmethod
    def get_state_dir() -> Path:
        if os.name == "posix":
            return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "dorkmaster"
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "DorkMaster" / "state"

    @classmethod
    def get_default_db_path(cls) -> Path:
        return cls.get_data_dir() / "dorks.json"

    @classmethod
    def get_default_log_path(cls) -> Path:
        return cls.get_state_dir() / "activity.log"

    @staticmethod
    def get_seed_candidates() -> List[Path]:
        package_dir = Path(__file__).resolve().parent
        return [package_dir / "data" / "dorks.json", package_dir.parent / "data" / "dorks.json",
                Path("/usr/share/dorkmaster/dorks.json")]


class Utils:
    @staticmethod
    def get_random_user_agent() -> str:
        return random.choice(USER_AGENTS)

    @staticmethod
    def sleep_jitter(min_seconds: float = 0.2, max_seconds: float = 0.6) -> None:
        time.sleep(random.uniform(min_seconds, max_seconds))

    @staticmethod
    def clear_screen() -> None:
        if sys.stdout.isatty():
            os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def log_activity(message: str, log_file: Optional[Path] = None) -> None:
        target = log_file or PathManager.get_default_log_path()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write("[{}] {}\n".format(datetime.now().isoformat(timespec="seconds"), message))
        except OSError:
            pass

    @staticmethod
    def export_data(filepath: Union[str, Path], data: Iterable[Dict[str, Any]], format_type: str = "json") -> bool:
        target, records, format_name = Path(filepath).expanduser(), list(data), format_type.lower()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if format_name == "json":
                with target.open("w", encoding="utf-8") as handle:
                    json.dump(records, handle, indent=2, ensure_ascii=False)
                    handle.write("\n")
            elif format_name == "csv":
                fields = list(dict.fromkeys(key for row in records for key in row))
                if not fields:
                    return False
                with target.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                    writer.writeheader(); writer.writerows(records)
            elif format_name in {"txt", "text"}:
                with target.open("w", encoding="utf-8") as handle:
                    for index, record in enumerate(records, start=1):
                        handle.write("{}. {}\n".format(index, record.get("dork") or record.get("title") or record))
            else:
                return False
            return True
        except (OSError, TypeError, ValueError) as error:
            Utils.log_activity("Export error for {}: {}".format(target, error))
            return False

    @staticmethod
    def format_table(data: List[List[Any]], headers: List[str]) -> str:
        try:
            from tabulate import tabulate
            return tabulate(data, headers=headers, tablefmt="grid")
        except ImportError:
            return "\n".join([" | ".join(headers), *(" | ".join(map(str, row)) for row in data)])


def safe_exit(code: int = 0) -> None:
    raise SystemExit(code)
