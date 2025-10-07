from nicegui import ui


class Base:
    name: str
    label: str

    def __init__(self, name: str, label: str) -> None:
        self.name = name
        self.label = label

    def build(self) -> None:
        pass


class BaseTab(Base):
    _tab: ui.tab = None

    _icon_name: str

    icon: ui.icon = None

    def __init__(self, name: str, label: str, icon_name: str) -> None:
        super().__init__(name, label)
        self._icon_name = icon_name

    def build(self) -> None:
        with ui.column().classes("items-center gap-1"):
            with ui.tab(self.name):
                self.icon = ui.icon(self._icon_name).props("size=24px")

    def clear(self) -> None:
        if self.icon:
            self.icon.clear()

    def reset(self) -> None:
        self.clear()
        self.build()


class BasePanel(Base):
    _title: ui.label = None

    _CONTENT_OF_STRING = "Content of: "

    def __init__(self, name: str, label: str) -> None:
        super().__init__(name, label)

    def build(self) -> None:
        if self._title:
            self._title.clear()
        self._title = ui.label(self._CONTENT_OF_STRING + self.label)

    def save(self) -> None:
        from src.utils.configure import Configure

        Configure().save(self._app_config)
