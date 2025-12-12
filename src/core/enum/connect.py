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


class IperfHostType(str, Enum):
    """Iperf host type for traffic testing."""

    SERVER = "server"
    CLIENT = "client"


class PortState(str, Enum):
    """Port/interface state for toggling."""

    ON = "true"
    OFF = "false"

    @property
    def display_name(self) -> str:
        """Get display name for logging.

        Returns:
            Display name (ON/OFF)
        """
        return self.name


class ShowPartType(str, Enum):
    """Parts to skip in system scanning.

    If show_parts is empty, all components run.
    Add flags to skip specific components.
    """

    NO_SYS_INFO = "no_sys_info"
    NO_MLXLINK = "no_mlxlink"
    NO_MLXLINK_AMBER = "no_mlxlink_amber"
    NO_MTEMP = "no_mtemp"
    NO_ETHTOOL = "no_ethtool"
    NO_DMESG = "no_dmesg"
    NO_TX_ERRORS = "no_tx_errors"
    NO_SLX_EYE = "no_slx_eye"
    NO_SLX_DSC = "no_slx_dsc"
    NO_FAN = "no_fan"
