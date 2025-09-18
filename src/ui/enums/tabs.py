from enum import Enum

from src.ui.tabs.ai_chat import AiChat
from src.ui.tabs.base_tab import BaseTab
from src.ui.tabs.ethtool import Ethtool
from src.ui.tabs.host import Host
from src.ui.tabs.info import Info
from src.ui.tabs.log import Log
from src.ui.tabs.mlxconfig import Mlxconfig
from src.ui.tabs.mlxlink import Mlxlink


class Tabs(Enum):
    HOST = ("Host", "home", Host)
    MLXLINK = ("mlxlink", "home_repair_service", Mlxlink)
    MLXCONFIG = ("mlxconfig", "home_repair_service", Mlxconfig)
    ETHTOOL = ("ethtool", "home_repair_service", Ethtool)
    INFO = ("Info", "info", Info)
    LOG = ("Log", "logo_dev", Log)
    AI_CHAT = ("AI chat", "tips_and_updates", AiChat)

    def __init__(self, value: str, icon: str, tab_cls: type[BaseTab]) -> None:
        self._value = value
        self._icon = icon
        self._tab_cls = tab_cls

    @property
    def name(self) -> str:
        """Return the enum value name."""
        return self._value

    @property
    def icon(self) -> str:
        """Return the associated icon for this tab."""
        return self._icon

    def create_panel(self) -> BaseTab:
        """Instantiate and return the panel for this tab."""
        return self._tab_cls()
