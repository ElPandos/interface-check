import logging

from dotenv import load_dotenv

from src.ui.gui import Gui
from src.utils.configure import Configure


class App:
    def __init__(self) -> None:
        logging.debug("App init")

        # Load env file
        load_dotenv()

        # Load configuration file
        app_config = Configure().load()

        # Load GUI
        try:
            self.gui = Gui(app_config)
        except KeyboardInterrupt as e:
            logging.info(f"User pressed 'Ctrl+c' - Exiting: {e}")
            self.gui.disconnect()
