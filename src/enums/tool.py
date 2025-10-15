"""Tool enumerations for the toolbox tab."""

from enum import Enum


class Software(Enum):
    """Network diagnostic and configuration SW tools."""

    MLXCONFIG = "mlxconfig"
    MLXLINK = "mlxlink"
    IPMITOOL = "ipmitool"
    ETHTOOL = "ethtool"
    MFT = "mft"
    DMESG = "dmesg"
