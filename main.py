import logging

from src.app import App
from src.utils.configure import setup_logging

setup_logging(logging.DEBUG)

logger = logging.getLogger(__name__)


# sudo sysctl fs.inotify.max_user_watches=524288
# sudo sysctl fs.inotify.max_user_instances=512


if __name__ in {"__main__", "__mp_main__"}:
    try:
        logger.debug("Main init")
        app = App()
    except Exception:
        logger.exception("Failed to initialise the application")
