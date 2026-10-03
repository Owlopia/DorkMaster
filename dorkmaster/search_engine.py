"""Query construction, terminal result retrieval, and browser launching."""

from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from typing import Dict, List

from dorkmaster.utils import Utils


@dataclass
class TerminalSearchRun:
    """The outcome of one terminal search without hiding provider failures."""

    query: str
    url: str
    results: List[Dict[str, str]]
    provider: str
    status: str = "ok"
    detail: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status == "ok"

    def message(self) -> str:
        messages = {
            "rate_limited": "The search provider rate-limited this terminal request.",
            "blocked": "The search provider declined this automated terminal request.",
            "unavailable": "The search provider could not be reached from this terminal.",
            "no_results": "No results were returned for this query.",
        }
        return messages.get(self.status, self.detail or "Terminal search did not complete.")


class DorkSearcher:
    MAX_RESULTS = 100

    @classmethod
    def normalize_count(cls, value: int) -> int:
        if not 1 <= value <= cls.MAX_RESULTS:
            raise ValueError("result count must be between 1 and {}".format(cls.MAX_RESULTS))
        return value

    @staticmethod
    def normalize_query(query: str) -> str:
        value = query.strip()
        if not value:
            raise ValueError("query cannot be empty")
        return value

    @classmethod
    def build_google_url(cls, query: str, num: int = 10) -> str:
        return "https://www.google.com/search?{}".format(
            urllib.parse.urlencode({"q": cls.normalize_query(query), "num": cls.normalize_count(num)})
        )

    @classmethod
    def open_in_browser(cls, query: str, num_results: int = 10) -> bool:
        try:
            return bool(webbrowser.open(cls.build_google_url(query, num_results)))
        except Exception as error:
            Utils.log_activity("Failed to open browser: {}".format(error))
            return False

    @staticmethod
    def _parse_google_results(content: str, limit: int) -> List[Dict[str, str]]:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return []
        results: List[Dict[str, str]] = []
        seen = set()
        for anchor in BeautifulSoup(content, "html.parser").select("a[href]"):
            href = anchor["href"]
            parsed = urllib.parse.urlparse(href)
            parameters = urllib.parse.parse_qs(parsed.query)
            if parsed.path == "/url" and parameters.get("q"):
                href = parameters["q"][0]
            elif parsed.path == "/url" and parameters.get("url"):
                href = parameters["url"][0]
            destination = urllib.parse.urlparse(href)
            if destination.scheme not in {"http", "https"} or destination.netloc.endswith("google.com") or href in seen:
                continue
            seen.add(href)
            results.append({"title": anchor.get_text(" ", strip=True) or href, "url": href, "snippet": ""})
            if len(results) >= limit:
                break
        return results

    @classmethod
    def search_with_status(cls, query: str, num_results: int = 10) -> TerminalSearchRun:
        """Search from a terminal and return an explicit, user-actionable result.

        Automated search is best-effort. The browser URL remains available for
        normal interactive search when a provider rejects scripted requests.
        """
        query = cls.normalize_query(query)
        limit = cls.normalize_count(num_results)
        url = cls.build_google_url(query, limit)
        try:
            from googlesearch import search as google_search
            results = [{"title": item, "url": item, "snippet": ""} for item in google_search(
                query, num_results=limit, sleep_interval=1
            )][:limit]
            return TerminalSearchRun(query, url, results, "googlesearch", "ok" if results else "no_results")
        except ImportError:
            # A standard-library fallback keeps native Linux packages usable.
            pass
        except Exception as error:
            detail = str(error)
            status = "rate_limited" if "429" in detail else "blocked" if "403" in detail else "unavailable"
            Utils.log_activity("Terminal search via googlesearch failed: {}".format(error))
            return TerminalSearchRun(query, url, [], "googlesearch", status, detail)

        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": Utils.get_random_user_agent(), "Accept-Language": "en-US,en;q=0.9"},
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                results = cls._parse_google_results(response.read().decode("utf-8", errors="replace"), limit)
            return TerminalSearchRun(query, url, results, "direct", "ok" if results else "no_results")
        except urllib.error.HTTPError as error:
            status = "rate_limited" if error.code == 429 else "blocked" if error.code in {401, 403} else "unavailable"
            Utils.log_activity("Terminal search HTTP error {}: {}".format(error.code, error))
            return TerminalSearchRun(query, url, [], "direct", status, str(error))
        except OSError as error:
            Utils.log_activity("Terminal search request failed: {}".format(error))
            return TerminalSearchRun(query, url, [], "direct", "unavailable", str(error))

    @classmethod
    def search(cls, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """Compatibility method returning only successful terminal results."""
        return cls.search_with_status(query, num_results).results


SearchEngine = DorkSearcher
__all__ = ["DorkSearcher", "SearchEngine", "TerminalSearchRun"]
