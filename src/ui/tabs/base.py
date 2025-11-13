from abc import ABC, abstractmethod

from nicegui import ui


class Base(ABC):
    """Base class for tabs and panels.

    Args:
        name: Component name
        label: Display label
        icon_name: Icon identifier
    """

    def __init__(self, name: str, label: str, icon_name: str) -> None:
        """Initialize base component.

        Args:
            name: Component name
            label: Display label
            icon_name: Icon identifier
        """
        self._name = name
        self._label = label
        self._icon_name = icon_name

    @abstractmethod
    def build(self) -> None:
        """Build the component."""
        pass

    @property
    def name(self) -> str:
        """Get component name.

        Returns:
            Component name
        """
        return self._name

    @property
    def label(self) -> str:
        """Get display label.

        Returns:
            Display label
        """
        return self._label

    @property
    def icon_name(self) -> str:
        """Get icon name.

        Returns:
            Icon identifier
        """
        return self._ICON_NAME


class BaseTab(Base):
    """Base class for tab components."""

    def __init__(self, name: str, label: str, icon_name: str) -> None:
        """Initialize tab.

        Args:
            name: Tab name
            label: Display label
            icon_name: Icon identifier
        """
        Base.__init__(self, name, label, icon_name)

        self._tab: ui.tab = None
        self._icon: ui.icon = None

    def build(self) -> None:
        """Build tab component."""
        with ui.column().classes("items-center gap-1"), ui.tab(self.name):
            if self._icon:
                self._icon.clear()
            self._icon = ui.icon(self.icon_name).props("size=24px")

    @property
    def icon(self) -> ui.icon:
        """Get tab icon.

        Returns:
            Icon component
        """
        return self._icon


class BasePanel(Base):
    """Base class for panel components."""

    _CONTENT_OF_STRING = "Content of: "

    def __init__(self, name: str, label: str, icon_name: str) -> None:
        """Initialize panel.

        Args:
            name: Panel name
            label: Display label
            icon_name: Icon identifier
        """
        Base.__init__(self, name, label, icon_name)

        self._title: ui.label = None

    def build(self) -> None:
        """Build panel component."""
        if self._title:
            self._title.clear()
        with ui.row().classes("items-center gap-2"):
            if self.icon_name:
                ui.icon(self.ICON_NAME).props("size=24px")
            self._title = ui.label(self._CONTENT_OF_STRING + self.label)

    @property
    def title(self) -> str:
        """Get panel title.

        Returns:
            Title label
        """
        return self._title
