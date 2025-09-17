from src.ui.gui import Gui


class App:
    def __init__(self) -> None:
        # # Initialize settings by loading environment variables
        # self._settings = Settings()

        # # Assign configuration file paths based on loaded environment settings
        # self.config_file = self._settings.config_file
        # self.settings_file = self._settings.settings_file

        # # Validate that all required file paths are present in the environment
        # if not self.config_file or not self.log_file or not self.settings_file:

        #     raise ValueError("Missing CONFIG_FILE, LOG_FILE, or SETTINGS_FILE in .env")

        # try:
        #     # Read and parse JSON configuration from the settings file
        #     with open(self.settings_file) as f:
        #         config = json.load(f)
        # except Exception as e:
        #     # Raise an error if there is any issue reading or parsing the file
        #     raise FileExistsError(f"Read file error: {e}") from e

        # # Extract values "A" and "B" from the configuration dictionary
        # self.a = config.get("A")
        # self.b = config.get("B")

        gui = Gui()
