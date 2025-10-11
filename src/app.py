import logging

from dotenv import load_dotenv

from src.ui.gui import Gui
from src.utils.configure import Configure

logger = logging.getLogger(__name__)


class App:
    """
    Main application class responsible for:
    - Loading environment variables
    - Reading configuration
    - Initializing and managing the GUI lifecycle
    """

    def __init__(self) -> None:
        """
        Initialize the application environment, configuration, and GUI.
        Handles graceful cleanup on user interrupt or initialization error.
        """
        logger.debug("Initializing App...")

        # Predefine _gui to avoid attribute errors later
        self._gui: Gui | None = None

        try:
            # Load .env variables
            load_dotenv()
            logger.info("Environment variables loaded.")

            # Load application configuration
            app_config = Configure().load()
            logger.info("Configuration loaded successfully.")

            # Initialize GUI
            self._gui = Gui(app_config)
            logger.info("GUI initialized successfully.")

            # Run the GUI
            self._gui.run()

        except KeyboardInterrupt as e:
            logger.info(f"User pressed Ctrl+C — Exiting gracefully: {e}")
            self._safe_disconnect()

        except Exception:
            # Catch-all for unexpected initialization failures
            logger.exception("Fatal error during App initialization")
            self._safe_disconnect()
            raise  # re-raise to make the error visible

    def _safe_disconnect(self) -> None:
        """
        Safely disconnect the GUI if it was initialized.
        Prevents AttributeError if _gui was never set.
        """
        if self._gui is not None:
            try:
                self._gui.disconnect()
                logger.debug("GUI disconnected cleanly.")
            except (AttributeError, RuntimeError) as e:
                logger.warning(f"Error while disconnecting GUI: {e}")
        else:
            logger.debug("No GUI instance to disconnect.")
