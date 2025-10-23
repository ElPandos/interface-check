"""Comprehensive UI theme system with light and dark modes."""

from dataclasses import dataclass
from typing import ClassVar

from nicegui import ui


@dataclass(frozen=True)
class LightTheme:
    """Light theme UI styling configuration - Modern and eye-friendly."""

    # Base Colors - Warm whites and soft grays
    PRIMARY_BG = "bg-slate-50"
    SECONDARY_BG = "bg-stone-50"
    TERTIARY_BG = "bg-neutral-100"
    BORDER_COLOR = "border-stone-200"
    TEXT_PRIMARY = "text-slate-700"
    TEXT_SECONDARY = "text-slate-600"
    TEXT_MUTED = "text-slate-500"

    # Buttons - Standard - Softer, warmer tones
    GRAY_BUTTON = "bg-stone-200 hover:bg-stone-300 text-slate-700 px-4 py-2 rounded-lg"
    BLUE_BUTTON = "bg-sky-200 hover:bg-sky-300 text-sky-800 px-4 py-2 rounded-lg"
    RED_BUTTON = "bg-rose-200 hover:bg-rose-300 text-rose-800 px-4 py-2 rounded-lg"
    GREEN_BUTTON = "bg-emerald-200 hover:bg-emerald-300 text-emerald-800 px-4 py-2 rounded-lg"
    ORANGE_BUTTON = "bg-amber-200 hover:bg-amber-300 text-amber-800 px-4 py-2 rounded-lg"
    PURPLE_BUTTON = "bg-violet-200 hover:bg-violet-300 text-violet-800 px-4 py-2 rounded-lg"
    TEAL_BUTTON = "bg-teal-200 hover:bg-teal-300 text-teal-800 px-4 py-2 rounded-lg"

    # Buttons - Small
    GRAY_BUTTON_SM = "bg-stone-200 hover:bg-stone-300 text-slate-700 px-2 py-1 text-xs rounded-lg"
    BLUE_BUTTON_SM = "bg-sky-200 hover:bg-sky-300 text-sky-800 px-2 py-1 text-xs rounded-lg"
    RED_BUTTON_SM = "bg-rose-200 hover:bg-rose-300 text-rose-800 px-2 py-1 text-xs rounded-lg"
    GREEN_BUTTON_SM = (
        "bg-emerald-200 hover:bg-emerald-300 text-emerald-800 px-2 py-1 text-xs rounded-lg"
    )

    # Buttons - Special - Modern accent colors
    PRIMARY_BUTTON = "bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg shadow-sm"
    SUCCESS_BUTTON = "bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg shadow-sm"
    DANGER_BUTTON = "bg-rose-500 hover:bg-rose-600 text-white px-4 py-2 rounded-lg shadow-sm"
    WARNING_BUTTON = "bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg shadow-sm"

    # Buttons - States
    DISABLED_BUTTON = "bg-gray-100 text-gray-400 cursor-not-allowed px-4 py-2 rounded"
    DISABLED_BUTTON_SM = "bg-gray-100 text-gray-400 cursor-not-allowed px-2 py-1 text-xs rounded"

    # Cards - Softer shadows and warmer backgrounds
    CARD_BASE = "bg-white border border-stone-200 rounded-xl shadow-sm"
    CARD_ELEVATED = "bg-white border border-stone-200 rounded-xl shadow-lg"
    CARD_CONTENT = "bg-stone-50 border border-stone-200 rounded-lg p-4"
    CARD_DIALOG = "bg-white border border-stone-300 rounded-xl shadow-2xl"

    # Headers & Gradients - Modern gradients with warmer tones
    HEADER_GRADIENT = "font-bold text-white bg-gradient-to-r from-indigo-500 to-slate-600 rounded-t-xl px-4 py-3 shadow-md"
    SSH_HEADER_GRADIENT = "font-bold text-white bg-gradient-to-r from-emerald-500 to-slate-600 rounded-t-xl px-4 py-3 shadow-md"

    # Expansion Panels
    EXPANSION_COLORS = {
        "blue": "bg-blue-50 border border-blue-200",
        "green": "bg-green-50 border border-green-200",
        "orange": "bg-orange-50 border border-orange-200",
        "red": "bg-red-50 border border-red-200",
        "purple": "bg-purple-50 border border-purple-200",
        "yellow": "bg-yellow-50 border border-yellow-200",
        "teal": "bg-teal-50 border border-teal-200",
        "cyan": "bg-cyan-50 border border-cyan-200",
        "lime": "bg-lime-50 border border-lime-200",
        "pink": "bg-pink-50 border border-pink-200",
        "indigo": "bg-indigo-50 border border-indigo-200",
        "amber": "bg-amber-50 border border-amber-200",
    }

    # Chat Interface
    CHAT_USER_MESSAGE = "bg-blue-500 text-white p-3 rounded-lg max-w-xs"
    CHAT_AI_MESSAGE = "bg-white border p-3 rounded-lg max-w-xs"
    CHAT_CONTAINER = "border border-gray-300 rounded p-4 bg-gray-50"

    # Tables
    TABLE_BASE = "w-full bg-white border border-gray-200"
    TABLE_HEADER = "bg-gray-100 text-gray-800 font-semibold"
    TABLE_ROW_EVEN = "bg-white"
    TABLE_ROW_ODD = "bg-gray-50"
    TABLE_ROW_HOVER = "hover:bg-gray-100"

    # Icons & Status
    ICON_PRIMARY = "text-blue-600"
    ICON_SUCCESS = "text-green-600"
    ICON_DANGER = "text-red-600"
    ICON_WARNING = "text-yellow-600"
    ICON_MUTED = "text-gray-400"

    # Layout
    CONTAINER_MAIN = "w-full h-screen p-4"
    CONTAINER_CONTENT = "w-full h-full p-6 shadow-lg bg-white border border-gray-200"
    ROW_ITEMS_CENTER = "w-full items-center gap-3"
    COLUMN_FULL = "w-full h-full"

    # Terminal/Output
    TERMINAL_BG = "bg-gray-900 border border-gray-700"
    TERMINAL_TEXT = "text-green-400 font-mono bg-black"
    OUTPUT_AREA = "w-full h-64 bg-black text-green-400 font-mono text-sm border border-gray-600"


