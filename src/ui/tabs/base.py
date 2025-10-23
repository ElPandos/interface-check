from abc import ABC, abstractmethod

from nicegui import ui


class Base(ABC):
    def __init__(self, name: str, label: str, icon_name: str) -> None:
        self._name = name
        self._label = label
        self._icon_name = icon_name

    @abstractmethod
    def build(self) -> None:
        pass

    @property
    def name(self) -> str:
        return self._name

    @property
    def label(self) -> str:
        return self._label

    @property
    def icon_name(self) -> str:
        return self._ICON_NAME


class BaseTab(Base):
    def __init__(self, name: str, label: str, icon_name: str) -> None:
        Base.__init__(self, name, label, icon_name)

        self._tab: ui.tab = None
        self._icon: ui.icon = None

    def build(self) -> None:
        with ui.column().classes("items-center gap-1"), ui.tab(self.name):
            if self._icon:
                self._icon.clear()
            self._icon = ui.icon(self.icon_name).props("size=24px")

    @property
    def icon(self) -> ui.icon:
        return self._icon


class BasePanel(Base):
    _CONTENT_OF_STRING = "Content of: "

    def __init__(self, name: str, label: str, icon_name: str) -> None:
        Base.__init__(self, name, label, icon_name)

        self._title: ui.label = None

    def build(self) -> None:
        if self._title:
            self._title.clear()
        with ui.row().classes("items-center gap-2"):
            if self.icon_name:
                ui.icon(self.ICON_NAME).props("size=24px")
            self._title = ui.label(self._CONTENT_OF_STRING + self.label)

    @property
    def title(self) -> str:
        return self._title
