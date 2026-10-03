#!/usr/bin/env python3
"""
DorkMaster Pro - Entrypoint for legacy / direct script execution.
Redirects to the modular dorkmaster package.
"""
import sys
from dorkmaster.cli import main

if __name__ == "__main__":
    sys.exit(main())
