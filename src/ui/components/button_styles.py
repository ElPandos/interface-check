"""Common button styles and configurations."""


class ButtonStyles:
    """Centralized button styling constants."""

    # Standard button styles - lighter versions
    GRAY_BUTTON = "bg-gray-300 hover:bg-gray-400 text-gray-800 px-2 py-1 text-xs"
    BLUE_BUTTON = "bg-blue-300 hover:bg-blue-400 text-blue-900 px-2 py-1 text-xs"
    RED_BUTTON = "bg-red-300 hover:bg-red-400 text-red-900 px-2 py-1 text-xs"
    GREEN_BUTTON = "bg-green-300 hover:bg-green-400 text-green-900 px-2 py-1 text-xs"

    # Dialog button styles - lighter
    DIALOG_BUTTON = "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-lg"

    # Disabled button styles - super light grey
    DISABLED_BUTTON = "bg-gray-100 text-gray-400 cursor-not-allowed px-2 py-1 text-xs"
    DISABLED_DIALOG_BUTTON = "bg-gray-100 text-gray-400 cursor-not-allowed px-6 py-2 rounded-lg"

    # Card styles
    CARD_BASE = "w-full mb-4"
    CARD_CONTENT = "w-full p-4 bg-gray-50 border border-gray-200 mb-4"
    CARD_DIALOG = "w-96 bg-white border border-gray-300 shadow-lg"
