from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.enums.settings import Options, Types
from src.utils.commands import Python
from src.utils.configure import Configure
from src.utils.json import Json
from src.utils.terminal import Cli


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
                    self._build_switch(opt, app_config)
                case Options.SLIDER.value | Options.SLIDER:
                    self._build_slider(opt, app_config)
                case Options.TEXT.value | Options.TEXT:
                    self._build_text(opt, app_config)
                case Options.BUTTON.value | Options.BUTTON:
                    self._build_button(opt)
                case Options.INFO.value | Options.INFO:
                    self._build_info()

    def _build_switch(self, opt, app_config: AppConfig) -> None:
        with ui.card().classes("w-full items-left"), ui.row().classes("w-full items-center"):
            ui.label(opt.name)
            value, _, _ = self._get_value(opt.name, app_config)
            switch = None
            if opt.name == Types.DEBUG.name:
                switch = ui.switch(value=value).classes("ml-auto")
            elif opt.name == Types.DARK.name:
                switch = ui.switch(value=value, on_change=lambda: self.__dark_mode.toggle()).classes("ml-auto")
            if switch:
                switch.bind_value(opt, "value")

    def _build_slider(self, opt, app_config: AppConfig) -> None:
        with ui.card().classes("w-full items-left"), ui.column().classes("w-full items-left"):
            with ui.row().classes("w-full items-center gap-2"):
                self._add_slider_icon(opt.name)
                ui.label(opt.name)
            value, value_min, value_max = self._get_value(opt.name, app_config)
            with ui.row().classes("w-full items-center flex-nowrap"):
                slider = ui.slider(min=value_min, max=value_max, value=value).classes("flex-grow")
                slider.bind_value(opt, "value")
                slider_value_label = ui.label(str(opt.value)).classes("w-3 text-right pr-10")
                slider_value_label.bind_text_from(slider, "value")

    def _add_slider_icon(self, name: str) -> None:
        if name == Types.REFRESH.name:
            ui.icon("dashboard", size="lg").classes("text-blue-600").tooltip(
                "Used in Dashboard tab for auto-refresh interval"
            )
        elif name == Types.COMMAND.name:
            ui.icon("terminal", size="lg").classes("text-yellow-600").tooltip("Used for command polling interval")
        elif name == Types.GRAPH.name:
            ui.icon("show_chart", size="lg").classes("text-green-600").tooltip("Used for graph update interval")

    def _build_text(self, opt, app_config: AppConfig) -> None:
        with ui.card().classes("w-full items-left"), ui.column().classes("w-full items-left"):
            value, _, _ = self._get_value(opt.name, app_config)
            textarea = ui.textarea(label=opt.name, placeholder="Start typing...", value=value).classes("w-full")
            textarea.bind_value(opt, "value")

    def _build_button(self, opt) -> None:
        with ui.card().classes("w-full"), ui.column().classes("w-full"):
            ui.button(opt.name, on_click=self._save).classes(
                "w-full items-left bg-gray-300 hover:bg-gray-400 text-gray-800"
            )

    def _build_info(self) -> None:
        ui.space()
        with (
            ui.card().classes("w-full"),
            ui.column().classes("w-full"),
            ui.dropdown_button("Libraries", icon="logo_dev", auto_close=True).classes("w-full items-left"),
        ):
            proc = Cli().run(Python().licenses().syntax)
            stdout, _, _ = Cli().get_output(proc)
            if stdout:
                licenses = Json.parse_string(stdout)
                for pkg in licenses:
                    name = pkg.get("Name")
                    version = pkg.get("Version")
                    pkg_license = pkg.get("License")
                    ui.item(
                        f"{name} == {version} [{pkg_license}]",
                        on_click=lambda n=name: ui.navigate.to(f"https://pypi.org/project/{n}", new_tab=True),
                    )
            else:
                ui.item(
                    "pip-licenses not installed in .venv",
                    on_click=lambda: ui.navigate.to("https://pypi.org/project/pip-licenses", new_tab=True),
                )


# Create the global singleton instance
settings = SettingsHandler()
