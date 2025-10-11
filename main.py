import logging

from src.app import App
from src.utils.system import setup_logging

setup_logging(logging.DEBUG)

# sudo sysctl fs.inotify.max_user_watches=524288
# sudo sysctl fs.inotify.max_user_instances=512


if __name__ in {"__main__", "__mp_main__"}:
    try:
        logging.debug("Main init")
        app = App()
    except Exception as e:
        logging.exception(f"Failed to initialise the application: {e}")
