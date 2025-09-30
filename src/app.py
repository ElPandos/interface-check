from dotenv import load_dotenv

from src.ui.gui import Gui
from src.utils.configure import Configure


class App:
    def __init__(self) -> None:
        # Load env files
        load_dotenv()

        # Load configurations
        app_config = Configure().load()

        # Load GUI
        Gui(app_config)
