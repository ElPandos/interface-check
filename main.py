import logging

from src.app import App
from src.core.config import setup_logging
from src.platform.enums.log import LogName

setup_logging(logging.DEBUG)


if __name__ in {"__main__", "__mp_main__"}:
    logger = logging.getLogger(LogName.MAIN.value)
    try:
        logger.debug("Main init")
        app = App()
    except Exception:
        logger.exception("Failed to initialise the application")
