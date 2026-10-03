"""Compatibility imports for code written against pre-0.1 DorkMaster."""

from dorkmaster.data_manager import DorkDatabase
from dorkmaster.scraper_engine import DorkScraper
from dorkmaster.search_engine import DorkSearcher
from dorkmaster.ui_controller import DorkMaster

# These constants used to be imported by integrations. The presentation layer
# no longer depends on ANSI sequences, so they intentionally remain empty.
CYAN = GREEN = YELLOW = RED = MAGENTA = BLUE = WHITE = RESET = ""
DorkMasterPro = DorkMaster

__all__ = ["DorkDatabase", "DorkScraper", "DorkSearcher", "DorkMaster", "DorkMasterPro"]
