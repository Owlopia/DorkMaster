"""Core modules for DorkMaster."""

from dorkmaster.data_manager import DorkDatabase
from dorkmaster.scraper_engine import DorkScraper
from dorkmaster.search_engine import DorkSearcher
from dorkmaster.ui_controller import DorkMaster

# Color constants for terminal output (empty when color not supported)
CYAN = GREEN = YELLOW = RED = MAGENTA = BLUE = WHITE = RESET = ""

__all__ = ["DorkDatabase", "DorkScraper", "DorkSearcher", "DorkMaster"]
