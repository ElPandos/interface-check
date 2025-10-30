from nicegui import ui

from src.core.bak.terminal import Cli
from src.core.config import Configure
from src.core.json import Json
from src.models.config import Config
from src.platform.bak.commands import Python
from src.ui.enums.settings import Options, Types


class SettingsHandler:
    """Handles rendering and synchronization of application settings."""

    def __init__(self) -> None:
        self.__dark_mode = ui.dark_mode()  # Keep a reference!

    def _get_value(self, name: str) -> tuple[str, int, int]:
        for s in self._config.settings.options:
            if s.name == name:
                return s.value, s.min, s.max
        return None, None, None

    def _save(self) -> None:
        Configure().save(self._config)

    def build(self, config: Config) -> None:
        """Render settings UI with live bindings to internal values."""
        self._config = config
        for o in self._config.settings.options:
            match o.type:
                case Options.SWITCH.value:
                    self._build_switch(o)
                case Options.SLIDER.value:
                    self._build_slider(o)
                case Options.TEXT.value:
                    self._build_text(o)
                case Options.BUTTON.value:
                    self._build_button(o)
                case Options.INFO.value:
                    self._build_info()

    def _build_switch(self, opt) -> None:
        with ui.card().classes("w-full items-left"), ui.row().classes("w-full items-center"):
            ui.label(opt.name)
            value, _, _ = self._get_value(opt.name)
            if opt.name == Types.DEBUG.name:
                switch = ui.switch(value=value).classes("ml-auto")
            elif opt.name == Types.DARK.name:
                switch = ui.switch(value=value, on_change=self.__dark_mode.toggle).classes(
                    "ml-auto"
                )
            else:
                return
            switch.bind_value(opt, "value")

    def _build_slider(self, opt) -> None:
        with ui.card().classes("w-full items-left"), ui.column().classes("w-full items-left"):
            with ui.row().classes("w-full items-center gap-2"):
                self._add_slider_icon(opt.name)
                ui.label(opt.name)
            value, value_min, value_max = self._get_value(opt.name)
            with ui.row().classes("w-full items-center flex-nowrap"):
                slider = ui.slider(min=value_min, max=value_max, value=value).classes("flex-grow")
                slider.bind_value(opt, "value")
                slider_value_label = ui.label(str(opt.value)).classes("w-3 text-right pr-10")
                slider_value_label.bind_text_from(slider, "value")

    def _add_slider_icon(self, name: str) -> None:
        icons = {
            Types.REFRESH.name: (
                "dashboard",
                "text-blue-600",
                "Used in Dashboard tab for auto-refresh interval",
            ),
            Types.COMMAND.name: (
                "terminal",
                "text-yellow-600",
                "Used for command polling interval",
            ),
            Types.GRAPH.name: ("show_chart", "text-green-600", "Used for graph update interval"),
        }
        if name in icons:
            icon, color, tooltip = icons[name]
            ui.icon(icon, size="lg").classes(color).tooltip(tooltip)

    def _build_text(self, opt) -> None:
        with ui.card().classes("w-full items-left"), ui.column().classes("w-full items-left"):
            value, _, _ = self._get_value(opt.name)
            textarea = ui.textarea(
                label=opt.name, placeholder="Start typing...", value=value
            ).classes("w-full")
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
            ui.dropdown_button("Libraries", icon="logo_dev", auto_close=True).classes(
                "w-full items-left"
            ),
        ):
            proc = Cli().run(Python().licenses().syntax)
            result = Cli().get_output(proc)
            if result.stdout:
                licenses = Json.parse_string(result.stdout)
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
                    on_click=lambda: ui.navigate.to(
                        "https://pypi.org/project/pip-licenses", new_tab=True
                    ),
                )


# Create the global singleton instance
settings = SettingsHandler()
