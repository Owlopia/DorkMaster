"""Interactive terminal interface for the catalogue and query workflows."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dorkmaster import __author__, __company__, __version__
from dorkmaster.banner import display_banner
from dorkmaster.data_manager import DorkDatabase
from dorkmaster.scraper_engine import DorkScraper
from dorkmaster.search_engine import DorkSearcher
from dorkmaster.utils import PathManager, Utils


class DorkMaster:
    """Application controller; business logic remains in the dedicated modules."""

    def __init__(self, data_path: Optional[str] = None) -> None:
        self.db = DorkDatabase(data_path)

    @staticmethod
    def _pause() -> None:
        try:
            input("\nPress Enter to continue...")
        except (EOFError, KeyboardInterrupt):
            pass

    def interactive_menu(self) -> None:
        while True:
            Utils.clear_screen()
            display_banner(version=__version__, company=__company__, author=__author__)
            print("Cached dorks: {}\n".format(self.db.get_stats()["total_dorks"]))
            print(" [1] Search local dorks")
            print(" [2] Check for new dorks (incremental update)")
            print(" [3] Sync complete GHDB library")
            print(" [4] Browse dorks by category")
            print(" [5] Quick execution (raw query)")
            print(" [6] View system statistics")
            print(" [7] Export local catalogue")
            print(" [8] Exit\n")
            try:
                choice = input("dorkmaster > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return
            if choice in {"8", "0", "q", "quit", "exit"}:
                return
            if choice == "1":
                self._menu_search()
            elif choice == "2":
                self._menu_sync(incremental=True)
            elif choice == "3":
                self._menu_sync(incremental=False)
            elif choice == "4":
                self._menu_categories()
            elif choice == "5":
                self._menu_direct_query()
            elif choice == "6":
                self._menu_stats()
            elif choice == "7":
                self._menu_export()
            else:
                print("Invalid option.")
                self._pause()

    def _menu_sync(self, *, incremental: bool) -> None:
        label = "incremental update" if incremental else "complete synchronization"
        try:
            if input("Start {}? (y/N): ".format(label)).strip().lower() not in {"y", "yes"}:
                return
            print("Downloading the official GHDB catalogue...")
            added, considered = DorkScraper.sync(self.db, incremental=incremental)
            if considered:
                print("Sync complete: {} new records ({} source records checked).".format(added, considered))
            else:
                print("No source records were received. Check connectivity and try again.")
        finally:
            self._pause()

    def _menu_search(self) -> None:
        try:
            query = input("Search keyword: ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if query:
            self._display_results_paged(self.db.search(query), "Search: {}".format(query))

    def _menu_categories(self) -> None:
        categories = self.db.get_categories()
        if not categories:
            print("No local categories. Run a complete synchronization first.")
            self._pause()
            return
        for index, category in enumerate(categories, start=1):
            print(" [{}] {}".format(index, category))
        try:
            selected = input("Category number (Enter to cancel): ").strip()
            index = int(selected) - 1
            if 0 <= index < len(categories):
                self._display_results_paged(self.db.filter_by_category(categories[index]), categories[index])
        except (ValueError, EOFError, KeyboardInterrupt):
            return

    def _menu_direct_query(self) -> None:
        try:
            query = input("Query: ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if query:
            self._modify_and_execute(query)

    def _menu_stats(self) -> None:
        stats = self.db.get_stats()
        rows = [["Total dorks", stats["total_dorks"]], ["Categories", stats["categories_count"]],
                ["Database", stats["db_path"]], ["Last database change", stats["last_modified"]],
                ["Last sync", stats["last_sync"]], ["Log", str(PathManager.get_default_log_path())]]
        print(Utils.format_table(rows, ["Property", "Value"]))
        self._pause()

    def _menu_export(self) -> None:
        try:
            format_name = input("Format (json/csv/txt) [json]: ").strip().lower() or "json"
            destination = input("Destination [dorks_export.{}]: ".format(format_name)).strip()
        except (EOFError, KeyboardInterrupt):
            return
        destination = destination or "dorks_export.{}".format(format_name)
        message = "Exported {} records to {}." if Utils.export_data(destination, self.db.dorks, format_name) else "Export failed."
        print(message.format(len(self.db.dorks), destination) if "{}" in message else message)
        self._pause()

    def _display_results_paged(self, items: List[Dict[str, Any]], title: str) -> None:
        if not items:
            print("No matching dorks.")
            self._pause()
            return
        page, page_size = 0, 15
        while True:
            start = page * page_size
            window = items[start:start + page_size]
            rows = [[start + index + 1, item["dork"][:55], item["category"][:24], item["date"]]
                    for index, item in enumerate(window)]
            print("\n{} — page {} of {}".format(title, page + 1, (len(items) + page_size - 1) // page_size))
            print(Utils.format_table(rows, ["#", "Query", "Category", "Date"]))
            try:
                action = input("[n]ext, [p]revious, number to inspect, [q]uit: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return
            if action in {"q", "quit", ""}:
                return
            if action in {"n", "next"} and start + page_size < len(items):
                page += 1
            elif action in {"p", "previous", "prev"} and page:
                page -= 1
            elif action.isdigit() and 0 < int(action) <= len(items):
                self._modify_and_execute(items[int(action) - 1]["dork"])

    def _modify_and_execute(self, base_query: str) -> None:
        query = base_query
        while True:
            print("\nActive query: {}".format(query))
            print(" [1] Append site constraint  [2] Append filter  [3] Edit  [4] Reset")
            print(" [t] Terminal results       [b] Open browser  [0] Back")
            try:
                choice = input("select > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return
            if choice in {"0", "q", "quit"}:
                return
            if choice == "1":
                domain = input("Domain: ").strip()
                if domain.casefold().startswith("site:"):
                    domain = domain[5:]
                if domain:
                    query = "{} site:{}".format(query, domain)
            elif choice == "2":
                filter_term = input("Filter or keyword: ").strip()
                if filter_term:
                    query = "{} {}".format(query, filter_term)
            elif choice == "3":
                query = input("New query: ").strip() or query
            elif choice == "4":
                query = base_query
            elif choice == "b":
                print(DorkSearcher.build_google_url(query))
                if not DorkSearcher.open_in_browser(query):
                    print("Browser could not be opened; copy the URL above.")
                self._pause()
            elif choice == "t":
                run = DorkSearcher.search_with_status(query)
                if run.results:
                    print(Utils.format_table([[i, item["title"][:50], item["url"]] for i, item in enumerate(run.results, 1)],
                                             ["#", "Title", "URL"]))
                else:
                    print("{}\nBrowser URL: {}".format(run.message(), run.url))
                self._pause()


class UIController:
    """Legacy display entrypoint retained for third-party callers."""
    display_banner = staticmethod(display_banner)


__all__ = ["DorkMaster", "UIController"]
