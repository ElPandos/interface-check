import json

from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.enums.settings import Options, Types
from src.utils.configure import Configure
from src.utils.process_manager import ProcessManager


class SettingsHandler:
    """Handles rendering and synchronization of application settings."""

    def __init__(self) -> None:
        self.__dark_mode = ui.dark_mode()  # Keep a reference!

    def _get_value(self, name: str, app_config: AppConfig) -> tuple[str, int, int]:
        for s in app_config.system.settings:
            if s.name == name:
                return s.value, s.min, s.max
        return None, None, None

    def _save(self) -> None:
        Configure().save(self._app_config)

    def build(self, app_config: AppConfig) -> None:
        """Render settings UI with live bindings to internal values."""
        self._app_config = app_config
        for opt in self._app_config.system.settings:
            match opt.type:
                case Options.SWITCH.value | Options.SWITCH:
                    with (
                        ui.card().classes("w-full items-left"),
                        ui.row().classes("w-full items-center"),
                    ):
                        ui.label(opt.name)
                        value, value_min, value_max = self._get_value(opt.name, app_config)
                        switch = None
                        if opt.name == Types.DEBUG.name:
                            switch = ui.switch(value=value).classes("ml-auto")

                        if opt.name == Types.DARK.name:
                            switch = ui.switch(value=value, on_change=lambda: self.__dark_mode.toggle()).classes(
                                "ml-auto"
                            )

                        switch.bind_value(opt, "value")

                case Options.SLIDER.value | Options.SLIDER:
                    with ui.card().classes("w-full items-left"), ui.column().classes("w-full items-left"):
                        ui.label(opt.name)
                        value, value_min, value_max = self._get_value(opt.name, app_config)
                        with ui.row().classes("w-full items-center flex-nowrap"):
                            # Slider
                            slider = ui.slider(min=value_min, max=value_max, value=value).classes("flex-grow")
                            slider.bind_value(opt, "value")

                            # Label
                            slider_value_label = ui.label(str(opt.value)).classes("w-3 text-right pr-10")
                            slider_value_label.bind_text_from(slider, "value")

                case Options.TEXT.value | Options.TEXT:
                    with ui.card().classes("w-full items-left"), ui.column().classes("w-full items-left"):
                        value, value_min, value_max = self._get_value(opt.name, app_config)
                        textarea = ui.textarea(
                            label=opt.name,
                            placeholder="Start typing...",
                            value=value,
                        ).classes("w-full")
                        textarea.bind_value(opt, "value")

                case Options.BUTTON.value | Options.BUTTON:
                    with (
                        ui.card().classes("w-full"),
                        ui.column().classes("w-full"),
                        ui.button(opt.name, on_click=self._save).classes(
                            "w-full items-left bg-gray-300 hover:bg-gray-400 text-gray-800"
                        ),
                    ):
                        pass

                case Options.INFO.value | Options.INFO:
                    ui.space()
                    with (
                        ui.card().classes("w-full"),
                        ui.column().classes("w-full"),
                        ui.dropdown_button("Libraries", icon="logo_dev", auto_close=True).classes("w-full items-left"),
                    ):
                        pm = ProcessManager()
                        proc = pm.run("uv run pip-licenses --format=json")
                        stdout, _ = pm.get_output(proc)
                        if stdout:
                            licenses = json.loads(stdout)
                            for pkg in licenses:
                                name = pkg.get("Name")
                                version = pkg.get("Version")
                                pkg_license = pkg.get("License")
                                ui.item(
                                    f"{name} == {version} [{pkg_license}]",
                                    on_click=lambda n=name: ui.navigate.to(
                                        f"https://pypi.org/project/{n}", new_tab=True
                                    ),
                                )
                        else:
                            ui.item(
                                "pip-licenses not installed in .venv",
                                on_click=lambda: ui.navigate.to("https://pypi.org/project/pip-licenses", new_tab=True),
                            )


# Create the global singleton instance
settings = SettingsHandler()
