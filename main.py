import logging
import traceback

from src.app import App

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

if __name__ in {"__main__", "__mp_main__"}:
    try:
        app = App()
    except Exception as e:
        logging.error(f"Error: {e}")
        logging.error(f"Error traceback: {traceback.format_exc()}")
