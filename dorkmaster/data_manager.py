"""Persistent storage for the local GHDB catalogue."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Union

from dorkmaster.utils import PathManager, Utils

Record = Dict[str, Any]
PathLike = Union[str, Path]


class DorkDatabase:
    """Read, normalize, search, and safely persist dork records."""

    def __init__(self, db_path: Optional[PathLike] = None) -> None:
        self._seed_enabled = db_path is None
        self.db_path = Path(db_path) if db_path else PathManager.get_default_db_path()
        self.metadata_path = self.db_path.with_suffix(self.db_path.suffix + ".meta.json")
        self.dorks: List[Record] = []
        self._seen_ids: Set[str] = set()
        self._load()

    @staticmethod
    def normalize(item: Any) -> Optional[Record]:
        """Convert an upstream or legacy record into the supported schema."""
        if not isinstance(item, dict):
            return None
        query = str(item.get("dork") or item.get("query") or item.get("querystring")
                    or item.get("url_title") or "").strip()
        if not query:
            return None
        record_id = str(item.get("id") or item.get("signatureReferenceNumber") or "").strip()
        if not record_id:
            record_id = "query-" + hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
        return {
            "id": record_id,
            "date": str(item.get("date") or "").strip(),
            "url_title": str(item.get("url_title") or item.get("shortDescription") or query).strip(),
            "dork": query,
            "category": str(item.get("category") or "General").strip() or "General",
            "author": str(item.get("author") or "Unknown").strip() or "Unknown",
        }

    def _load_json_list(self, path: Path) -> List[Record]:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, list):
            raise ValueError("database root must be a JSON array")
        return [record for raw in value if (record := self.normalize(raw))]

    def _load(self) -> None:
        if self.db_path.exists():
            try:
                self.dorks = self._load_json_list(self.db_path)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                Utils.log_activity("Failed to read database {}: {}".format(self.db_path, error))
                self.dorks = []
            self._reindex()
            return
        if not self._seed_enabled:
            return
        for seed in PathManager.get_seed_candidates():
            if not seed.is_file():
                continue
            try:
                self.dorks = self._load_json_list(seed)
                self._reindex()
                self.save()
                return
            except (OSError, ValueError, json.JSONDecodeError) as error:
                Utils.log_activity("Failed to load bundled catalogue {}: {}".format(seed, error))
        self.dorks = []

    def _reindex(self) -> None:
        self._seen_ids = {record["id"] for record in self.dorks}

    @staticmethod
    def _atomic_json_write(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
            os.replace(str(temporary_path), str(path))
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    def save(self) -> bool:
        try:
            self._atomic_json_write(self.db_path, self.dorks)
            return True
        except (OSError, TypeError, ValueError) as error:
            Utils.log_activity("Database save error for {}: {}".format(self.db_path, error))
            return False

    def add_dorks(self, new_items: Iterable[Any]) -> int:
        additions: List[Record] = []
        candidate_ids = set(self._seen_ids)
        for raw in new_items:
            item = self.normalize(raw)
            if item and item["id"] not in candidate_ids:
                additions.append(item)
                candidate_ids.add(item["id"])
        if not additions:
            return 0
        self.dorks.extend(additions)
        if not self.save():
            del self.dorks[-len(additions):]
            return 0
        self._seen_ids = candidate_ids
        return len(additions)

    def search(self, query: str) -> List[Record]:
        terms = [term.casefold() for term in query.split() if term]
        if not terms:
            return list(self.dorks)
        fields = ("dork", "url_title", "category", "author", "date")
        return [item for item in self.dorks if all(
            term in " ".join(str(item.get(field, "")) for field in fields).casefold()
            for term in terms
        )]

    def get_categories(self) -> List[str]:
        return sorted({item["category"] for item in self.dorks}, key=str.casefold)

    def filter_by_category(self, category: str) -> List[Record]:
        normalized = category.strip().casefold()
        return [item for item in self.dorks if item["category"].casefold() == normalized]

    def get_sync_metadata(self) -> Record:
        try:
            with self.metadata_path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError, json.JSONDecodeError):
            return {}

    def record_sync(self, *, mode: str, source_count: int, added_count: int) -> None:
        value = {"last_sync": datetime.now(timezone.utc).isoformat(), "mode": mode,
                 "source_count": source_count, "added_count": added_count}
        try:
            self._atomic_json_write(self.metadata_path, value)
        except (OSError, TypeError, ValueError) as error:
            Utils.log_activity("Sync metadata save error for {}: {}".format(self.metadata_path, error))

    def get_stats(self) -> Record:
        metadata = self.get_sync_metadata()
        modified = "Never"
        try:
            if self.db_path.exists():
                modified = datetime.fromtimestamp(self.db_path.stat().st_mtime).isoformat(sep=" ", timespec="seconds")
        except OSError:
            pass
        return {"total_dorks": len(self.dorks), "categories_count": len(self.get_categories()),
                "db_path": str(self.db_path), "last_modified": modified,
                "last_sync": metadata.get("last_sync", "Never"),
                "last_sync_mode": metadata.get("mode", "Never")}


DataManager = DorkDatabase
__all__ = ["DataManager", "DorkDatabase", "Record"]
