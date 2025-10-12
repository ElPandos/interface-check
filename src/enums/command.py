from enum import Enum, auto


class CommandType(Enum):
    MODIFY = auto()
    SYSTEM = auto()
    PYTHON = auto()
    COMMON = auto()
    ETHTOOL = auto()
    MLXLINK = auto()
    MLXCONFIG = auto()
    MST = auto()
    GIT = auto()