@dataclass(frozen=True)
class DarkTheme:
    """Dark theme UI styling configuration - Modern and eye-friendly."""

    # Base Colors - Warmer dark tones, less harsh
    PRIMARY_BG = "bg-slate-900"
    SECONDARY_BG = "bg-slate-800"
    TERTIARY_BG = "bg-slate-700"
    BORDER_COLOR = "border-slate-600"
    TEXT_PRIMARY = "text-slate-100"
    TEXT_SECONDARY = "text-slate-300"
    TEXT_MUTED = "text-slate-400"

    # Buttons - Standard - Softer dark tones
    GRAY_BUTTON = "bg-slate-600 hover:bg-slate-500 text-slate-100 px-4 py-2 rounded-lg"
    BLUE_BUTTON = "bg-sky-600 hover:bg-sky-500 text-sky-100 px-4 py-2 rounded-lg"
    RED_BUTTON = "bg-rose-600 hover:bg-rose-500 text-rose-100 px-4 py-2 rounded-lg"
    GREEN_BUTTON = "bg-emerald-600 hover:bg-emerald-500 text-emerald-100 px-4 py-2 rounded-lg"
    ORANGE_BUTTON = "bg-amber-600 hover:bg-amber-500 text-amber-100 px-4 py-2 rounded-lg"
    PURPLE_BUTTON = "bg-violet-600 hover:bg-violet-500 text-violet-100 px-4 py-2 rounded-lg"
    TEAL_BUTTON = "bg-teal-600 hover:bg-teal-500 text-teal-100 px-4 py-2 rounded-lg"

    # Buttons - Small
    GRAY_BUTTON_SM = "bg-slate-600 hover:bg-slate-500 text-slate-100 px-2 py-1 text-xs rounded-lg"
    BLUE_BUTTON_SM = "bg-sky-600 hover:bg-sky-500 text-sky-100 px-2 py-1 text-xs rounded-lg"
    RED_BUTTON_SM = "bg-rose-600 hover:bg-rose-500 text-rose-100 px-2 py-1 text-xs rounded-lg"
    GREEN_BUTTON_SM = (
        "bg-emerald-600 hover:bg-emerald-500 text-emerald-100 px-2 py-1 text-xs rounded-lg"
    )

    # Buttons - Special - Modern accent colors
    PRIMARY_BUTTON = "bg-indigo-500 hover:bg-indigo-400 text-white px-4 py-2 rounded-lg shadow-sm"
    SUCCESS_BUTTON = "bg-emerald-500 hover:bg-emerald-400 text-white px-4 py-2 rounded-lg shadow-sm"
    DANGER_BUTTON = "bg-rose-500 hover:bg-rose-400 text-white px-4 py-2 rounded-lg shadow-sm"
    WARNING_BUTTON = "bg-amber-500 hover:bg-amber-400 text-slate-900 px-4 py-2 rounded-lg shadow-sm"

    # Buttons - States
    DISABLED_BUTTON = "bg-gray-700 text-gray-500 cursor-not-allowed px-4 py-2 rounded"
    DISABLED_BUTTON_SM = "bg-gray-700 text-gray-500 cursor-not-allowed px-2 py-1 text-xs rounded"

    # Cards - Warmer dark backgrounds
    CARD_BASE = "bg-slate-800 border border-slate-600 rounded-xl shadow-sm"
    CARD_ELEVATED = "bg-slate-800 border border-slate-600 rounded-xl shadow-lg"
    CARD_CONTENT = "bg-slate-700 border border-slate-600 rounded-lg p-4"
    CARD_DIALOG = "bg-slate-800 border border-slate-600 rounded-xl shadow-2xl"

    # Headers & Gradients - Modern gradients with warmer dark tones
    HEADER_GRADIENT = "font-bold text-white bg-gradient-to-r from-indigo-600 to-slate-700 rounded-t-xl px-4 py-3 shadow-md"
    SSH_HEADER_GRADIENT = "font-bold text-white bg-gradient-to-r from-emerald-600 to-slate-700 rounded-t-xl px-4 py-3 shadow-md"

    # Expansion Panels
    EXPANSION_COLORS: ClassVar[dict[str, str]] = {
        "blue": "bg-blue-900 border border-blue-700",
        "green": "bg-green-900 border border-green-700",
        "orange": "bg-orange-900 border border-orange-700",
        "red": "bg-red-900 border border-red-700",
        "purple": "bg-purple-900 border border-purple-700",
        "yellow": "bg-yellow-900 border border-yellow-700",
        "teal": "bg-teal-900 border border-teal-700",
        "cyan": "bg-cyan-900 border border-cyan-700",
        "lime": "bg-lime-900 border border-lime-700",
        "pink": "bg-pink-900 border border-pink-700",
        "indigo": "bg-indigo-900 border border-indigo-700",
        "amber": "bg-amber-900 border border-amber-700",
    }

    # Chat Interface
    CHAT_USER_MESSAGE = "bg-blue-600 text-white p-3 rounded-lg max-w-xs"
    CHAT_AI_MESSAGE = "bg-gray-700 border border-gray-600 text-gray-100 p-3 rounded-lg max-w-xs"
    CHAT_CONTAINER = "border border-gray-600 rounded p-4 bg-gray-800"

    # Tables
    TABLE_BASE = "w-full bg-gray-800 border border-gray-600"
    TABLE_HEADER = "bg-gray-700 text-gray-100 font-semibold"
    TABLE_ROW_EVEN = "bg-gray-800"
    TABLE_ROW_ODD = "bg-gray-750"
    TABLE_ROW_HOVER = "hover:bg-gray-700"

    # Icons & Status
    ICON_PRIMARY = "text-blue-400"
    ICON_SUCCESS = "text-green-400"
    ICON_DANGER = "text-red-400"
    ICON_WARNING = "text-yellow-400"
    ICON_MUTED = "text-gray-500"

    # Layout
    CONTAINER_MAIN = "w-full h-screen p-4"
    CONTAINER_CONTENT = "w-full h-full p-6 shadow-lg bg-gray-800 border border-gray-600"
    ROW_ITEMS_CENTER = "w-full items-center gap-3"
    COLUMN_FULL = "w-full h-full"

    # Terminal/Output
    TERMINAL_BG = "bg-black border border-gray-600"
    TERMINAL_TEXT = "text-green-400 font-mono bg-black"
    OUTPUT_AREA = "w-full h-64 bg-black text-green-400 font-mono text-sm border border-gray-500"


# Current theme (can be switched at runtime)
CURRENT_THEME = LightTheme()

COLORS = {
    "primary": "#475569",  # Warmer slate-600
    "secondary": "#64748b",  # Softer slate-500
    "accent": "#6366f1",  # Modern indigo-500
    "dark": "#0f172a",  # Deep slate-900
    "positive": "#10b981",  # Emerald-500 (unchanged - already good)
    "negative": "#f43f5e",  # Rose-500 (softer red)
    "info": "#0ea5e9",  # Sky-500 (warmer blue)
    "warning": "#f59e0b",  # Amber-500 (unchanged - already good)
}


def apply_global_theme():
    ui.colors(**COLORS)
