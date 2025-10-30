from enum import Enum, auto


class ServiceStatus(Enum):
    """System service status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    UNKNOWN = "unknown"


class PackageStatus(Enum):
    """Package installation status."""

    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    UNKNOWN = "unknown"


class PackageManagerType(Enum):
    """Package manager types."""

    APT = "apt"
    YUM = "yum"
    UNKNOWN = "unknown"


class CommandInputType(Enum):
    """Command input types."""

    INTERFACE = "Network interface"
    PCI_ID = "PCI id"
    MST_PCICONF = "_pciconfig"
    NOTHING = ""


class ToolType(Enum):
    """Tool types."""

    DMESG = auto()
    ETHTOOL = auto()
    MLX = auto()
    MST = auto()
    RDMA = auto()
    SYSTEM = auto()
