import logging

from src.app import App
from src.utils.system import setup_logging

setup_logging()


if __name__ in {"__main__", "__mp_main__"}:
    try:
        app = App()
    except Exception:
        logging.exception("Failed to initialise the application")
