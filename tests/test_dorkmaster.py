import io
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from dorkmaster.cli import main, parse_args
from dorkmaster.data_manager import DorkDatabase
from dorkmaster.scraper_engine import DorkScraper
from dorkmaster.search_engine import DorkSearcher
from dorkmaster.utils import Utils


LEGACY_XML = b"""<?xml version='1.0'?><searchEngineSignature>
<signature><signatureReferenceNumber>42</signatureReferenceNumber><date>2026-10-01</date>
<category>Testing</category><querystring>site:example.test status</querystring>
<shortDescription>Example status</shortDescription><author>Tester</author></signature>
</searchEngineSignature>"""
CURRENT_XML = b"""<?xml version='1.0'?><feed>
<entry><id>99</id><date>2026-10-02</date><category>Current</category>
<query>site:example.test health</query><shortDescription>Health endpoint</shortDescription></entry>
</feed>"""


class DorkDatabaseTests(unittest.TestCase):
    def test_database_normalizes_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = DorkDatabase(Path(temporary) / "nested" / "dorks.json")
            self.assertEqual(1, database.add_dorks([{"query": "site:example.test", "id": "one"}]))
            self.assertEqual(0, database.add_dorks([{"dork": "ignored duplicate", "id": "one"}]))
            reloaded = DorkDatabase(database.db_path)
            self.assertEqual("site:example.test", reloaded.dorks[0]["dork"])

    def test_invalid_database_root_is_recoverable(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "dorks.json"
            path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
            self.assertEqual([], DorkDatabase(path).dorks)

    def test_export_csv_handles_different_record_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "records.csv"
            self.assertTrue(Utils.export_data(target, [{"id": "1"}, {"query": "two"}], "csv"))
            self.assertIn("query", target.read_text(encoding="utf-8"))


class ScraperTests(unittest.TestCase):
    def test_parser_supports_legacy_and_current_formats(self):
        legacy = DorkScraper.parse_archive(io.BytesIO(LEGACY_XML))
        current = DorkScraper.parse_archive(io.BytesIO(CURRENT_XML))
        self.assertEqual("42", legacy[0]["id"])
        self.assertEqual("site:example.test status", legacy[0]["dork"])
        self.assertEqual("99", current[0]["id"])

    def test_incremental_filter_keeps_same_day_records(self):
        records = DorkScraper.parse_archive(io.BytesIO(LEGACY_XML), since=date(2026, 10, 1))
        self.assertEqual(1, len(records))
        records = DorkScraper.parse_archive(io.BytesIO(LEGACY_XML), since=date(2026, 10, 2))
        self.assertEqual([], records)

    def test_sync_records_metadata_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = DorkDatabase(Path(temporary) / "dorks.json")
            source = [{"id": "1", "date": "2026-10-02", "dork": "site:example.test status"}]
            with patch.object(DorkScraper, "fetch_archive_feed", return_value=source) as fetch:
                self.assertEqual((1, 1), DorkScraper.sync(database, incremental=False))
                self.assertEqual((0, 1), DorkScraper.sync(database, incremental=True))
            self.assertEqual("incremental", database.get_stats()["last_sync_mode"])
            self.assertIsNotNone(fetch.call_args.kwargs["since"])


class CliTests(unittest.TestCase):
    def test_cli_rejects_invalid_result_count(self):
        with self.assertRaises(SystemExit):
            parse_args(["--num", "0"])

    def test_search_url_encodes_query_and_enforces_count(self):
        self.assertIn("q=site%3Aexample.test+status", DorkSearcher.build_google_url("site:example.test status"))
        with self.assertRaises(ValueError):
            DorkSearcher.build_google_url("x", 101)

    def test_cli_search_works_against_custom_catalogue(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "dorks.json"
            path.write_text(json.dumps([{"id": "1", "dork": "site:example.test status"}]), encoding="utf-8")
            self.assertEqual(0, main(["--data-path", str(path), "--search", "status"]))


class TerminalSearchTests(unittest.TestCase):
    def test_rate_limit_is_reported_without_an_exception(self):
        response = HTTPError("https://example.test", 429, "Too Many Requests", {}, None)
        with patch.dict(sys.modules, {"googlesearch": None}), patch("urllib.request.urlopen", side_effect=response):
            run = DorkSearcher.search_with_status("site:example.test status")
        self.assertEqual("rate_limited", run.status)
        self.assertIn("rate-limited", run.message())
        self.assertIn("site%3Aexample.test", run.url)

    def test_browser_uses_the_requested_result_limit(self):
        with patch("dorkmaster.search_engine.webbrowser.open", return_value=True) as open_browser:
            self.assertTrue(DorkSearcher.open_in_browser("site:example.test", 25))
        self.assertIn("num=25", open_browser.call_args.args[0])


class DesktopIntegrationTests(unittest.TestCase):
    def test_desktop_entry_is_terminal_backed_and_discoverable(self):
        desktop_file = Path(__file__).parents[1] / "dorkmaster.desktop"
        content = desktop_file.read_text(encoding="utf-8")
        self.assertIn("Exec=dorkmaster", content)
        self.assertIn("Terminal=true", content)
        self.assertIn("Icon=dorkmaster", content)
        self.assertIn("Categories=Security;Network;Utility;01-info-gathering;", content)
        self.assertIn("X-Kali-Package=dorkmaster", content)


if __name__ == "__main__":
    unittest.main()
