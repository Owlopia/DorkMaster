"""Command-line entrypoint for DorkMaster."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from dorkmaster import __author__, __company__, __version__
from dorkmaster.banner import display_banner
from dorkmaster.data_manager import DorkDatabase
from dorkmaster.scraper_engine import DorkScraper
from dorkmaster.search_engine import DorkSearcher
from dorkmaster.ui_controller import DorkMaster
from dorkmaster.utils import PathManager, Utils


def result_count(value: str) -> int:
    try:
        return DorkSearcher.normalize_count(int(value))
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error))


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="dorkmaster", description="Local GHDB catalogue and authorized-search helper")
    parser.add_argument("-v", "--version", action="version", version="DorkMaster {} — {} / {}".format(__version__, __company__, __author__))
    parser.add_argument("-s", "--search", metavar="KEYWORD", help="Search the local catalogue")
    parser.add_argument("-q", "--query", metavar="QUERY", help="Run a query in the browser or retrieve permitted terminal results")
    parser.add_argument("-b", "--browser", action="store_true", help="Open --query in the default browser")
    parser.add_argument("-n", "--num", type=result_count, default=10, metavar="COUNT", help="Result count, 1-100 (default: 10)")
    parser.add_argument("--sync", action="store_true", help="Download and reconcile the complete official GHDB catalogue")
    parser.add_argument("--update", action="store_true", help="Check the official GHDB catalogue for records since the last sync")
    parser.add_argument("--site", metavar="DOMAIN", help="Append a site: constraint to --query")
    parser.add_argument("-p", "--param", metavar="FILTER", help="Append a filter or keyword to --query")
    parser.add_argument("--stats", action="store_true", help="Show catalogue and storage statistics")
    parser.add_argument("--export", metavar="FILE", help="Export the local catalogue")
    parser.add_argument("--format", choices=("json", "csv", "txt"), default="json", help="Format for --export (default: json)")
    parser.add_argument("--banner", action="store_true", help="Show the banner and exit")
    parser.add_argument("--data-path", metavar="PATH", help="Use a specific local JSON catalogue")
    return parser.parse_args(args)


def render_stats(db: DorkDatabase) -> None:
    stats = db.get_stats()
    rows = [["Total dorks", stats["total_dorks"]], ["Categories", stats["categories_count"]],
            ["Database", stats["db_path"]], ["Last sync", stats["last_sync"]],
            ["Log", str(PathManager.get_default_log_path())]]
    print(Utils.format_table(rows, ["Property", "Value"]))


def strip_site_prefix(value: str) -> str:
    value = value.strip()
    return value[5:] if value.casefold().startswith("site:") else value


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.banner:
        display_banner(version=__version__, company=__company__, author=__author__)
        return 0
    db = DorkDatabase(args.data_path)
    if args.sync or args.update:
        added, considered = DorkScraper.sync(db, incremental=args.update)
        if considered:
            print("{} sync complete: {} new records ({} checked).".format("Incremental" if args.update else "Full", added, considered))
            return 0
        print("Synchronization failed: no records received from the official source.", file=sys.stderr)
        return 1
    if args.stats:
        render_stats(db)
        return 0
    if args.export:
        if Utils.export_data(args.export, db.dorks, args.format):
            print("Exported {} records to {}.".format(len(db.dorks), args.export))
            return 0
        print("Export failed.", file=sys.stderr)
        return 1
    if args.search:
        matches = db.search(args.search)
        rows = [[index, item["dork"][:55], item["category"][:24], item["date"]]
                for index, item in enumerate(matches[:args.num], start=1)]
        print(Utils.format_table(rows, ["#", "Query", "Category", "Date"]) if rows else "No matching dorks.")
        return 0
    if args.query:
        query = args.query.strip()
        if not query:
            print("Query cannot be empty.", file=sys.stderr)
            return 2
        if args.site:
            query = "{} site:{}".format(query, strip_site_prefix(args.site))
        if args.param:
            query = "{} {}".format(query, args.param.strip())
        if args.browser:
            url = DorkSearcher.build_google_url(query, args.num)
            print(url)
            return 0 if DorkSearcher.open_in_browser(query, args.num) else 1
        run = DorkSearcher.search_with_status(query, args.num)
        if run.results:
            print(Utils.format_table([[i, item["title"][:50], item["url"]] for i, item in enumerate(run.results, 1)], ["#", "Title", "URL"]))
        else:
            print("{}\nOpen this URL in a browser:\n{}".format(run.message(), run.url))
        return 0
    DorkMaster(args.data_path).interactive_menu()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
