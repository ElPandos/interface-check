"""Tool enumerations for the toolbox tab."""

from enum import Enum


class NetworkTool(Enum):
    """Network diagnostic and configuration tools."""

    MLXCONFIG = "mlxconfig"
    MLXLINK = "mlxlink"
    IPMITOOL = "ipmitool"
    ETHTOOL = "ethtool"
    MFT = "mft"
    DMESG = "dmesg"
