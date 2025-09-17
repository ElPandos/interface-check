import json
from typing import Any

from nicegui import ui

from src.process_manager import ProcessManager
from src.ui.enums.settings import Options, Types


class SettingsHandler:
    """Handles rendering and synchronization of application settings."""

    def __init__(self) -> None:
        # Define available options
        self.__options: list[dict[str, Any]] = [
            {"name": Types.DARK.name, "type": Options.SWITCH, "value": False},
            {"name": Types.DEBUG.name, "type": Options.SWITCH, "value": False},
            {"name": Types.UPDATE.name, "type": Options.SLIDER, "min": 5, "max": 100, "value": 10},
            {"name": Types.MESSAGE.name, "type": Options.TEXT, "value": ""},
            {"name": Types.LIBS.name, "type": Options.INFO, "value": ""},
        ]
        self.__dark_mode = ui.dark_mode()  # Keep a reference!

    def build(self) -> None:
        """Render settings UI with live bindings to internal values."""
        for opt in self.__options:
            match opt["type"]:
                case Options.SWITCH:
                    with ui.card().classes("w-full items-left"):
                        with ui.row().classes("w-full items-center"):
                            ui.label(opt["name"])
                            switch = None
                            if opt["name"] == Types.DEBUG.name:
                                switch = ui.switch(value=opt["value"]).classes("ml-auto")

                            if opt["name"] == Types.DARK.name:
                                switch = ui.switch(
                                    value=opt["value"], on_change=lambda: self.__dark_mode.toggle()
                                ).classes("ml-auto")

                            switch.bind_value(opt, "value")

                case Options.SLIDER:
                    with ui.card().classes("w-full items-left"):
                        with ui.column().classes("w-full items-left"):
                            ui.label(opt["name"])
                            with ui.row().classes("w-full items-center flex-nowrap"):  # right-aligned group
                                # Slider
                                slider = ui.slider(min=opt["min"], max=opt["max"], value=opt["value"]).classes(
                                    "flex-grow"
                                )
                                slider.bind_value(opt, "value")

                                # Label
                                slider_value_label = ui.label(str(opt["value"])).classes("w-3 text-right pr-10")
                                slider_value_label.bind_text_from(slider, "value")

                case Options.TEXT:
                    with ui.card().classes("w-full items-left"):
                        with ui.column().classes("w-full items-left"):
                            textarea = ui.textarea(
                                label=opt["name"],
                                placeholder="Start typing...",
                                value=opt["value"],
                            ).classes("w-full")
                            textarea.bind_value(opt, "value")

                case Options.INFO:
                    with ui.card().classes("w-full"):
                        with ui.column().classes("w-full"):
                            with ui.dropdown_button("Libraries", icon="logo_dev", auto_close=True):
                                pm = ProcessManager()
                                proc = pm.run("uv run pip-licenses --format=json")
                                stdout, stderr = pm.get_output(proc)
                                if stdout:
                                    licenses = json.loads(stdout)
                                    for pkg in licenses:
                                        name = pkg.get("Name")
                                        version = pkg.get("Version")
                                        license = pkg.get("License")
                                        ui.item(
                                            f"{name}=={version} uses license: {license}",
                                            on_click=lambda: ui.notify(f"{name}"),
                                        )
                                else:
                                    ui.item(
                                        "pip-licenses not installed in venv",
                                    )

    def get_settings(self) -> dict[str, Any]:
        """Return current settings as a dictionary."""
        return {opt["name"]: opt["value"] for opt in self.__options}


# Create the global singleton instance
settings = SettingsHandler()
