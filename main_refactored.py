"""Entry point for refactored application."""

import logging

from src.app_refactored import RefactoredApp
from src.utils.configure import setup_logging

if __name__ == "__main__":
    setup_logging(logging.INFO)
    app = RefactoredApp()
    app.run()
