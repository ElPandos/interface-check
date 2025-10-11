import logging
from dotenv import load_dotenv

from src.ui.gui import Gui
from src.utils.configure import Configure


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
        logging.debug("Initializing App...")

        # Predefine _gui to avoid attribute errors later
        self._gui: Gui | None = None

        try:
            # Load .env variables
            load_dotenv()
            logging.info("Environment variables loaded.")

            # Load application configuration
            app_config = Configure().load()
            logging.info("Configuration loaded successfully.")

            # Initialize GUI
            self._gui = Gui(app_config)
            logging.info("GUI initialized successfully.")

            # Run the GUI
            self._gui.run()

        except KeyboardInterrupt as e:
            logging.info(f"User pressed Ctrl+C — Exiting gracefully: {e}")
            self._safe_disconnect()

        except Exception as e:
            # Catch-all for unexpected initialization failures
            logging.exception(f"Fatal error during App initialization: {e}")
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
                logging.debug("GUI disconnected cleanly.")
            except Exception as e:
                logging.warning(f"Error while disconnecting GUI: {e}")
        else:
            logging.debug("No GUI instance to disconnect.")
