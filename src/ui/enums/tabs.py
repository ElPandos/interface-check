from enum import Enum


class Tabs(Enum):
    HOST = "Host"
    MLXLINK = "Tool [mlxlink]"
    MLXCONFIG = "Tool [mlxconfig]"
    ETHTOOL = "Tool [ethtool]"
    OTHER = "Other"
    LOG = "Log"

    @property
    def name(self) -> str:
        return self.value
