"""Synchronization with the public Exploit-DB GHDB feed."""

from __future__ import annotations

import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from typing import BinaryIO, List, Optional, Tuple

from dorkmaster.data_manager import DorkDatabase, Record
from dorkmaster.utils import Utils


class DorkScraper:
    """Download and stream-parse the official GHDB XML catalogue.

    The old web-page DataTables endpoint is not used: it is an undocumented UI
    endpoint whose response shape has changed repeatedly.
    """

    GHDB_ARCHIVE_URL = "https://gitlab.com/exploit-database/exploitdb/-/raw/main/ghdb.xml"

    @staticmethod
    def _tag_name(element: ET.Element) -> str:
        return element.tag.rsplit("}", 1)[-1]

    @classmethod
    def _value(cls, element: ET.Element, *names: str) -> str:
        wanted = set(names)
        for child in element.iter():
            if cls._tag_name(child) in wanted and child.text:
                return html.unescape(child.text).strip()
        return ""

    @classmethod
    def _record_from_element(cls, element: ET.Element) -> Optional[Record]:
        query = cls._value(element, "query", "querystring")
        if not query:
            return None
        return {
            "id": cls._value(element, "id", "signatureReferenceNumber", "signatureId"),
            "date": cls._value(element, "date", "dateAdded"),
            "url_title": cls._value(element, "shortDescription", "title") or query,
            "dork": query,
            "category": cls._value(element, "category") or "General",
            "author": cls._value(element, "author") or "Unknown",
        }

    @classmethod
    def parse_archive(cls, stream: BinaryIO, since: Optional[date] = None) -> List[Record]:
        """Parse legacy ``signature`` and current ``entry`` GHDB records.

        Iterative parsing keeps the upstream catalogue out of a full object
        tree while supporting the XML forms Exploit-DB has published.
        """
        records: List[Record] = []
        for _, element in ET.iterparse(stream, events=("end",)):
            if cls._tag_name(element) not in {"entry", "signature"}:
                continue
            record = cls._record_from_element(element)
            element.clear()
            if not record:
                continue
            if since and record["date"]:
                try:
                    if date.fromisoformat(record["date"][:10]) < since:
                        continue
                except ValueError:
                    pass
            records.append(record)
        return records

    @classmethod
    def fetch_archive_feed(cls, since: Optional[date] = None) -> List[Record]:
        request = urllib.request.Request(
            cls.GHDB_ARCHIVE_URL,
            headers={"User-Agent": Utils.get_random_user_agent(), "Accept": "application/xml,text/xml"},
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return cls.parse_archive(response, since=since)
        except (OSError, ET.ParseError) as error:
            Utils.log_activity("GHDB archive fetch error: {}".format(error))
            return []

    @staticmethod
    def _last_sync_day(db: DorkDatabase) -> Optional[date]:
        raw = str(db.get_sync_metadata().get("last_sync", ""))[:10]
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None

    @classmethod
    def sync(cls, db: DorkDatabase, *, incremental: bool = False) -> Tuple[int, int]:
        """Synchronize and return ``(new_records, source_records_considered)``."""
        records = cls.fetch_archive_feed(since=cls._last_sync_day(db) if incremental else None)
        if not records:
            return 0, 0
        added = db.add_dorks(records)
        db.record_sync(mode="incremental" if incremental else "full", source_count=len(records), added_count=added)
        return added, len(records)

    @classmethod
    def sync_all(cls, db: DorkDatabase, **_: object) -> int:
        """Compatibility entrypoint for callers of releases before 0.1."""
        return cls.sync(db, incremental=False)[0]

    @classmethod
    def sync_incremental(cls, db: DorkDatabase) -> int:
        return cls.sync(db, incremental=True)[0]


ScraperEngine = DorkScraper
__all__ = ["DorkScraper", "ScraperEngine"]
