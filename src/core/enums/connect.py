"""Connection type enumerations."""

from enum import Enum


class ConnectType(str, Enum):
    """Connection type for command execution."""

    LOCAL = "local"
    REMOTE = "remote"


class HostType(str, Enum):
    """Host type for SSH connection creation."""

    SLX = "slx"
    SUT = "sut"


class ShowPartType(str, Enum):
    """Parts to skip in system scanning.

    If show_parts is empty, all components run.
    Add flags to skip specific components.
    """

    NO_SYS_INFO = "no_sys_info"
    NO_MLXLINK = "no_mlxlink"
    NO_MTEMP = "no_mtemp"
    NO_DMESG = "no_dmesg"
    NO_EYE_SCAN = "no_eye_scan"
