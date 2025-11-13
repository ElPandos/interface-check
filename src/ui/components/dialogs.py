"""Reusable dialog components."""

import asyncio

from nicegui import ui


class DialogFactory:
    """Factory for creating common dialog types."""

    @staticmethod
    async def get_text_input(title: str, label: str, placeholder: str = "") -> str | None:
        """Show a dialog with text input and return user's input.

        Args:
            title: Dialog title
            label: Input label
            placeholder: Input placeholder text

        Returns:
            User input or None if cancelled
        """
        future = asyncio.get_event_loop().create_future()
        dialog = ui.dialog()

        with dialog, ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"):
            ui.label(title).classes("text-xl font-bold mb-6 text-center text-gray-800")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label(label).classes("font-semibold mb-3 text-gray-700")
                input_field = ui.input("Command", placeholder=placeholder).classes("w-full")
                input_field.props("outlined")

            with ui.row().classes("w-full mt-6"):
                ui.button(
                    icon="play_arrow",
                    text="Execute",
                    on_click=lambda: (dialog.close(), future.set_result(input_field.value)),
                ).classes("bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg")
                ui.space()
                ui.button(
                    icon="cancel",
                    text="Cancel",
                    on_click=lambda: (dialog.close(), future.set_result(None)),
                ).classes("bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg")

        dialog.open()
        return await future
