from enum import Enum


class LogName(Enum):
    """Log names."""

    MAIN = "main"
    MEMORY = "memory"

    SUT_SYSTEM_INFO = "sut_system_info"
    SUT_MXLINK = "sut_mxlink"
    SUT_MXLINK_AMBER = "sut_mxlink_amber"
    SUT_MTEMP = "sut_mtemp"
    SUT_ETHTOOL = "sut_ethtool"
    SUT_LINK_FLAP = "sut_link_flap"

    SLX_EYE = "slx_eye"
    SLX_DSC = "slx_dsc"
